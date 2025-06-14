/**
 * Debug API Endpoint for Vercel Deployment
 *
 * Provides debugging information and health checks for the deployed application
 */

const path = require('path');

// Set up environment for backend modules
process.env.NODE_PATH = path.join(__dirname, '../backend/node_modules');
require('module')._initPaths();

// Load environment variables
require('dotenv').config({ path: path.join(__dirname, '../.env') });

const handler = async (req, res) => {
  try {
    const debugInfo = {
      timestamp: new Date().toISOString(),
      environment: process.env.NODE_ENV || 'development',
      vercel: process.env.VERCEL || 'false',
      region: process.env.VERCEL_REGION || 'unknown',
      version: process.env.npm_package_version || '1.0.0',
      app: {
        name: process.env.APP_NAME || 'MetroPower Dashboard',
        company: process.env.COMPANY_NAME || 'MetroPower',
        branch: process.env.BRANCH_NAME || 'Tucker Branch'
      },
      config: {
        demoMode: process.env.DEMO_MODE_ENABLED || 'true',
        logLevel: process.env.LOG_LEVEL || 'info',
        fileLogging: process.env.DISABLE_FILE_LOGGING || 'true'
      },
      request: {
        method: req.method,
        url: req.url,
        headers: {
          'user-agent': req.headers['user-agent'],
          'x-forwarded-for': req.headers['x-forwarded-for'],
          'x-vercel-id': req.headers['x-vercel-id']
        }
      },
      system: {
        nodeVersion: process.version,
        platform: process.platform,
        arch: process.arch,
        memory: process.memoryUsage(),
        uptime: process.uptime()
      }
    };

    // Set appropriate headers
    res.setHeader('Content-Type', 'application/json');
    res.setHeader('Cache-Control', 'no-cache, no-store, must-revalidate');

    res.status(200).json({
      status: 'success',
      message: 'MetroPower Dashboard Debug Information',
      data: debugInfo
    });

  } catch (error) {
    console.error('Debug endpoint error:', error);
    res.status(500).json({
      status: 'error',
      message: 'Debug endpoint failed',
      error: process.env.NODE_ENV === 'development' ? error.message : 'Internal server error',
      timestamp: new Date().toISOString()
    });
  }
};

module.exports = handler;
