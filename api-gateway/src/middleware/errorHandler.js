/**
 * Global error handling middleware
 * Provides consistent error responses across the API
 */
const errorHandler = (err, req, res, next) => {
  // Default error status and message
  const status = err.status || 500;
  const message = err.message || 'Internal Server Error';
  
  // Log the error (will be handled by Winston in production)
  console.error(`[ERROR] ${err.stack}`);
  
  // Send the error response
  res.status(status).json({
    error: {
      message,
      status,
      timestamp: new Date().toISOString()
    }
  });
};

module.exports = { errorHandler };
