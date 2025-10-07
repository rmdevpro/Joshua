const fs = require('fs/promises');
const path = require('path');
const logger = require('./utils/logger');
const WorkerPool = require('./workers/worker-pool');
const Validator = require('./utils/validator');
const formatDetector = require('./utils/format-detector');

const EXAMPLES_DIR = path.join(__dirname, 'examples');

class McpTools {
    constructor() {
        this.workerPool = new WorkerPool();
        this.validator = new Validator();
        this.tools = [
            {
                name: 'playfair_create_diagram',
                description: 'Create a professional diagram from Graphviz DOT or Mermaid specification.',
                inputSchema: {
                    type: 'object',
                    properties: {
                        content: { type: 'string', description: 'Diagram specification (DOT or Mermaid syntax).' },
                        format: { type: 'string', enum: ['dot', 'mermaid', 'auto'], default: 'auto', description: 'Input format.' },
                        output_format: { type: 'string', enum: ['svg', 'png'], default: 'svg', description: 'Output image format.' },
                        theme: { type: 'string', enum: ['professional', 'modern', 'minimal', 'dark'], default: 'modern', description: 'Visual theme.' },
                        width: { type: 'integer', default: 1920, description: 'Output width in pixels for PNG.' },
                        height: { type: 'integer', description: 'Output height in pixels (auto if not specified).' },
                        output_path: { type: 'string', description: 'Optional: file path for output. If not specified, returns base64 data.' },
                    },
                    required: ['content'],
                },
            },
            {
                name: 'playfair_list_capabilities',
                description: 'List all supported diagram formats, themes, and capabilities.',
                inputSchema: { type: 'object', properties: {} },
            },
            {
                name: 'playfair_get_examples',
                description: 'Get example syntax for a specific diagram type.',
                inputSchema: {
                    type: 'object',
                    properties: {
                        diagram_type: { type: 'string', enum: ['flowchart', 'orgchart', 'architecture', 'sequence', 'network', 'mindmap', 'er', 'state'] },
                    },
                    required: ['diagram_type'],
                },
            },
            {
                name: 'playfair_validate_syntax',
                description: 'Validate diagram syntax without rendering.',
                inputSchema: {
                    type: 'object',
                    properties: {
                        content: { type: 'string', description: 'Diagram specification to validate.' },
                        format: { type: 'string', enum: ['dot', 'mermaid', 'auto'], default: 'auto' },
                    },
                    required: ['content'],
                },
            },
        ];
    }

    listTools() {
        return this.tools;
    }

    async callTool(name, input, clientId) {
        logger.info({ clientId, tool: name, input: { ...input, content: '...' } }, 'Tool call initiated');
        try {
            switch (name) {
                case 'playfair_create_diagram':
                    return await this.createDiagram(input);
                case 'playfair_list_capabilities':
                    return this.listCapabilities();
                case 'playfair_get_examples':
                    return await this.getExamples(input);
                case 'playfair_validate_syntax':
                    return await this.validateSyntax(input);
                default:
                    return { error: true, code: 'TOOL_NOT_FOUND', message: `Tool '${name}' not found.` };
            }
        } catch (error) {
            logger.error({ clientId, tool: name, error: error.message, stack: error.stack }, 'Tool call failed');
            return {
                error: true,
                code: error.code || 'INTERNAL_ERROR',
                message: error.message || 'An unexpected error occurred.',
            };
        }
    }

    async createDiagram(input) {
        const { content, format: specifiedFormat = 'auto', width, height, output_path, ...options } = input;

        if (!content) {
            return { error: true, code: 'MISSING_CONTENT', message: 'Input "content" is required.' };
        }

        // Resource limit: Enforce maximum PNG dimensions to prevent DoS
        const MAX_PNG_WIDTH = parseInt(process.env.MAX_PNG_WIDTH, 10) || 8192;
        const MAX_PNG_HEIGHT = parseInt(process.env.MAX_PNG_HEIGHT, 10) || 8192;

        if (width && width > MAX_PNG_WIDTH) {
            return { error: true, code: 'INVALID_DIMENSION', message: `Width exceeds maximum allowed (${MAX_PNG_WIDTH}px).` };
        }
        if (height && height > MAX_PNG_HEIGHT) {
            return { error: true, code: 'INVALID_DIMENSION', message: `Height exceeds maximum allowed (${MAX_PNG_HEIGHT}px).` };
        }
        if (width && width < 1) {
            return { error: true, code: 'INVALID_DIMENSION', message: 'Width must be a positive integer.' };
        }
        if (height && height < 1) {
            return { error: true, code: 'INVALID_DIMENSION', message: 'Height must be a positive integer.' };
        }

        const format = specifiedFormat === 'auto' ? formatDetector.detect(content) : specifiedFormat;
        if (!format) {
            return { error: true, code: 'FORMAT_DETECTION_FAILED', message: 'Could not auto-detect diagram format. Please specify "dot" or "mermaid".' };
        }

        const job = { format, content, options: { ...options, width, height } };
        const result = await this.workerPool.submit(job);

        // Result contains { data: Buffer, error: null } or { data: null, error: {...} }
        if (result.error) {
            return result.error;
        }

        // If output_path is specified, save to file instead of returning base64
        if (output_path) {
            try {
                await fs.writeFile(output_path, result.data);
                logger.info({ output_path, size: result.data.length }, 'Diagram saved to file');
                return {
                    result: {
                        format: options.output_format || 'svg',
                        output_path: output_path,
                        size: result.data.length,
                    },
                };
            } catch (error) {
                logger.error({ output_path, error: error.message }, 'Failed to write diagram to file');
                return { error: true, code: 'FILE_WRITE_ERROR', message: `Failed to write file: ${error.message}` };
            }
        }

        // Default: return base64 data
        return {
            result: {
                format: options.output_format || 'svg',
                encoding: 'base64',
                data: result.data.toString('base64'),
            },
        };
    }

    listCapabilities() {
        return {
            result: {
                engines: ['graphviz', 'mermaid'],
                input_formats: ['dot', 'mermaid'],
                output_formats: ['svg', 'png'],
                themes: ['professional', 'modern', 'minimal', 'dark'],
                diagram_types: {
                    graphviz: ['flowchart', 'orgchart', 'architecture', 'network', 'mindmap'],
                    mermaid: ['sequence', 'er', 'state', 'flowchart', 'mindmap'],
                },
            },
        };
    }

    async getExamples(input) {
        const { diagram_type } = input;
        const exampleMap = {
            flowchart: 'flowchart.dot',
            orgchart: 'orgchart.dot',
            architecture: 'architecture.dot',
            network: 'network.dot',
            mindmap: 'mindmap.dot',
            sequence: 'sequence.mmd',
            er: 'er.mmd',
            state: 'state.mmd',
        };
        const filename = exampleMap[diagram_type];
        if (!filename) {
            return { error: true, code: 'INVALID_DIAGRAM_TYPE', message: `Unknown diagram_type: ${diagram_type}` };
        }

        try {
            const content = await fs.readFile(path.join(EXAMPLES_DIR, filename), 'utf-8');
            return { result: { diagram_type, content } };
        } catch (error) {
            logger.error({ diagram_type, error: error.message }, 'Failed to read example file');
            return { error: true, code: 'EXAMPLE_NOT_FOUND', message: 'Could not load example file.' };
        }
    }

    async validateSyntax(input) {
        const { content, format: specifiedFormat = 'auto' } = input;
        if (!content) {
            return { error: true, code: 'MISSING_CONTENT', message: 'Input "content" is required.' };
        }

        const format = specifiedFormat === 'auto' ? formatDetector.detect(content) : specifiedFormat;
        if (!format) {
            return { error: true, code: 'FORMAT_DETECTION_FAILED', message: 'Could not auto-detect diagram format.' };
        }

        const result = await this.validator.validate(content, format);
        return { result };
    }
    
    getHealthStatus() {
        return {
            status: 'healthy',
            engines: ['graphviz', 'mermaid'],
            ...this.workerPool.getStatus(),
        };
    }
}

module.exports = McpTools;