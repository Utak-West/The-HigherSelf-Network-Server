/**
 * Request logging middleware
 * Logs all incoming requests with relevant details for audit and debugging
 */
const requestLogger = (logger) => {
  return (req, res, next) => {
    // Capture original response methods to track response
    const originalSend = res.send;
    const originalJson = res.json;
    const originalEnd = res.end;

    // Log request details
    const startTime = Date.now();
    const requestId = req.headers['x-request-id'] || `req-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

    // Log request information
    logger.info(`Request received: ${req.method} ${req.originalUrl}`, {
      requestId,
      method: req.method,
      url: req.originalUrl,
      ip: req.ip,
      userAgent: req.headers['user-agent'],
      body: req.method !== 'GET' ? JSON.stringify(req.body) : null
    });

    // Override response methods to log response
    res.send = function (body) {
      const responseTime = Date.now() - startTime;
      logger.info(`Response sent: ${res.statusCode} (${responseTime}ms)`, {
        requestId,
        statusCode: res.statusCode,
        responseTime,
        contentLength: Buffer.isBuffer(body) ? body.length : (typeof body === 'string' ? body.length : null)
      });
      return originalSend.apply(res, arguments);
    };

    res.json = function (body) {
      const responseTime = Date.now() - startTime;
      logger.info(`Response sent: ${res.statusCode} (${responseTime}ms)`, {
        requestId,
        statusCode: res.statusCode,
        responseTime
      });
      return originalJson.apply(res, arguments);
    };

    res.end = function () {
      const responseTime = Date.now() - startTime;
      if (!res._headerSent) {
        logger.info(`Response sent: ${res.statusCode} (${responseTime}ms)`, {
          requestId,
          statusCode: res.statusCode,
          responseTime
        });
      }
      return originalEnd.apply(res, arguments);
    };

    // Add request ID to response headers for client-side tracking
    res.set('X-Request-ID', requestId);

    next();
  };
};

module.exports = { requestLogger };
