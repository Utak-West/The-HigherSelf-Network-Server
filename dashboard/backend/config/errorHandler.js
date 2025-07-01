const winston = require('winston');

// Configure logger
const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.json()
  ),
  transports: [
    new winston.transports.File({ filename: 'logs/error.log', level: 'error' }),
    new winston.transports.Console({
      format: winston.format.simple()
    })
  ]
});

// Custom error class for application errors
class AppError extends Error {
  constructor(message, statusCode, code = null, details = null) {
    super(message);
    this.statusCode = statusCode;
    this.code = code;
    this.details = details;
    this.isOperational = true;

    Error.captureStackTrace(this, this.constructor);
  }
}

// Error handler middleware
const errorHandler = (err, req, res, next) => {
  let error = { ...err };
  error.message = err.message;

  // Log error
  logger.error('Error occurred:', {
    message: err.message,
    stack: err.stack,
    url: req.url,
    method: req.method,
    ip: req.ip,
    userAgent: req.get('User-Agent'),
    userId: req.user?.id,
    organizationId: req.organization?.id
  });

  // Mongoose bad ObjectId
  if (err.name === 'CastError') {
    const message = 'Resource not found';
    error = new AppError(message, 404, 'RESOURCE_NOT_FOUND');
  }

  // Mongoose duplicate key
  if (err.code === 11000) {
    const message = 'Duplicate field value entered';
    error = new AppError(message, 400, 'DUPLICATE_FIELD');
  }

  // Mongoose validation error
  if (err.name === 'ValidationError') {
    const message = Object.values(err.errors).map(val => val.message).join(', ');
    error = new AppError(message, 400, 'VALIDATION_ERROR');
  }

  // JWT errors
  if (err.name === 'JsonWebTokenError') {
    const message = 'Invalid token';
    error = new AppError(message, 401, 'INVALID_TOKEN');
  }

  if (err.name === 'TokenExpiredError') {
    const message = 'Token expired';
    error = new AppError(message, 401, 'TOKEN_EXPIRED');
  }

  // MySQL errors
  if (err.code === 'ER_DUP_ENTRY') {
    const message = 'Duplicate entry';
    error = new AppError(message, 409, 'DUPLICATE_ENTRY');
  }

  if (err.code === 'ER_NO_SUCH_TABLE') {
    const message = 'Database table not found';
    error = new AppError(message, 500, 'DATABASE_ERROR');
  }

  if (err.code === 'ER_ACCESS_DENIED_ERROR') {
    const message = 'Database access denied';
    error = new AppError(message, 500, 'DATABASE_ACCESS_ERROR');
  }

  // Redis errors
  if (err.code === 'ECONNREFUSED' && err.address) {
    const message = 'Cache service unavailable';
    error = new AppError(message, 503, 'CACHE_UNAVAILABLE');
  }

  // Rate limiting errors
  if (err.status === 429) {
    const message = 'Too many requests';
    error = new AppError(message, 429, 'RATE_LIMIT_EXCEEDED');
  }

  // File upload errors
  if (err.code === 'LIMIT_FILE_SIZE') {
    const message = 'File too large';
    error = new AppError(message, 413, 'FILE_TOO_LARGE');
  }

  if (err.code === 'LIMIT_UNEXPECTED_FILE') {
    const message = 'Unexpected file field';
    error = new AppError(message, 400, 'UNEXPECTED_FILE');
  }

  // Network errors
  if (err.code === 'ENOTFOUND' || err.code === 'ECONNRESET') {
    const message = 'Network error occurred';
    error = new AppError(message, 503, 'NETWORK_ERROR');
  }

  // Default to 500 server error
  const statusCode = error.statusCode || 500;
  const errorCode = error.code || 'INTERNAL_SERVER_ERROR';

  // Prepare error response
  const errorResponse = {
    error: error.message || 'Internal server error',
    code: errorCode,
    timestamp: new Date().toISOString(),
    path: req.url,
    method: req.method
  };

  // Add additional details in development
  if (process.env.NODE_ENV === 'development') {
    errorResponse.stack = err.stack;
    errorResponse.details = error.details;
  }

  // Add request ID if available
  if (req.requestId) {
    errorResponse.requestId = req.requestId;
  }

  // Send error response
  res.status(statusCode).json(errorResponse);
};

// Async error wrapper
const asyncHandler = (fn) => (req, res, next) => {
  Promise.resolve(fn(req, res, next)).catch(next);
};

// 404 handler
const notFound = (req, res, next) => {
  const error = new AppError(`Not found - ${req.originalUrl}`, 404, 'NOT_FOUND');
  next(error);
};

// Validation error formatter
const formatValidationErrors = (errors) => {
  return errors.array().map(error => ({
    field: error.param,
    message: error.msg,
    value: error.value,
    location: error.location
  }));
};

// Database error handler
const handleDatabaseError = (error) => {
  logger.error('Database error:', error);
  
  // Don't expose internal database errors in production
  if (process.env.NODE_ENV === 'production') {
    return new AppError('Database operation failed', 500, 'DATABASE_ERROR');
  }
  
  return error;
};

// Integration error handler
const handleIntegrationError = (error, serviceName) => {
  logger.error(`Integration error with ${serviceName}:`, error);
  
  return new AppError(
    `Integration with ${serviceName} failed`,
    503,
    'INTEGRATION_ERROR',
    { service: serviceName, originalError: error.message }
  );
};

// Rate limit error handler
const handleRateLimitError = (req, res, next) => {
  const error = new AppError(
    'Too many requests from this IP, please try again later',
    429,
    'RATE_LIMIT_EXCEEDED',
    {
      ip: req.ip,
      retryAfter: req.rateLimit?.resetTime
    }
  );
  next(error);
};

// Graceful shutdown error handler
const handleShutdownError = (error) => {
  logger.error('Shutdown error:', error);
  
  // Force exit after 30 seconds
  setTimeout(() => {
    logger.error('Could not close connections in time, forcefully shutting down');
    process.exit(1);
  }, 30000);
};

// Unhandled promise rejection handler
process.on('unhandledRejection', (err, promise) => {
  logger.error('Unhandled Promise Rejection:', err);
  
  // Close server & exit process
  if (process.env.NODE_ENV === 'production') {
    process.exit(1);
  }
});

// Uncaught exception handler
process.on('uncaughtException', (err) => {
  logger.error('Uncaught Exception:', err);
  
  // Close server & exit process
  process.exit(1);
});

module.exports = {
  AppError,
  errorHandler,
  asyncHandler,
  notFound,
  formatValidationErrors,
  handleDatabaseError,
  handleIntegrationError,
  handleRateLimitError,
  handleShutdownError
};

