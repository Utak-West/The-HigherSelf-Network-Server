# MetroPower Dashboard - Vercel Deployment Checklist

## Pre-Deployment Checklist

### ✅ Repository Setup
- [ ] Code is committed to GitHub repository
- [ ] Repository is accessible to your Vercel account
- [ ] All required files are present (run `node scripts/test-vercel-config.js` to verify)

### ✅ Configuration Files
- [ ] `vercel.json` is configured correctly
- [ ] `api/index.js` and `api/debug.js` are present
- [ ] `.env.example` contains all required environment variables
- [ ] `package.json` has correct build scripts

### ✅ Environment Variables Preparation
Prepare these environment variables for Vercel:

**Required:**
- [ ] `NODE_ENV=production`
- [ ] `JWT_SECRET` (generate a strong secret)
- [ ] `APP_NAME=MetroPower Dashboard`
- [ ] `COMPANY_NAME=MetroPower`
- [ ] `BRANCH_NAME=Tucker Branch`

**CORS Configuration:**
- [ ] `CORS_ORIGIN` (will be your Vercel domain)
- [ ] `WEBSOCKET_CORS_ORIGIN` (will be your Vercel domain)

**Optional but Recommended:**
- [ ] `FROM_EMAIL` and `FROM_NAME` (for email features)
- [ ] `DATABASE_URL` (if using external database)
- [ ] `REDIS_URL` (if using external Redis)

## Deployment Steps

### Option 1: Vercel Dashboard (Recommended)

1. **Connect Repository**
   - [ ] Go to [Vercel Dashboard](https://vercel.com/dashboard)
   - [ ] Click "New Project"
   - [ ] Import your GitHub repository
   - [ ] Select `MetroPower-Dashboard` as root directory

2. **Configure Project**
   - [ ] Framework Preset: `Other`
   - [ ] Root Directory: `MetroPower-Dashboard`
   - [ ] Build Command: `npm run vercel-build`
   - [ ] Output Directory: (leave empty)

3. **Set Environment Variables**
   - [ ] Add all required environment variables
   - [ ] Update CORS origins with your Vercel domain

4. **Deploy**
   - [ ] Click "Deploy"
   - [ ] Wait for deployment to complete

### Option 2: Vercel CLI

1. **Install CLI**
   ```bash
   npm i -g vercel
   ```

2. **Deploy**
   ```bash
   cd MetroPower-Dashboard
   vercel login
   vercel --prod
   ```

## Post-Deployment Testing

### ✅ Basic Functionality
- [ ] Visit your deployed URL
- [ ] Check health endpoint: `/health`
- [ ] Check debug endpoint: `/api/debug`
- [ ] Verify API documentation: `/api-docs`

### ✅ Frontend Testing
- [ ] Main dashboard loads correctly
- [ ] CSS and JavaScript files load
- [ ] Images and assets display properly
- [ ] Responsive design works on mobile

### ✅ API Testing
- [ ] Authentication endpoints work
- [ ] Employee data endpoints respond
- [ ] File upload functionality (if applicable)
- [ ] Export functionality (if applicable)

### ✅ Error Handling
- [ ] 404 pages display correctly
- [ ] API errors return proper JSON responses
- [ ] CORS headers are set correctly

## Troubleshooting

### Common Issues and Solutions

**Build Failures:**
- [ ] Check Node.js version (requires 18+)
- [ ] Verify all dependencies in package.json
- [ ] Review build logs in Vercel dashboard

**Runtime Errors:**
- [ ] Check environment variables are set
- [ ] Review function logs in Vercel dashboard
- [ ] Test debug endpoint for configuration

**CORS Issues:**
- [ ] Update CORS_ORIGIN environment variable
- [ ] Include your Vercel domain in allowed origins

**Performance Issues:**
- [ ] Check function timeout settings
- [ ] Monitor function execution time
- [ ] Optimize large dependencies

## Security Checklist

### ✅ Production Security
- [ ] Strong JWT secret is set
- [ ] Environment variables are secure
- [ ] HTTPS is enabled (automatic with Vercel)
- [ ] CORS is properly configured
- [ ] Rate limiting is enabled

### ✅ Data Protection
- [ ] No sensitive data in client-side code
- [ ] Database credentials are secure
- [ ] File uploads are validated
- [ ] User input is sanitized

## Monitoring and Maintenance

### ✅ Setup Monitoring
- [ ] Enable Vercel Analytics
- [ ] Monitor function logs
- [ ] Set up error tracking
- [ ] Monitor performance metrics

### ✅ Regular Maintenance
- [ ] Update dependencies regularly
- [ ] Monitor security vulnerabilities
- [ ] Review and rotate secrets
- [ ] Backup important data

## Custom Domain (Optional)

### ✅ Domain Setup
- [ ] Add custom domain in Vercel settings
- [ ] Update DNS records
- [ ] Verify SSL certificate
- [ ] Update CORS_ORIGIN environment variable

## Final Verification

- [ ] All tests pass
- [ ] Application is accessible
- [ ] All features work as expected
- [ ] Performance is acceptable
- [ ] Security measures are in place
- [ ] Monitoring is configured

## Support Resources

- [Vercel Documentation](https://vercel.com/docs)
- [Node.js Serverless Functions](https://vercel.com/docs/functions/serverless-functions/runtimes/node-js)
- [Environment Variables](https://vercel.com/docs/projects/environment-variables)
- [Custom Domains](https://vercel.com/docs/projects/domains)

---

**Note:** Keep this checklist updated as your application evolves and new requirements are added.
