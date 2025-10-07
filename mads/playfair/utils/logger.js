const LOG_LEVEL = process.env.LOG_LEVEL || 'info';

const levels = {
    debug: 10,
    info: 20,
    warn: 30,
    error: 40,
};

const currentLevel = levels[LOG_LEVEL.toLowerCase()] || levels.info;

function log(level, data, message) {
    if (levels[level] < currentLevel) {
        return;
    }

    const logEntry = {
        level,
        timestamp: new Date().toISOString(),
        message,
        ...data,
    };

    // Output structured JSON log to stderr
    process.stderr.write(JSON.stringify(logEntry) + '\n');
}

module.exports = {
    debug: (data, message) => log('debug', data, message),
    info: (data, message) => log('info', data, message),
    warn: (data, message) => log('warn', data, message),
    error: (data, message) => log('error', data, message),
};