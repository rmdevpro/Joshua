const logger = require('../utils/logger');
const PngConverter = require('../utils/png-converter');
const GraphvizEngine = require('../engines/graphviz');
const MermaidEngine = require('../engines/mermaid');

const POOL_SIZE = parseInt(process.env.WORKER_POOL_SIZE, 10) || 3;
const MAX_QUEUE_SIZE = parseInt(process.env.MAX_QUEUE_SIZE, 10) || 50;

class WorkerPool {
    constructor() {
        this.queue = [];
        this.activeWorkers = 0;
        this.engines = {
            dot: new GraphvizEngine(),
            mermaid: new MermaidEngine(),
        };
        this.pngConverter = new PngConverter();
        logger.info({ size: POOL_SIZE, queueSize: MAX_QUEUE_SIZE }, 'Worker pool initialized');
    }

    submit(job) {
        return new Promise((resolve, reject) => {
            if (this.queue.length >= MAX_QUEUE_SIZE) {
                const err = new Error('Server is busy. Please try again later.');
                err.code = 'QUEUE_FULL';
                return reject(err);
            }

            // Simple priority: smaller content gets higher priority
            const priority = job.content.length < 1000 ? 1 : 0;
            this.queue.push({ job, resolve, reject, priority });
            this.queue.sort((a, b) => b.priority - a.priority); // Higher priority first

            this._processQueue();
        });
    }

    _processQueue() {
        if (this.activeWorkers >= POOL_SIZE || this.queue.length === 0) {
            return;
        }

        this.activeWorkers++;
        const { job, resolve } = this.queue.shift();

        this._runJob(job)
            .then(resolve)
            .catch(err => {
                // The promise from submit() will be rejected here if an error occurs
                // We format the error to match the required MCP error structure
                const formattedError = {
                    error: true,
                    code: err.code || 'RENDERING_FAILED',
                    message: err.message,
                    engine: err.engine,
                    line: err.line,
                    suggestion: err.suggestion,
                };
                resolve({ error: formattedError });
            })
            .finally(() => {
                this.activeWorkers--;
                this._processQueue(); // Check for more jobs
            });
    }

    async _runJob(job) {
        const { format, content, options } = job;
        const startTime = Date.now();

        logger.info({ format, theme: options.theme, output: options.output_format }, 'Starting diagram render');

        const engine = this.engines[format];
        if (!engine) {
            throw { code: 'UNSUPPORTED_FORMAT', message: `Format '${format}' is not supported.` };
        }

        // Render to SVG first
        const svgBuffer = await engine.render(content, options);

        let data;
        // Convert to PNG if requested
        if (options.output_format === 'png') {
            data = await this.pngConverter.convert(svgBuffer, options.width, options.height);
        } else {
            data = svgBuffer;
        }

        const duration = Date.now() - startTime;
        logger.info({ format, duration, size: data.length }, 'Diagram render complete');

        return { data };
    }
    
    getStatus() {
        return {
            queue_depth: this.queue.length,
            active_workers: this.activeWorkers,
            pool_size: POOL_SIZE,
        };
    }
}

module.exports = WorkerPool;