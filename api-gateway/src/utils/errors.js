/**
 * Custom error classes for the API Gateway
 * Provides specific error types for different scenarios
 */

/**
 * Base API Error class
 */
class ApiError extends Error {
  constructor(message, status = 500) {
    super(message);
    this.name = this.constructor.name;
    this.status = status;
    Error.captureStackTrace(this, this.constructor);
  }
}

/**
 * 400 Bad Request - Invalid input
 */
class BadRequestError extends ApiError {
  constructor(message = 'Bad Request') {
    super(message, 400);
  }
}

/**
 * 401 Unauthorized - Authentication error
 */
class UnauthorizedError extends ApiError {
  constructor(message = 'Unauthorized') {
    super(message, 401);
  }
}

/**
 * 403 Forbidden - Permission error
 */
class ForbiddenError extends ApiError {
  constructor(message = 'Forbidden') {
    super(message, 403);
  }
}

/**
 * 404 Not Found - Resource not found
 */
class NotFoundError extends ApiError {
  constructor(message = 'Resource not found') {
    super(message, 404);
  }
}

/**
 * 429 Too Many Requests - Rate limit exceeded
 */
class RateLimitError extends ApiError {
  constructor(message = 'Rate limit exceeded') {
    super(message, 429);
  }
}

/**
 * Notion Database Error - Issues with Notion integration
 */
class NotionDatabaseError extends ApiError {
  constructor(message = 'Notion Database Error', originalError = null) {
    super(message, 500);
    this.originalError = originalError;
  }
}

/**
 * Workflow State Error - Invalid state transition
 */
class WorkflowStateError extends BadRequestError {
  constructor(message = 'Invalid workflow state transition') {
    super(message);
  }
}

module.exports = {
  ApiError,
  BadRequestError,
  UnauthorizedError,
  ForbiddenError,
  NotFoundError,
  RateLimitError,
  NotionDatabaseError,
  WorkflowStateError
};
