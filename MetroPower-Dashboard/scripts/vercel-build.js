#!/usr/bin/env node

/**
 * Vercel Build Script for MetroPower Dashboard
 *
 * This script prepares the application for deployment on Vercel by:
 * 1. Installing backend dependencies
 * 2. Copying necessary files
 * 3. Setting up the serverless environment
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

console.log('🚀 Starting Vercel build process for MetroPower Dashboard...');

const rootDir = path.join(__dirname, '..');
const backendDir = path.join(rootDir, 'backend');
const apiDir = path.join(rootDir, 'api');

try {
  // Ensure API directory exists
  if (!fs.existsSync(apiDir)) {
    fs.mkdirSync(apiDir, { recursive: true });
    console.log('✅ Created API directory');
  }

  // Install backend dependencies if package.json exists
  if (fs.existsSync(path.join(backendDir, 'package.json'))) {
    console.log('📦 Installing backend dependencies...');
    process.chdir(backendDir);
    execSync('npm ci --production', { stdio: 'inherit' });
    console.log('✅ Backend dependencies installed');
  }

  // Copy environment template if it doesn't exist
  const envExample = path.join(rootDir, '.env.example');
  const envFile = path.join(rootDir, '.env');

  if (!fs.existsSync(envFile) && fs.existsSync(envExample)) {
    fs.copyFileSync(envExample, envFile);
    console.log('✅ Environment file template copied');
  }

  // Verify required files exist
  const requiredFiles = [
    path.join(apiDir, 'index.js'),
    path.join(apiDir, 'debug.js'),
    path.join(rootDir, 'vercel.json')
  ];

  for (const file of requiredFiles) {
    if (!fs.existsSync(file)) {
      throw new Error(`Required file missing: ${file}`);
    }
  }

  console.log('✅ All required files verified');

  // Create uploads and exports directories if they don't exist
  const dirs = ['uploads', 'exports'];
  for (const dir of dirs) {
    const dirPath = path.join(rootDir, dir);
    if (!fs.existsSync(dirPath)) {
      fs.mkdirSync(dirPath, { recursive: true });
      // Create .gitkeep file
      fs.writeFileSync(path.join(dirPath, '.gitkeep'), '');
      console.log(`✅ Created ${dir} directory`);
    }
  }

  console.log('🎉 Vercel build completed successfully!');
  console.log('');
  console.log('Next steps:');
  console.log('1. Set up environment variables in Vercel dashboard');
  console.log('2. Configure database connection (if using external database)');
  console.log('3. Deploy to Vercel');

} catch (error) {
  console.error('❌ Build failed:', error.message);
  process.exit(1);
}
