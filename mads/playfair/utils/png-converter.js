const sharp = require('sharp');
const logger = require('./logger');

class PngConverter {
    /**
     * Converts an SVG buffer to a PNG buffer.
     * @param {Buffer} svgBuffer - The input SVG data.
     * @param {number} width - The target width in pixels.
     * @param {number} [height] - The target height in pixels (optional, maintains aspect ratio if omitted).
     * @returns {Promise<Buffer>} - A promise that resolves with the PNG buffer.
     */
    async convert(svgBuffer, width = 1920, height) {
        try {
            return await sharp(svgBuffer, { density: 144 }) // Use higher density for better quality text
                .resize(width, height, {
                    fit: 'inside',
                    withoutEnlargement: true,
                })
                .png({
                    quality: 90,
                    compressionLevel: 6,
                })
                .toBuffer();
        } catch (error) {
            logger.error({ error: error.message }, 'Failed to convert SVG to PNG');
            const err = new Error('PNG conversion failed. The source SVG may be invalid.');
            err.code = 'CONVERSION_ERROR';
            throw err;
        }
    }
}

module.exports = PngConverter;