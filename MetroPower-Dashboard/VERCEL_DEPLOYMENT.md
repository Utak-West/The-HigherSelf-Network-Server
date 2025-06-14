# MetroPower Dashboard - Vercel Deployment Guide

This guide will help you deploy the MetroPower Dashboard to Vercel.

## Prerequisites

- GitHub account with access to the repository
- Vercel account (free tier is sufficient for testing)
- Node.js 18+ installed locally (for testing)

## Quick Deployment

### Option 1: Deploy via Vercel Dashboard

1. **Connect Repository**
   - Go to [Vercel Dashboard](https://vercel.com/dashboard)
   - Click "New Project"
   - Import your GitHub repository
   - Select the `MetroPower-Dashboard` directory as the root

2. **Configure Build Settings**
   - Framework Preset: `Other`
   - Root Directory: `MetroPower-Dashboard`
   - Build Command: `npm run vercel-build`
   - Output Directory: Leave empty (handled by vercel.json)

3. **Set Environment Variables**
   - Copy variables from `.env.example`
   - Set required variables (see Environment Variables section below)

4. **Deploy**
   - Click "Deploy"
   - Wait for deployment to complete

### Option 2: Deploy via Vercel CLI

```bash
# Install Vercel CLI
npm i -g vercel

# Navigate to project directory
cd MetroPower-Dashboard

# Login to Vercel
vercel login

# Deploy
vercel --prod
```

## Environment Variables

### Required Variables

Set these in your Vercel project settings:

```env
NODE_ENV=production
JWT_SECRET=your-super-secret-jwt-key-here
APP_NAME=MetroPower Dashboard
COMPANY_NAME=MetroPower
BRANCH_NAME=Tucker Branch
CORS_ORIGIN=https://your-vercel-app.vercel.app
WEBSOCKET_CORS_ORIGIN=https://your-vercel-app.vercel.app
```

### Optional Variables

```env
# Email configuration (if using email features)
FROM_EMAIL=noreply@metropower.com
FROM_NAME=MetroPower Dashboard

# Database (if using external database)
DATABASE_URL=postgresql://user:pass@host:port/db

# Redis (if using external Redis)
REDIS_URL=redis://user:pass@host:port

# Feature flags
DEMO_MODE_ENABLED=true
LOG_LEVEL=info
```

## Project Structure

```
MetroPower-Dashboard/
├── api/                    # Vercel serverless functions
│   ├── index.js           # Main API handler
│   └── debug.js           # Debug endpoint
├── backend/               # Express.js backend
│   ├── server.js          # Main server file
│   ├── src/               # Source code
│   └── package.json       # Backend dependencies
├── frontend/              # Static frontend files
│   ├── index.html         # Main HTML file
│   ├── css/               # Stylesheets
│   ├── js/                # JavaScript files
│   └── assets/            # Images, icons, etc.
├── scripts/               # Build and utility scripts
│   └── vercel-build.js    # Vercel build script
├── vercel.json            # Vercel configuration
├── package.json           # Root package.json
└── .env.example           # Environment variables template
```

## Configuration Files

### vercel.json

The `vercel.json` file configures:
- Serverless function builds
- Static file serving
- Route handling
- Environment variables
- Build settings

### API Handlers

- `/api/index.js` - Main application handler
- `/api/debug.js` - Debug and health check endpoint

## Testing Deployment

After deployment, test these endpoints:

1. **Health Check**: `https://your-app.vercel.app/health`
2. **Debug Info**: `https://your-app.vercel.app/api/debug`
3. **API Docs**: `https://your-app.vercel.app/api-docs`
4. **Frontend**: `https://your-app.vercel.app/`

## Troubleshooting

### Common Issues

1. **Build Failures**
   - Check Node.js version (requires 18+)
   - Verify all dependencies are listed in package.json
   - Check build logs in Vercel dashboard

2. **Runtime Errors**
   - Check environment variables are set correctly
   - Review function logs in Vercel dashboard
   - Test debug endpoint for configuration issues

3. **CORS Issues**
   - Update CORS_ORIGIN environment variable
   - Include your Vercel domain in allowed origins

### Debug Commands

```bash
# Test build locally
npm run vercel-build

# Test API locally
vercel dev

# Check logs
vercel logs
```

## Custom Domain

To use a custom domain:

1. Go to your Vercel project settings
2. Navigate to "Domains"
3. Add your custom domain
4. Update DNS records as instructed
5. Update CORS_ORIGIN environment variable

## Monitoring

- Use Vercel Analytics for performance monitoring
- Check function logs in Vercel dashboard
- Monitor error rates and response times

## Support

For deployment issues:
1. Check Vercel documentation
2. Review build and function logs
3. Test locally with `vercel dev`
4. Contact support if needed

## Security Notes

- Never commit `.env` files to version control
- Use strong JWT secrets in production
- Enable HTTPS only (Vercel provides this by default)
- Regularly update dependencies
- Monitor for security vulnerabilities
