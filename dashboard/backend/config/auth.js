const jwt = require('jsonwebtoken');
const bcrypt = require('bcryptjs');
const { promisify } = require('util');
const winston = require('winston');
const db = require('../config/database');
const redis = require('../config/redis');

// Configure logger
const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.json()
  ),
  transports: [
    new winston.transports.Console({
      format: winston.format.simple()
    })
  ]
});

// JWT configuration
const JWT_SECRET = process.env.JWT_SECRET || 'your-secret-key';
const JWT_EXPIRES_IN = process.env.JWT_EXPIRES_IN || '24h';
const JWT_REFRESH_EXPIRES_IN = process.env.JWT_REFRESH_EXPIRES_IN || '7d';

// Authentication utilities
class AuthUtils {
  // Generate JWT token
  static generateToken(payload, expiresIn = JWT_EXPIRES_IN) {
    return jwt.sign(payload, JWT_SECRET, { expiresIn });
  }

  // Verify JWT token
  static async verifyToken(token) {
    try {
      return await promisify(jwt.verify)(token, JWT_SECRET);
    } catch (error) {
      throw new Error('Invalid token');
    }
  }

  // Hash password
  static async hashPassword(password) {
    const saltRounds = 12;
    return await bcrypt.hash(password, saltRounds);
  }

  // Compare password
  static async comparePassword(password, hashedPassword) {
    return await bcrypt.compare(password, hashedPassword);
  }

  // Generate refresh token
  static generateRefreshToken() {
    return jwt.sign(
      { type: 'refresh', timestamp: Date.now() },
      JWT_SECRET,
      { expiresIn: JWT_REFRESH_EXPIRES_IN }
    );
  }

  // Extract token from request
  static extractToken(req) {
    const authHeader = req.headers.authorization;
    if (authHeader && authHeader.startsWith('Bearer ')) {
      return authHeader.substring(7);
    }
    return req.cookies?.token || null;
  }

  // Get user permissions for organization
  static async getUserPermissions(userId, organizationId) {
    try {
      const membership = await db.query(`
        SELECT role, permissions, status
        FROM user_organizations
        WHERE user_id = ? AND organization_id = ? AND status = 'active'
      `, [userId, organizationId]);

      if (membership.length === 0) {
        return null;
      }

      const { role, permissions } = membership[0];
      
      // Default permissions based on role
      const defaultPermissions = {
        owner: ['*'],
        admin: ['read', 'write', 'delete', 'manage_users', 'manage_integrations'],
        manager: ['read', 'write', 'manage_team'],
        user: ['read', 'write'],
        viewer: ['read']
      };

      // Merge default permissions with custom permissions
      const userPermissions = permissions ? JSON.parse(permissions) : [];
      const rolePermissions = defaultPermissions[role] || ['read'];
      
      return {
        role,
        permissions: [...new Set([...rolePermissions, ...userPermissions])]
      };
    } catch (error) {
      logger.error('Error getting user permissions:', error);
      return null;
    }
  }

  // Check if user has specific permission
  static hasPermission(userPermissions, requiredPermission) {
    if (!userPermissions || !userPermissions.permissions) {
      return false;
    }

    const { permissions } = userPermissions;
    
    // Owner has all permissions
    if (permissions.includes('*')) {
      return true;
    }

    // Check for specific permission
    return permissions.includes(requiredPermission);
  }

  // Blacklist token (for logout)
  static async blacklistToken(token) {
    try {
      const decoded = await this.verifyToken(token);
      const expiresIn = decoded.exp - Math.floor(Date.now() / 1000);
      
      if (expiresIn > 0) {
        await redis.set(`blacklist:${token}`, 'true', expiresIn);
      }
    } catch (error) {
      logger.error('Error blacklisting token:', error);
    }
  }

  // Check if token is blacklisted
  static async isTokenBlacklisted(token) {
    try {
      const blacklisted = await redis.get(`blacklist:${token}`);
      return blacklisted === 'true';
    } catch (error) {
      logger.error('Error checking token blacklist:', error);
      return false;
    }
  }

  // Rate limiting for authentication attempts
  static async checkAuthRateLimit(identifier) {
    const key = `auth_attempts:${identifier}`;
    const maxAttempts = 5;
    const windowInSeconds = 900; // 15 minutes

    try {
      const attempts = await redis.get(key) || 0;
      
      if (attempts >= maxAttempts) {
        return {
          allowed: false,
          remaining: 0,
          resetTime: Date.now() + (windowInSeconds * 1000)
        };
      }

      return {
        allowed: true,
        remaining: maxAttempts - attempts - 1,
        resetTime: Date.now() + (windowInSeconds * 1000)
      };
    } catch (error) {
      logger.error('Error checking auth rate limit:', error);
      return { allowed: true, remaining: maxAttempts - 1 };
    }
  }

  // Record authentication attempt
  static async recordAuthAttempt(identifier, success = false) {
    const key = `auth_attempts:${identifier}`;
    const windowInSeconds = 900; // 15 minutes

    try {
      if (success) {
        // Clear attempts on successful login
        await redis.del(key);
      } else {
        // Increment failed attempts
        const current = await redis.get(key) || 0;
        await redis.set(key, parseInt(current) + 1, windowInSeconds);
      }
    } catch (error) {
      logger.error('Error recording auth attempt:', error);
    }
  }
}

// Authentication middleware
const authenticate = async (req, res, next) => {
  try {
    // Extract token from request
    const token = AuthUtils.extractToken(req);
    
    if (!token) {
      return res.status(401).json({
        error: 'Access denied',
        message: 'No token provided'
      });
    }

    // Check if token is blacklisted
    if (await AuthUtils.isTokenBlacklisted(token)) {
      return res.status(401).json({
        error: 'Access denied',
        message: 'Token has been revoked'
      });
    }

    // Verify token
    const decoded = await AuthUtils.verifyToken(token);
    
    // Get user from database
    const users = await db.query(`
      SELECT id, email, first_name, last_name, status, last_login
      FROM users
      WHERE id = ? AND status = 'active'
    `, [decoded.userId]);

    if (users.length === 0) {
      return res.status(401).json({
        error: 'Access denied',
        message: 'User not found or inactive'
      });
    }

    const user = users[0];

    // Update last login if it's been more than 1 hour
    const lastLogin = new Date(user.last_login);
    const oneHourAgo = new Date(Date.now() - 60 * 60 * 1000);
    
    if (!user.last_login || lastLogin < oneHourAgo) {
      await db.query(`
        UPDATE users 
        SET last_login = CURRENT_TIMESTAMP, login_count = login_count + 1
        WHERE id = ?
      `, [user.id]);
    }

    // Attach user to request
    req.user = {
      id: user.id,
      email: user.email,
      firstName: user.first_name,
      lastName: user.last_name,
      fullName: `${user.first_name} ${user.last_name}`
    };

    // Attach token to request for potential blacklisting
    req.token = token;

    next();
  } catch (error) {
    logger.error('Authentication error:', error);
    
    if (error.name === 'TokenExpiredError') {
      return res.status(401).json({
        error: 'Access denied',
        message: 'Token has expired'
      });
    }

    return res.status(401).json({
      error: 'Access denied',
      message: 'Invalid token'
    });
  }
};

// Organization access middleware
const requireOrganizationAccess = (requiredPermission = 'read') => {
  return async (req, res, next) => {
    try {
      const organizationId = req.params.organizationId || req.body.organizationId || req.query.organizationId;
      
      if (!organizationId) {
        return res.status(400).json({
          error: 'Bad request',
          message: 'Organization ID is required'
        });
      }

      // Get user permissions for this organization
      const permissions = await AuthUtils.getUserPermissions(req.user.id, organizationId);
      
      if (!permissions) {
        return res.status(403).json({
          error: 'Access denied',
          message: 'You do not have access to this organization'
        });
      }

      // Check if user has required permission
      if (!AuthUtils.hasPermission(permissions, requiredPermission)) {
        return res.status(403).json({
          error: 'Access denied',
          message: `You do not have '${requiredPermission}' permission for this organization`
        });
      }

      // Attach organization info to request
      req.organization = {
        id: organizationId,
        userRole: permissions.role,
        userPermissions: permissions.permissions
      };

      next();
    } catch (error) {
      logger.error('Organization access error:', error);
      return res.status(500).json({
        error: 'Internal server error',
        message: 'Error checking organization access'
      });
    }
  };
};

// Role-based access control middleware
const requireRole = (requiredRoles) => {
  const roles = Array.isArray(requiredRoles) ? requiredRoles : [requiredRoles];
  
  return (req, res, next) => {
    if (!req.organization) {
      return res.status(400).json({
        error: 'Bad request',
        message: 'Organization context required'
      });
    }

    if (!roles.includes(req.organization.userRole)) {
      return res.status(403).json({
        error: 'Access denied',
        message: `Required role: ${roles.join(' or ')}`
      });
    }

    next();
  };
};

// Permission-based access control middleware
const requirePermission = (requiredPermissions) => {
  const permissions = Array.isArray(requiredPermissions) ? requiredPermissions : [requiredPermissions];
  
  return (req, res, next) => {
    if (!req.organization) {
      return res.status(400).json({
        error: 'Bad request',
        message: 'Organization context required'
      });
    }

    const userPermissions = req.organization.userPermissions;
    const hasPermission = permissions.some(permission => 
      userPermissions.includes('*') || userPermissions.includes(permission)
    );

    if (!hasPermission) {
      return res.status(403).json({
        error: 'Access denied',
        message: `Required permission: ${permissions.join(' or ')}`
      });
    }

    next();
  };
};

// Optional authentication middleware (for public endpoints with optional user context)
const optionalAuth = async (req, res, next) => {
  try {
    const token = AuthUtils.extractToken(req);
    
    if (token && !(await AuthUtils.isTokenBlacklisted(token))) {
      const decoded = await AuthUtils.verifyToken(token);
      
      const users = await db.query(`
        SELECT id, email, first_name, last_name
        FROM users
        WHERE id = ? AND status = 'active'
      `, [decoded.userId]);

      if (users.length > 0) {
        const user = users[0];
        req.user = {
          id: user.id,
          email: user.email,
          firstName: user.first_name,
          lastName: user.last_name,
          fullName: `${user.first_name} ${user.last_name}`
        };
      }
    }

    next();
  } catch (error) {
    // Ignore authentication errors for optional auth
    next();
  }
};

module.exports = {
  AuthUtils,
  authenticate,
  requireOrganizationAccess,
  requireRole,
  requirePermission,
  optionalAuth
};

