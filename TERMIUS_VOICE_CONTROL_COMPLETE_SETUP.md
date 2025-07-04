# Termius Voice Control Complete Setup Guide
## HigherSelf Network Server Voice-Activated Management

### 🎯 Overview

This comprehensive guide provides everything you need to set up Termius for voice-controlled management of your HigherSelf Network server. You'll be able to start, stop, restart, and monitor your server using voice commands through Termius Pro.

### 📋 Prerequisites

1. **Termius Pro** - Download from [https://termius.com/](https://termius.com/)
2. **SiteGround Hosting Account** - Jump Start Plan (4 CPU, 8GB RAM, 40GB SSD)
3. **Microphone** - For voice command input
4. **SSH Access** - To your server environment

### 🔑 Credentials Setup

#### 1. Environment Variables (.env file)
A comprehensive `.env` file has been created with all necessary configurations:

```bash
# Core server settings
ENVIRONMENT=development
SERVER_HOST=0.0.0.0
SERVER_PORT=8000

# Voice control settings
VOICE_COMMAND_ENABLED=true
TERMIUS_VOICE_CONTROL_ENABLED=true
AQUA_API_KEY=your_aqua_api_key_here

# Database configurations
SUPABASE_URL=https://mmmtfmulvmvtxybwxxrr.supabase.co
SUPABASE_API_KEY=your_supabase_api_key_here
REDIS_URI=redis://redis-18441.c280.us-central1-2.gce.redns.redis-cloud.com:18441

# SiteGround hosting credentials (replace with your actual credentials)
SITEGROUND_FTP_HOST=your_siteground_ftp_host
SITEGROUND_FTP_USERNAME=your_siteground_ftp_username
SITEGROUND_FTP_PASSWORD=your_siteground_ftp_password
```

#### 2. SiteGround Credentials Location

**FTP/SFTP Access:**
- Login to your SiteGround control panel
- Navigate to **Websites** → **Site Tools** → **File Manager**
- Or go to **Websites** → **Site Tools** → **FTP Accounts**
- Your credentials will be displayed there

**Database Access:**
- In SiteGround control panel: **Websites** → **Site Tools** → **MySQL**
- Database credentials are shown in the **MySQL Databases** section

**SSH Access:**
- Go to **Websites** → **Site Tools** → **SSH Keys Manager**
- Generate or upload your SSH key for secure access

### 🚀 Quick Setup Instructions

#### Step 1: Run the Setup Script
```bash
# Navigate to your project directory
cd /path/to/The-HigherSelf-Network-Server-2

# Run the voice control setup script
./scripts/termius/setup-voice-control.sh
```

#### Step 2: Configure Termius Pro
1. **Install Termius Pro** from the official website
2. **Import Host Configuration:**
   - Open Termius Pro
   - Go to **Settings** → **Import**
   - Import `termius-setup/hosts-voice-control.json`
3. **Import Voice Snippets:**
   - Import `termius-setup/snippets-voice-control.json`
4. **Enable Voice Recognition:**
   - Go to **Settings** → **Voice**
   - Enable microphone access
   - Set confidence threshold to 0.8

#### Step 3: Set Up SSH Connection
1. **Generate SSH Key** (if not already done):
   ```bash
   ssh-keygen -t ed25519 -f ~/.ssh/higherself_dev_ed25519 -C "higherself-dev"
   ```
2. **Add to SSH Agent:**
   ```bash
   ssh-add ~/.ssh/higherself_dev_ed25519
   ```
3. **Configure in Termius:**
   - Add the private key to Termius keychain
   - Associate with the HigherSelf host

### 🎤 Voice Commands Available

#### Server Management
- **"start higher self server"** - Start the server
- **"stop higher self server"** - Stop the server
- **"restart higher self server"** - Restart the server
- **"server status"** - Check server health and status
- **"show server logs"** - Display recent server logs

#### Development Operations
- **"deploy server"** - Deploy to specified environment
- **"run tests"** - Execute the test suite
- **"build server"** - Build Docker images

#### Environment-Specific Commands
Add environment suffix for specific deployments:
- **"deploy to production"** - Deploy to production environment
- **"start staging server"** - Start staging environment

### 🔧 Configuration Files Created

1. **`.env`** - Complete environment configuration
2. **`services/voice_server_control.py`** - Voice control service
3. **`termius-setup/snippets-voice-control.json`** - Termius voice snippets
4. **`termius-setup/hosts-voice-control.json`** - Voice-enabled host configuration
5. **`scripts/termius/setup-voice-control.sh`** - Automated setup script

### 📊 API Endpoints Added

The following voice control endpoints have been added to the server:

- **POST** `/voice/server/control` - Process text-based server commands
- **POST** `/voice/server/transcribe-and-control` - Process audio files for server control

### 🛠️ Usage Instructions

#### 1. Start Your Server
```bash
# Traditional method
docker-compose up -d

# Or use voice command in Termius
"start higher self server"
```

#### 2. Connect via Termius
1. Open Termius Pro
2. Connect to "HigherSelf-Voice-Local" host
3. Ensure microphone is enabled

#### 3. Use Voice Commands
1. Speak clearly into your microphone
2. Use exact trigger phrases
3. Wait for command confirmation
4. Monitor execution in the terminal

### 🔍 Testing Your Setup

#### 1. Test Server API
```bash
# Test the voice control API
curl -X POST "http://localhost:8000/voice/server/control" \
  -H "Content-Type: application/json" \
  -d '{"command": "server status", "environment": "development"}'
```

#### 2. Test Voice Recognition
1. In Termius, try: **"server status"**
2. Verify the command executes
3. Check the response in the terminal

#### 3. Test Server Operations
1. **"stop higher self server"** - Should stop all services
2. **"start higher self server"** - Should restart services
3. **"show server logs"** - Should display recent logs

### 🔒 Security Features

- **Session Logging** - All voice commands are logged
- **Confirmation Required** - Production commands require confirmation
- **SSH Key Authentication** - Secure connection to servers
- **Environment Isolation** - Separate configurations per environment

### 📈 Monitoring and Logs

#### Server Health Endpoints
- **API Health:** `http://localhost:8000/health`
- **Redis Health:** `http://localhost:8000/health/redis`
- **MongoDB Health:** `http://localhost:8000/health/mongodb`

#### Log Locations
- **Application Logs:** `./logs/app.log`
- **Docker Logs:** `docker-compose logs`
- **Termius Session Logs:** Available in Termius Pro

### 🚨 Troubleshooting

#### Voice Recognition Issues
1. **Check microphone permissions** in Termius
2. **Verify trigger phrases** are exact
3. **Adjust confidence threshold** if needed
4. **Test with manual commands** first

#### Server Connection Issues
1. **Verify SSH key setup** and permissions
2. **Check server accessibility** and firewall
3. **Confirm Docker services** are running
4. **Review environment variables** in `.env`

#### API Endpoint Issues
1. **Ensure server is running** on port 8000
2. **Check voice router endpoints** are loaded
3. **Verify environment configuration**
4. **Review server logs** for errors

### 🎯 Next Steps

1. **Customize Voice Commands** - Edit snippet configurations
2. **Set Up Production Environment** - Configure production hosts
3. **Integrate with CI/CD** - Automate deployments
4. **Monitor Performance** - Set up alerts and monitoring

### 📞 Support

For issues or questions:
1. **Check server logs:** `docker-compose logs -f`
2. **Review voice API responses** in browser dev tools
3. **Verify Termius configuration** in settings
4. **Test manual command execution** via SSH

### 🎉 Congratulations!

You now have a fully voice-controlled HigherSelf Network server management system through Termius Pro. You can start, stop, restart, and monitor your server using simple voice commands, making server management more efficient and hands-free.

**Remember to:**
- Keep your credentials secure
- Test in development before production use
- Monitor voice command execution
- Update configurations as needed

Happy voice-controlled server management! 🎤🚀
