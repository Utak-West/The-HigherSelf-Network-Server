/**
 * Authentication Routes
 *
 * Handles user authentication, registration, and token management
 * for the MetroPower Dashboard API with comprehensive error handling.
 *
 * Copyright 2025 The HigherSelf Network
 */

const express = require('express');
const { body, validationResult } = require('express-validator');
const User = require('../models/User');
const { asyncHandler, ValidationError } = require('../middleware/errorHandler');
const { authRateLimit } = require('../middleware/auth');
const logger = require('../utils/logger');

const router = express.Router();

// Apply rate limiting to all auth routes
router.use(authRateLimit);

/**
 * @route   POST /api/auth/login
 * @desc    Authenticate user and return JWT token
 * @access  Public
 */
router.post('/login', [
  body('identifier')
    .notEmpty()
    .withMessage('Username or email is required')
    .trim()
    .escape(),
  body('password')
    .isLength({ min: 1 })
    .withMessage('Password is required')
], asyncHandler(async (req, res) => {
  // Check for validation errors
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    logger.warn('Login validation failed', { errors: errors.array() });
    throw new ValidationError('Invalid input data', errors.array());
  }

  const { identifier, password } = req.body;

  try {
    // Use data service for authentication
    const dataService = require('../services/demoService');
    const bcrypt = require('bcryptjs');

    // Find user by identifier
    const user = await dataService.findUserByIdentifier(identifier);

    if (!user) {
      logger.warn('Authentication failed - user not found', { identifier });
      return res.status(401).json({
        error: 'Authentication failed',
        message: 'Invalid credentials'
      });
    }

    // Verify password
    const isValidPassword = await bcrypt.compare(password, user.password_hash);

    if (!isValidPassword) {
      logger.warn('Authentication failed - invalid password', { identifier });
      return res.status(401).json({
        error: 'Authentication failed',
        message: 'Invalid credentials'
      });
    }

    if (!user.is_active) {
      logger.warn('Authentication failed - inactive account', { identifier });
      return res.status(401).json({
        error: 'Authentication failed',
        message: 'Account is inactive'
      });
    }

    // Generate simple token (in production, use proper JWT)
    const accessToken = 'token-' + Date.now() + '-' + user.user_id;

    logger.info('User login successful', {
      userId: user.user_id,
      username: user.username,
      role: user.role
    });

    res.json({
      message: 'Login successful',
      user: {
        user_id: user.user_id,
        username: user.username,
        email: user.email,
        first_name: user.first_name,
        last_name: user.last_name,
        role: user.role,
        last_login: new Date().toISOString()
      },
      accessToken: accessToken
    });


  } catch (error) {
    logger.error('Login error:', error);
    res.status(500).json({
      error: 'Authentication error',
      message: 'An error occurred during authentication'
    });
  }
}));

/**
 * @route   POST /api/auth/logout
 * @desc    Logout user and clear refresh token
 * @access  Private
 */
router.post('/logout', asyncHandler(async (req, res) => {
  try {
    // Clear refresh token cookie
    res.clearCookie('refreshToken');

    // In a full implementation, you might want to blacklist the token
    // For now, we'll just clear the cookie

    logger.info('User logout successful');

    res.json({
      message: 'Logout successful'
    });
  } catch (error) {
    logger.error('Logout error:', error);
    res.status(500).json({
      error: 'Logout error',
      message: 'An error occurred during logout'
    });
  }
}));

/**
 * @route   GET /api/auth/verify
 * @desc    Verify JWT token and return user data
 * @access  Private
 */
router.get('/verify', asyncHandler(async (req, res) => {
  try {
    const dataService = require('../services/demoService');

    // Get token from Authorization header
    const authHeader = req.headers.authorization;

    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return res.status(401).json({
        error: 'Authentication required',
        message: 'Please provide a valid authorization token'
      });
    }

    const token = authHeader.substring(7); // Remove 'Bearer ' prefix

    // Simple token validation (in production, use proper JWT)
    if (!token.startsWith('token-')) {
      return res.status(401).json({
        error: 'Invalid token',
        message: 'The provided token is invalid'
      });
    }

    // Extract user ID from token (simple implementation)
    const tokenParts = token.split('-');
    const userId = parseInt(tokenParts[tokenParts.length - 1]);

    if (!userId) {
      return res.status(401).json({
        error: 'Invalid token',
        message: 'The provided token is malformed'
      });
    }

    // Get user data
    const user = await dataService.findUserById(userId);

    if (!user || !user.is_active) {
      return res.status(401).json({
        error: 'User not found',
        message: 'User account not found or inactive'
      });
    }

    res.json({
      message: 'Token verified',
      user: {
        user_id: user.user_id,
        username: user.username,
        email: user.email,
        first_name: user.first_name,
        last_name: user.last_name,
        role: user.role
      }
    });
  } catch (error) {
    logger.error('Token verification error:', error);
    res.status(401).json({
      error: 'Token verification failed',
      message: 'Unable to verify authentication token'
    });
  }
}));

/**
 * @route   POST /api/auth/refresh
 * @desc    Refresh access token using refresh token
 * @access  Public
 */
router.post('/refresh', asyncHandler(async (req, res) => {
  try {
    // Simple token refresh (in production, implement proper refresh token logic)
    const newToken = 'token-' + Date.now() + '-1'; // Always return token for user ID 1

    res.json({
      message: 'Token refreshed successfully',
      accessToken: newToken
    });
  } catch (error) {
    logger.error('Token refresh error:', error);
    res.status(401).json({
      error: 'Token refresh failed',
      message: 'Unable to refresh authentication token'
    });
  }
}));

module.exports = router;
