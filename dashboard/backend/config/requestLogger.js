const winston = require('winston');
const { v4: uuidv4 } = require('uuid');

// Configure logger
const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.json()
  ),
  transports: [
    new winston.transports.File({ filename: 'logs/access.log' }),
    new winston.transports.Console({
      format: winston.format.simple()
    })
  ]
});

// Request logging middleware
const requestLogger = (req, res, next) => {
  // Generate unique request ID
  req.requestId = uuidv4();
  
  // Add request ID to response headers
  res.setHeader('X-Request-ID', req.requestId);

  // Capture start time
  const startTime = Date.now();

  // Extract relevant request information
  const requestInfo = {
    requestId: req.requestId,
    method: req.method,
    url: req.url,
    originalUrl: req.originalUrl,
    ip: req.ip || req.connection.remoteAddress,
    userAgent: req.get('User-Agent'),
    referer: req.get('Referer'),
    contentType: req.get('Content-Type'),
    contentLength: req.get('Content-Length'),
    host: req.get('Host'),
    protocol: req.protocol,
    secure: req.secure,
    timestamp: new Date().toISOString()
  };

  // Add user info if authenticated
  if (req.user) {
    requestInfo.userId = req.user.id;
    requestInfo.userEmail = req.user.email;
  }

  // Add organization info if available
  if (req.organization) {
    requestInfo.organizationId = req.organization.id;
    requestInfo.userRole = req.organization.userRole;
  }

  // Log sensitive routes differently
  const sensitiveRoutes = ['/auth/login', '/auth/register', '/auth/reset-password'];
  const isSensitive = sensitiveRoutes.some(route => req.url.includes(route));

  if (isSensitive) {
    requestInfo.sensitive = true;
    // Don't log request body for sensitive routes
  } else {
    // Log request body for non-sensitive routes (limit size)
    if (req.body && Object.keys(req.body).length > 0) {
      const bodyString = JSON.stringify(req.body);
      requestInfo.bodySize = bodyString.length;
      
      // Only log body if it's small enough
      if (bodyString.length < 1000) {
        requestInfo.body = req.body;
      }
    }
  }

  // Log query parameters
  if (req.query && Object.keys(req.query).length > 0) {
    requestInfo.query = req.query;
  }

  // Log request parameters
  if (req.params && Object.keys(req.params).length > 0) {
    requestInfo.params = req.params;
  }

  // Override res.end to capture response information
  const originalEnd = res.end;
  res.end = function(chunk, encoding) {
    // Calculate response time
    const responseTime = Date.now() - startTime;

    // Capture response information
    const responseInfo = {
      requestId: req.requestId,
      statusCode: res.statusCode,
      statusMessage: res.statusMessage,
      responseTime: responseTime,
      contentLength: res.get('Content-Length'),
      contentType: res.get('Content-Type')
    };

    // Determine log level based on status code
    let logLevel = 'info';
    if (res.statusCode >= 400 && res.statusCode < 500) {
      logLevel = 'warn';
    } else if (res.statusCode >= 500) {
      logLevel = 'error';
    }

    // Create combined log entry
    const logEntry = {
      type: 'http_request',
      request: requestInfo,
      response: responseInfo,
      duration: responseTime
    };

    // Log the request/response
    logger.log(logLevel, 'HTTP Request', logEntry);

    // Call original end method
    originalEnd.call(this, chunk, encoding);
  };

  // Log incoming request
  logger.info('Incoming Request', {
    type: 'http_request_start',
    requestId: req.requestId,
    method: req.method,
    url: req.url,
    ip: requestInfo.ip,
    userAgent: requestInfo.userAgent,
    userId: requestInfo.userId,
    organizationId: requestInfo.organizationId
  });

  next();
};

// Performance monitoring middleware
const performanceMonitor = (req, res, next) => {
  const startTime = process.hrtime.bigint();

  // Override res.end to capture performance metrics
  const originalEnd = res.end;
  res.end = function(chunk, encoding) {
    const endTime = process.hrtime.bigint();
    const duration = Number(endTime - startTime) / 1000000; // Convert to milliseconds

    // Log performance metrics for slow requests
    if (duration > 1000) { // Log requests taking more than 1 second
      logger.warn('Slow Request', {
        type: 'performance_warning',
        requestId: req.requestId,
        method: req.method,
        url: req.url,
        duration: duration,
        statusCode: res.statusCode,
        memoryUsage: process.memoryUsage(),
        cpuUsage: process.cpuUsage()
      });
    }

    // Store performance metrics for monitoring
    if (req.performanceMetrics) {
      req.performanceMetrics.push({
        endpoint: `${req.method} ${req.route?.path || req.url}`,
        duration: duration,
        statusCode: res.statusCode,
        timestamp: new Date()
      });
    }

    originalEnd.call(this, chunk, encoding);
  };

  next();
};

// Security logging middleware
const securityLogger = (req, res, next) => {
  // Log potential security events
  const securityEvents = [];

  // Check for suspicious patterns
  const suspiciousPatterns = [
    /\.\.\//,  // Directory traversal
    /<script/i, // XSS attempts
    /union.*select/i, // SQL injection
    /javascript:/i, // JavaScript injection
    /eval\(/i, // Code injection
    /exec\(/i  // Command injection
  ];

  const checkForSuspiciousContent = (content) => {
    if (typeof content === 'string') {
      return suspiciousPatterns.some(pattern => pattern.test(content));
    }
    if (typeof content === 'object') {
      return Object.values(content).some(value => checkForSuspiciousContent(value));
    }
    return false;
  };

  // Check URL for suspicious patterns
  if (checkForSuspiciousContent(req.url)) {
    securityEvents.push({
      type: 'suspicious_url',
      url: req.url,
      pattern: 'potential_injection'
    });
  }

  // Check request body for suspicious patterns
  if (req.body && checkForSuspiciousContent(req.body)) {
    securityEvents.push({
      type: 'suspicious_body',
      pattern: 'potential_injection'
    });
  }

  // Check for unusual request headers
  const suspiciousHeaders = ['x-forwarded-for', 'x-real-ip', 'x-originating-ip'];
  suspiciousHeaders.forEach(header => {
    if (req.get(header) && req.get(header) !== req.ip) {
      securityEvents.push({
        type: 'header_mismatch',
        header: header,
        value: req.get(header),
        actualIp: req.ip
      });
    }
  });

  // Log security events
  if (securityEvents.length > 0) {
    logger.warn('Security Event', {
      type: 'security_warning',
      requestId: req.requestId,
      ip: req.ip,
      userAgent: req.get('User-Agent'),
      url: req.url,
      method: req.method,
      events: securityEvents,
      userId: req.user?.id,
      timestamp: new Date().toISOString()
    });
  }

  next();
};

// API usage tracking middleware
const apiUsageTracker = (req, res, next) => {
  // Track API usage for rate limiting and analytics
  const apiKey = req.get('X-API-Key');
  const userId = req.user?.id;
  const organizationId = req.organization?.id;

  if (apiKey || userId) {
    const usageInfo = {
      type: 'api_usage',
      requestId: req.requestId,
      apiKey: apiKey ? `${apiKey.substring(0, 8)}...` : null,
      userId: userId,
      organizationId: organizationId,
      endpoint: req.url,
      method: req.method,
      ip: req.ip,
      userAgent: req.get('User-Agent'),
      timestamp: new Date().toISOString()
    };

    // Log API usage
    logger.info('API Usage', usageInfo);

    // Store usage metrics (could be sent to analytics service)
    if (global.apiUsageMetrics) {
      global.apiUsageMetrics.push(usageInfo);
    }
  }

  next();
};

// Error correlation middleware
const errorCorrelation = (req, res, next) => {
  // Add error correlation context
  req.errorContext = {
    requestId: req.requestId,
    timestamp: new Date().toISOString(),
    url: req.url,
    method: req.method,
    ip: req.ip,
    userAgent: req.get('User-Agent'),
    userId: req.user?.id,
    organizationId: req.organization?.id
  };

  next();
};

module.exports = {
  requestLogger,
  performanceMonitor,
  securityLogger,
  apiUsageTracker,
  errorCorrelation
};

