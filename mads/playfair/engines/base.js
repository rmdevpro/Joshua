/**
 * Abstract base class for diagram rendering engines.
 * This defines the interface that all engine adapters must implement.
 */
class BaseEngine {
    constructor(name) {
        if (this.constructor === BaseEngine) {
            throw new Error("Abstract classes can't be instantiated.");
        }
        this.name = name;
    }

    /**
     * Renders a diagram from source content.
     * @param {string} content - The diagram source code (e.g., DOT or Mermaid syntax).
     * @param {object} options - Rendering options (theme, output_format, etc.).
     * @returns {Promise<Buffer>} - A promise that resolves with the rendered diagram as a Buffer.
     */
    async render(content, options) {
        throw new Error("Method 'render()' must be implemented.");
    }

    /**
     * Validates the syntax of the diagram source content.
     * @param {string} content - The diagram source code to validate.
     * @returns {Promise<{valid: boolean, errors: Array<{line: number, message: string}>}>}
     */
    async validate(content) {
        throw new Error("Method 'validate()' must be implemented.");
    }
}

module.exports = BaseEngine;