/**
 * Vercel Serverless Function Entry Point
 *
 * This file serves as the main entry point for the MetroPower Dashboard API
 * when deployed on Vercel. It imports and configures the Express app from
 * the backend directory and exports it as a serverless function.
 */

const path = require('path');

// Set up environment for backend modules
process.env.NODE_PATH = path.join(__dirname, '../backend/node_modules');
require('module')._initPaths();

// Load environment variables
require('dotenv').config({ path: path.join(__dirname, '../.env') });

// Import the Express app from backend
const { app, initializeApp } = require('../backend/server');

// Initialize the application
let initialized = false;

const handler = async (req, res) => {
  try {
    // Initialize app on first request
    if (!initialized) {
      await initializeApp();
      initialized = true;
    }

    // Handle the request
    return app(req, res);
  } catch (error) {
    console.error('Serverless function error:', error);
    res.status(500).json({
      error: 'Internal Server Error',
      message: process.env.NODE_ENV === 'development' ? error.message : 'Something went wrong'
    });
  }
};

module.exports = handler;
