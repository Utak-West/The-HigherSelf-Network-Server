#!/usr/bin/env node

/**
 * Test script to verify Vercel configuration
 */

const fs = require('fs');
const path = require('path');

console.log('🔍 Testing Vercel configuration...\n');

const rootDir = path.join(__dirname, '..');
const errors = [];
const warnings = [];

// Check required files
const requiredFiles = [
  'vercel.json',
  'api/index.js',
  'api/debug.js',
  'package.json',
  '.env.example',
  'frontend/index.html'
];

console.log('📁 Checking required files:');
requiredFiles.forEach(file => {
  const filePath = path.join(rootDir, file);
  if (fs.existsSync(filePath)) {
    console.log(`  ✅ ${file}`);
  } else {
    console.log(`  ❌ ${file}`);
    errors.push(`Missing required file: ${file}`);
  }
});

// Check vercel.json structure
console.log('\n⚙️  Checking vercel.json configuration:');
try {
  const vercelConfig = JSON.parse(fs.readFileSync(path.join(rootDir, 'vercel.json'), 'utf8'));

  if (vercelConfig.version === 2) {
    console.log('  ✅ Version 2 configuration');
  } else {
    warnings.push('Vercel configuration should use version 2');
  }

  if (vercelConfig.builds && vercelConfig.builds.length > 0) {
    console.log('  ✅ Build configurations found');
  } else {
    errors.push('No build configurations found in vercel.json');
  }

  if (vercelConfig.routes && vercelConfig.routes.length > 0) {
    console.log('  ✅ Route configurations found');
  } else {
    warnings.push('No route configurations found in vercel.json');
  }

} catch (error) {
  errors.push(`Invalid vercel.json: ${error.message}`);
}

// Check package.json scripts
console.log('\n📦 Checking package.json scripts:');
try {
  const packageJson = JSON.parse(fs.readFileSync(path.join(rootDir, 'package.json'), 'utf8'));

  const requiredScripts = ['build', 'vercel-build'];
  requiredScripts.forEach(script => {
    if (packageJson.scripts && packageJson.scripts[script]) {
      console.log(`  ✅ ${script} script found`);
    } else {
      warnings.push(`Missing recommended script: ${script}`);
    }
  });

} catch (error) {
  errors.push(`Invalid package.json: ${error.message}`);
}

// Check backend structure
console.log('\n🔧 Checking backend structure:');
const backendFiles = [
  'backend/server.js',
  'backend/package.json'
];

backendFiles.forEach(file => {
  const filePath = path.join(rootDir, file);
  if (fs.existsSync(filePath)) {
    console.log(`  ✅ ${file}`);
  } else {
    console.log(`  ❌ ${file}`);
    errors.push(`Missing backend file: ${file}`);
  }
});

// Check frontend structure
console.log('\n🎨 Checking frontend structure:');
const frontendFiles = [
  'frontend/index.html',
  'frontend/css',
  'frontend/js'
];

frontendFiles.forEach(file => {
  const filePath = path.join(rootDir, file);
  if (fs.existsSync(filePath)) {
    console.log(`  ✅ ${file}`);
  } else {
    console.log(`  ❌ ${file}`);
    warnings.push(`Missing frontend file/directory: ${file}`);
  }
});

// Summary
console.log('\n📊 Summary:');
if (errors.length === 0 && warnings.length === 0) {
  console.log('🎉 All checks passed! Your project is ready for Vercel deployment.');
} else {
  if (errors.length > 0) {
    console.log(`❌ ${errors.length} error(s) found:`);
    errors.forEach(error => console.log(`   - ${error}`));
  }

  if (warnings.length > 0) {
    console.log(`⚠️  ${warnings.length} warning(s) found:`);
    warnings.forEach(warning => console.log(`   - ${warning}`));
  }

  if (errors.length > 0) {
    console.log('\n🔧 Please fix the errors before deploying to Vercel.');
    process.exit(1);
  } else {
    console.log('\n✅ No critical errors found. You can proceed with deployment.');
  }
}

console.log('\n📚 Next steps:');
console.log('1. Set up environment variables in Vercel dashboard');
console.log('2. Connect your GitHub repository to Vercel');
console.log('3. Deploy using the Vercel dashboard or CLI');
console.log('4. Test the deployed application');
