import redis from 'redis';

const LEVELS = { "TRACE": 5, "DEBUG": 10, "INFO": 20, "WARN": 30, "ERROR": 40 };
const DEFAULT_REDACT_FIELDS = new Set(['password', 'token', 'api_key', 'authorization', 'secret']);
const REDACTED_VALUE = "[REDACTED]";

export class ICCMLogger {
    /**
     * Non-blocking logger that sends logs to Godot via Redis (REQ-LIB-003)
     * @param {object} options
     * @param {string} options.component - Component name
     * @param {string} [options.redisUrl='redis://localhost:6379']
     * @param {string} [options.defaultLevel='INFO']
     * @param {string[]} [options.redactFields=[]]
     * @param {number} [options.maxQueueSize=100000]
     * @param {string} [options.logQueueName='logs:queue']
     */
    constructor({ component, redisUrl = 'redis://localhost:6379', defaultLevel = 'INFO', redactFields = [], maxQueueSize = 100000, logQueueName = 'logs:queue' }) {
        if (!component) {
            throw new Error('ICCMLogger requires a "component" name.');
        }
        this.component = component;
        this.level = LEVELS[defaultLevel.toUpperCase()] || LEVELS.INFO;
        this.redactFields = new Set([...DEFAULT_REDACT_FIELDS, ...redactFields]);
        this.maxQueueSize = maxQueueSize;
        this.logQueueName = logQueueName;
        this._redisAvailable = false;

        this.redisClient = redis.createClient({
            url: redisUrl,
            socket: { connectTimeout: 1000 }
        });

        // REQ-GOD-005: Lua script for atomic FIFO queue management
        this.luaScript = `
            local queue = KEYS[1]
            local max_size = tonumber(ARGV[1])
            local log_entry = ARGV[2]

            local current_size = redis.call('LLEN', queue)
            if current_size >= max_size then
                redis.call('RPOP', queue)
            end
            redis.call('LPUSH', queue, log_entry)
            return current_size + 1
        `;

        this.redisClient.on('error', (err) => {
            if (this._redisAvailable) {
                this._logFallbackWarning(`Redis connection error: ${err.message}. Falling back to local logging.`);
            }
            this._redisAvailable = false;
        });

        this.redisClient.on('ready', () => {
            if (!this._redisAvailable) {
                console.log(`[ICCMLogger INFO] ${this.component}: Successfully connected to Redis.`);
            }
            this._redisAvailable = true;
        });

        // Fire-and-forget connection attempt
        this.redisClient.connect().catch(err => {
            this._logFallbackWarning(`Could not connect to Redis at ${redisUrl}. Reason: ${err.message}. Falling back to local logging.`);
        });
    }

    /** REQ-LIB-005: Dynamically change the log level */
    setLevel(level) {
        const newLevel = LEVELS[level.toUpperCase()];
        if (newLevel !== undefined) {
            this.level = newLevel;
        } else {
            this._logFallbackWarning(`Invalid log level '${level}'. Level not changed.`);
        }
    }

    /** REQ-SEC-001/002/003: Recursively redact sensitive fields */
    _redact(data) {
        if (data === null || typeof data !== 'object') {
            return data;
        }

        if (Array.isArray(data)) {
            return data.map(item => this._redact(item));
        }

        const cleanData = {};
        for (const key in data) {
            if (Object.prototype.hasOwnProperty.call(data, key)) {
                if (this.redactFields.has(key.toLowerCase())) {
                    cleanData[key] = REDACTED_VALUE;
                } else {
                    cleanData[key] = this._redact(data[key]);
                }
            }
        }
        return cleanData;
    }

    /** Internal log method */
    async _log(levelName, message, data, traceId) {
        const levelNum = LEVELS[levelName];
        if (levelNum < this.level) {
            return; // REQ-LIB-006: Filter logs below current level
        }

        const logEntry = {
            component: this.component,
            level: levelName,
            message: message,
            trace_id: traceId || null, // REQ-COR-004, REQ-COR-005
            data: data ? this._redact(data) : null,
            created_at: new Date().toISOString()
        };

        // REQ-LIB-003: Non-blocking push with local fallback
        if (!this._redisAvailable) {
            this._logLocal(logEntry);
            return;
        }

        try {
            // REQ-LIB-004: Atomic FIFO queue management
            await this.redisClient.eval(
                this.luaScript,
                {
                    keys: [this.logQueueName],
                    arguments: [String(this.maxQueueSize), JSON.stringify(logEntry)]
                }
            );
        } catch (err) {
            this._redisAvailable = false;
            this._logFallbackWarning(`Redis command failed. Reason: ${err.message}. Falling back to local logging.`);
            this._logLocal(logEntry);
        }
    }

    /** REQ-LIB-007: Log a warning indicating fallback mode */
    _logFallbackWarning(message) {
        console.warn(`[ICCMLogger WARNING] ${this.component}: ${message}`);
    }

    /** Logs to stdout as a fallback */
    _logLocal(logEntry) {
        console.log(JSON.stringify(logEntry));
    }

    // REQ-LIB-001: Public log methods
    trace(message, data, traceId) { this._log('TRACE', message, data, traceId); }
    debug(message, data, traceId) { this._log('DEBUG', message, data, traceId); }
    info(message, data, traceId) { this._log('INFO', message, data, traceId); }
    warn(message, data, traceId) { this._log('WARN', message, data, traceId); }
    error(message, data, traceId) { this._log('ERROR', message, data, traceId); }

    /** Gracefully close the Redis connection */
    async close() {
        if (this.redisClient && this.redisClient.isOpen) {
            await this.redisClient.quit();
        }
    }
}
