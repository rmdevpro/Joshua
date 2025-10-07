const { optimize } = require('svgo');
const graphvizThemes = require('./graphviz-themes.json');

/**
 * SVG Post-Processor for applying modern aesthetics.
 * This module is critical for achieving the desired look and feel,
 * especially for Graphviz which has limited native styling options.
 */
class SvgProcessor {
    constructor() {
        this.svgoConfig = {
            plugins: [
                'preset-default',
                'removeDimensions',
                {
                    name: 'addAttributesToSVGElement',
                    params: {
                        attributes: [
                            { width: '100%' },
                            { height: '100%' }
                        ]
                    }
                }
            ],
        };
    }

    /**
     * Main processing function.
     * @param {string} rawSvg - The raw SVG string from the rendering engine.
     * @param {string} engine - 'graphviz' or 'mermaid'.
     * @param {string} themeName - The name of the theme being applied.
     * @returns {Promise<string>} - The processed and optimized SVG string.
     */
    async process(rawSvg, engine, themeName) {
        let svg = rawSvg;

        // Apply engine-specific enhancements
        if (engine === 'graphviz') {
            svg = this._applyGraphvizEnhancements(svg, themeName);
        } else {
            // For Mermaid, we primarily ensure font consistency
            svg = this._applyFontConsistency(svg, 'Roboto, sans-serif');
        }

        // Optimize the final SVG using SVGO
        const { data: optimizedSvg } = optimize(svg, this.svgoConfig);

        return optimizedSvg;
    }

    /**
     * Applies enhancements specific to Graphviz output.
     * This includes adding CSS for fonts, gradients, and shadows.
     * @param {string} svg - The SVG string.
     * @param {string} themeName - The theme name.
     * @returns {string} - The enhanced SVG string.
     */
    _applyGraphvizEnhancements(svg, themeName) {
        const theme = graphvizThemes[themeName];
        if (!theme) return svg;

        const fontName = theme.graph.fontname || 'Inter, sans-serif';

        // 1. Define styles in a <style> tag for better maintainability
        // Fonts (Inter, Roboto) are installed in container - no external dependency
        const style = `
        .graph {
            font-family: ${fontName};
        }
        .node text {
            font-family: ${theme.node.fontname || fontName};
            font-size: ${theme.node.fontsize || 11}px;
        }
        .edge text {
            font-family: ${theme.edge.fontname || fontName};
            font-size: ${theme.edge.fontsize || 10}px;
        }
        ${this._getThemeSpecificCss(themeName)}
        `;

        // 2. Inject the <defs> and <style> block into the SVG
        const styleBlock = `<defs/><style>${style}</style>`;
        return svg.replace(/<g/, `${styleBlock}<g`);
    }

    /**
     * Generates additional CSS for special effects like gradients.
     * @param {string} themeName - The theme name.
     * @returns {string} - Additional CSS rules.
     */
    _getThemeSpecificCss(themeName) {
        if (themeName === 'modern') {
            return `
            .node > polygon {
                fill: url(#modern-gradient);
            }
            .node > path {
                fill: url(#modern-gradient);
            }
            <defs>
              <linearGradient id="modern-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" style="stop-color:#667EEA;stop-opacity:1" />
                <stop offset="100%" style="stop-color:#764BA2;stop-opacity:1" />
              </linearGradient>
            </defs>
            `;
        }
        return '';
    }

    /**
     * Ensures consistent font usage across different engines.
     * @param {string} svg - The SVG string.
     * @param {string} fontFamily - The font family to apply.
     * @returns {string} - The modified SVG string.
     */
    _applyFontConsistency(svg, fontFamily) {
        // Fonts installed in container - no external dependency
        const style = `
        .root { font-family: ${fontFamily}; }
        `;
        const styleBlock = `<defs/><style>${style}</style>`;
        return svg.replace(/<svg/, `<svg class="root"`).replace(/<g/, `${styleBlock}<g`);
    }
}

module.exports = new SvgProcessor();