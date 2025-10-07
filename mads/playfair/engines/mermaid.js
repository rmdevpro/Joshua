const { execFile } = require('child_process');
const { promisify } = require('util');
const crypto = require('crypto');
const fs = require('fs/promises');
const path = require('path');
const os = require('os');
const BaseEngine = require('./base');
const logger = require('../utils/logger');
const svgProcessor = require('../themes/svg-processor');
const themes = require('../themes/mermaid-themes.json');

const execFileAsync = promisify(execFile);
const RENDER_TIMEOUT = parseInt(process.env.RENDER_TIMEOUT_MS, 10) || 60000;

class MermaidEngine extends BaseEngine {
    constructor() {
        super('mermaid');
    }

    async render(content, options) {
        const theme = options.theme || 'modern';
        const mermaidTheme = themes[theme]?.mermaidTheme || 'default';
        
        let tempInputDir, tempOutputDir, tempConfigPath;
        try {
            // Create temporary files for mmdc CLI with crypto-random names to prevent symlink attacks
            const tempDir = await fs.mkdtemp(path.join(os.tmpdir(), 'playfair-mermaid-'));
            const randomName = crypto.randomBytes(8).toString('hex');
            tempInputDir = path.join(tempDir, `${randomName}.mmd`);
            tempOutputDir = path.join(tempDir, `${randomName}.svg`);
            tempConfigPath = path.join(tempDir, `${randomName}-config.json`);

            await fs.writeFile(tempInputDir, content);

            // Create Mermaid theme config file
            const mermaidConfig = { "theme": mermaidTheme };
            await fs.writeFile(tempConfigPath, JSON.stringify(mermaidConfig));

            // Create Puppeteer config file with --no-sandbox for Docker environment
            const puppeteerConfigPath = path.join(tempDir, `${randomName}-puppeteer.json`);
            const puppeteerConfig = {
                "args": ["--no-sandbox", "--disable-setuid-sandbox"]
            };
            await fs.writeFile(puppeteerConfigPath, JSON.stringify(puppeteerConfig));

            // Use execFile (no shell) for better security
            const args = [
                '-i', tempInputDir,
                '-o', tempOutputDir,
                '-c', tempConfigPath,
                '-p', puppeteerConfigPath,  // Puppeteer config for Docker sandbox workaround
                '-w', '1920'
            ];

            await execFileAsync('mmdc', args, { timeout: RENDER_TIMEOUT });
            
            const rawSvg = await fs.readFile(tempOutputDir, 'utf-8');
            
            // Post-process SVG for font consistency and potential custom styling
            const processedSvg = await svgProcessor.process(rawSvg, 'mermaid', theme);
            return Buffer.from(processedSvg);

        } catch (error) {
            logger.error({ engine: this.name, error: error.stderr || error.message }, 'Mermaid rendering failed');
            const parsedError = this._parseError(error.stderr || error.message);
            throw parsedError;
        } finally {
            // Cleanup temporary files
            if (tempInputDir) await fs.rm(path.dirname(tempInputDir), { recursive: true, force: true });
        }
    }

    async validate(content) {
        // Mermaid CLI doesn't have a dedicated validate-only flag.
        // A quick render to a temporary file is the most reliable way.
        // We can optimize this if it becomes a bottleneck, but for now, correctness is key.
        try {
            await this.render(content, { theme: 'default' });
            return { valid: true, errors: [] };
        } catch (error) {
            return { valid: false, errors: [{ line: error.line || null, message: error.message }] };
        }
    }

    _parseError(stderr) {
        const error = new Error();
        error.engine = this.name;

        // Mermaid CLI errors are often generic but can sometimes be parsed
        if (stderr.includes('Syntax error in graph')) {
            error.code = 'SYNTAX_ERROR';
            error.message = 'Mermaid syntax error.';
            error.suggestion = 'Check the Mermaid syntax. Common issues include missing semicolons or incorrect keywords.';
        } else if (stderr.includes('timeout')) {
            error.code = 'TIMEOUT';
            error.message = 'Mermaid rendering timed out.';
            error.suggestion = 'The diagram is too complex. Try simplifying it.';
        } else {
            error.code = 'ENGINE_CRASH';
            error.message = stderr.split('\n')[0] || 'Mermaid engine failed unexpectedly.';
            error.suggestion = 'Please check the diagram content for errors.';
        }
        return error;
    }
}

module.exports = MermaidEngine;