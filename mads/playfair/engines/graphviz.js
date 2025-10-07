const { spawn } = require('child_process');
const { exec } = require('child_process');
const { promisify } = require('util');
const BaseEngine = require('./base');
const logger = require('../utils/logger');
const svgProcessor = require('../themes/svg-processor');
const themes = require('../themes/graphviz-themes.json');

const execAsync = promisify(exec);
const RENDER_TIMEOUT = parseInt(process.env.RENDER_TIMEOUT_MS, 10) || 60000;

class GraphvizEngine extends BaseEngine {
    constructor() {
        super('graphviz');
    }

    async render(content, options) {
        const theme = options.theme || 'modern';
        const themedDot = this._applyTheme(content, theme);

        return new Promise((resolve, reject) => {
            const proc = spawn('dot', ['-Tsvg', '-Kdot'], {
                timeout: RENDER_TIMEOUT
            });

            let stdout = '';
            let stderr = '';

            proc.stdout.on('data', (data) => {
                stdout += data.toString();
            });

            proc.stderr.on('data', (data) => {
                stderr += data.toString();
            });

            proc.on('error', (error) => {
                logger.error({ engine: this.name, error: error.message }, 'Graphviz spawn failed');
                reject(new Error(`Failed to spawn dot: ${error.message}`));
            });

            proc.on('close', async (code) => {
                if (code !== 0) {
                    logger.error({ engine: this.name, code, stderr }, 'Graphviz rendering failed');
                    reject(this._parseError(stderr));
                } else {
                    try {
                        const processedSvg = await svgProcessor.process(stdout, 'graphviz', theme);
                        resolve(Buffer.from(processedSvg));
                    } catch (error) {
                        reject(error);
                    }
                }
            });

            // Write input to stdin and close
            proc.stdin.write(themedDot);
            proc.stdin.end();
        });
    }

    async validate(content) {
        return new Promise((resolve) => {
            // Validate by attempting to render to /dev/null
            const proc = spawn('dot', ['-Tsvg', '-o/dev/null'], { timeout: 10000 });

            let stderr = '';

            proc.stderr.on('data', (data) => {
                stderr += data.toString();
            });

            proc.on('close', (code) => {
                if (code === 0) {
                    resolve({ valid: true, errors: [] });
                } else {
                    const parsedError = this._parseError(stderr);
                    resolve({ valid: false, errors: [{ line: parsedError.line || null, message: parsedError.message }] });
                }
            });

            proc.stdin.write(content);
            proc.stdin.end();
        });
    }

    _applyTheme(dotContent, themeName) {
        const theme = themes[themeName];
        if (!theme) {
            logger.warn({ themeName }, 'Unknown theme requested, using default.');
            return dotContent;
        }

        // Create attribute strings from the theme JSON
        const graphAttrs = Object.entries(theme.graph).map(([k, v]) => `${k}="${v}"`).join(' ');
        const nodeAttrs = Object.entries(theme.node).map(([k, v]) => `${k}="${v}"`).join(' ');
        const edgeAttrs = Object.entries(theme.edge).map(([k, v]) => `${k}="${v}"`).join(' ');

        const themeInjection = `
  // Theme: ${themeName}
  graph [${graphAttrs}];
  node [${nodeAttrs}];
  edge [${edgeAttrs}];
`;
        // Inject theme attributes after the opening brace of the digraph/graph
        return dotContent.replace(/digraph\s*.*?\{/i, `$&${themeInjection}`);
    }

    _parseError(stderr) {
        const error = new Error();
        error.engine = this.name;

        const lineMatch = stderr.match(/error in line (\d+)/i);
        if (lineMatch) {
            error.code = 'SYNTAX_ERROR';
            error.line = parseInt(lineMatch[1], 10);
            error.message = stderr.split('\n')[0] || 'Graphviz syntax error.';
            error.suggestion = `Check the DOT syntax near line ${error.line}.`;
        } else if (stderr.includes('timeout')) {
            error.code = 'TIMEOUT';
            error.message = 'Graphviz rendering timed out.';
            error.suggestion = 'The diagram is too complex. Try simplifying it.';
        } else {
            error.code = 'ENGINE_CRASH';
            error.message = 'Graphviz engine failed unexpectedly.';
            error.suggestion = 'Please check the diagram content for errors.';
        }
        return error;
    }
}

module.exports = GraphvizEngine;