const GraphvizEngine = require('../engines/graphviz');
const MermaidEngine = require('../engines/mermaid');

class Validator {
    constructor() {
        this.engines = {
            dot: new GraphvizEngine(),
            mermaid: new MermaidEngine(),
        };
    }

    /**
     * Validates the syntax of a diagram.
     * @param {string} content - The diagram source code.
     * @param {string} format - The format ('dot' or 'mermaid').
     * @returns {Promise<{valid: boolean, errors: Array, engine: string}>}
     */
    async validate(content, format) {
        const engine = this.engines[format];
        if (!engine) {
            return {
                valid: false,
                engine: 'unknown',
                errors: [{ message: `Unsupported format for validation: ${format}` }],
            };
        }

        const result = await engine.validate(content);
        return { ...result, engine: format };
    }
}

module.exports = Validator;