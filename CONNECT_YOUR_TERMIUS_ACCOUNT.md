# 🔗 Connect Your Termius Account to HigherSelf Network Server

## Overview

This guide shows you exactly how to connect your actual Termius app to receive real-time GitHub Actions notifications from the HigherSelf Network Server.

## 🚀 Quick Start (5 minutes)

### Step 1: Run the Connection Script

```bash
# Navigate to your project
cd "/Users/utakwest/Documents/HigherSelf/The HigherSelf Network /The HigherSelf Network Server"

# Run the connection setup
./scripts/termius/connect_termius_account.sh
```

This script will:
- ✅ Install required dependencies (paramiko, rich)
- ✅ Generate SSH keys for notifications
- ✅ Register your current terminal session
- ✅ Create Termius startup scripts
- ✅ Send a test notification

### Step 2: Configure Termius App

#### On macOS/iOS Termius App:

1. **Open Termius** on your Mac or iPhone/iPad

2. **Add New Host**:
   - Click the "+" button
   - Name: `HigherSelf-Notifications`
   - Address: `localhost` (or your Mac's IP if connecting from mobile)
   - Port: `22`
   - Username: `utakwest` (your Mac username)

3. **Import SSH Key**:
   - Go to Keychain in Termius
   - Click "+" to add new key
   - Name: `HigherSelf-Notifications`
   - Import private key from: `/Users/utakwest/.ssh/termius_higherself_notifications`

4. **Set Startup Command** (Optional but recommended):
   - In host settings, set startup command:
   ```bash
   /Users/utakwest/.termius_higherself/scripts/termius_startup.sh
   ```

5. **Connect and Test**:
   - Connect to the host
   - You should see a welcome message
   - Test notifications by running:
   ```bash
   python3 ~/.termius_higherself/scripts/termius_ssh_notifier.py test
   ```

## 📱 Mobile Setup (iPhone/iPad)

If you want notifications on your mobile device:

1. **Enable SSH on your Mac** (if not already enabled):
   ```bash
   sudo systemctl enable ssh  # Linux
   # OR
   sudo launchctl load -w /System/Library/LaunchDaemons/ssh.plist  # macOS
   ```

2. **Get your Mac's IP address**:
   ```bash
   ifconfig | grep "inet " | grep -v 127.0.0.1
   ```

3. **In Termius mobile app**:
   - Use your Mac's IP address instead of `localhost`
   - Same SSH key and settings as above

## 🔔 How Notifications Work

### Automatic Notifications

Once connected, you'll receive notifications for:

- ✅ **Build Success**: When GitHub Actions workflows complete successfully
- ❌ **Build Failure**: When builds fail with error details
- 🚀 **Deployments**: When code is deployed to staging/production
- 🔒 **Security Scans**: Results from vulnerability scans
- ⚠️ **Warnings**: Any issues during CI/CD process

### Notification Format

```
══════════════════════════════════════════════════════════════
🔔 HigherSelf Network Server Notification
══════════════════════════════════════════════════════════════
✅ GitHub Actions: Enhanced CI/CD Pipeline
📊 Status: SUCCESS
🌿 Branch: main
📝 Commit: abc12345
👤 Actor: Utak-West
🔗 Details: https://github.com/Utak-West/The-HigherSelf-Network-Server/actions/runs/123456
Time: 14:30:25
══════════════════════════════════════════════════════════════
```

## 🧪 Testing Your Setup

### 1. Test SSH Notifications

```bash
# Send test notification
python3 ~/.termius_higherself/scripts/termius_ssh_notifier.py test

# Send custom notification
python3 ~/.termius_higherself/scripts/termius_ssh_notifier.py send \
  --message "Hello from HigherSelf!" \
  --type success

# List active sessions
python3 ~/.termius_higherself/scripts/termius_ssh_notifier.py list
```

### 2. Test GitHub Actions Integration

1. **Make a small change** to your repository
2. **Push to GitHub** to trigger the workflow
3. **Watch your Termius terminal** for real-time notifications

### 3. Test API Endpoints

```bash
# Start the server (in another terminal)
python3 main.py

# Test the webhook endpoint
curl -X POST http://localhost:8000/api/termius/test/notification

# Check active sessions
curl http://localhost:8000/api/termius/sessions
```

## 🔧 Advanced Configuration

### Multiple Environments

You can set up different notification profiles for different environments:

```bash
# Register development session
python3 ~/.termius_higherself/scripts/termius_ssh_notifier.py register \
  --host localhost \
  --username utakwest \
  --key-file ~/.ssh/termius_higherself_notifications

# Register production session (if you have a production server)
python3 ~/.termius_higherself/scripts/termius_ssh_notifier.py register \
  --host your-production-server.com \
  --username ubuntu \
  --key-file ~/.ssh/your-production-key
```

### Custom Notification Types

```bash
# Success notification (green)
python3 ~/.termius_higherself/scripts/termius_ssh_notifier.py send \
  --message "Deployment successful!" \
  --type success

# Error notification (red)
python3 ~/.termius_higherself/scripts/termius_ssh_notifier.py send \
  --message "Build failed!" \
  --type failure

# Warning notification (yellow)
python3 ~/.termius_higherself/scripts/termius_ssh_notifier.py send \
  --message "Security scan found issues" \
  --type warning
```

## 🛠 Troubleshooting

### Common Issues

1. **"Permission denied" when connecting**:
   ```bash
   # Check SSH key permissions
   chmod 600 ~/.ssh/termius_higherself_notifications
   chmod 700 ~/.ssh/
   
   # Verify key is in authorized_keys
   cat ~/.ssh/authorized_keys | grep termius-higherself-notifications
   ```

2. **No notifications received**:
   ```bash
   # Test SSH connection manually
   ssh -i ~/.ssh/termius_higherself_notifications localhost
   
   # Check if SSH service is running
   sudo systemctl status ssh  # Linux
   sudo launchctl list | grep ssh  # macOS
   ```

3. **Script not found errors**:
   ```bash
   # Re-run the connection setup
   ./scripts/termius/connect_termius_account.sh
   
   # Check file permissions
   ls -la ~/.termius_higherself/scripts/
   ```

4. **Mobile app can't connect**:
   ```bash
   # Enable SSH on macOS
   sudo systemctl enable ssh
   
   # Check firewall settings
   sudo ufw status  # Linux
   # System Preferences > Security & Privacy > Firewall (macOS)
   ```

### Debug Commands

```bash
# Check active SSH sessions
who

# Test notification system
python3 ~/.termius_higherself/scripts/termius_ssh_notifier.py test

# View notification logs
tail -f ~/.termius_higherself/logs/notifications.log

# Check SSH connection
ssh -v localhost
```

## 🎯 What Happens Next

Once you complete this setup:

1. **Every GitHub push** will trigger notifications in your Termius terminals
2. **Build status changes** will appear in real-time
3. **Deployment events** will be immediately visible
4. **Security alerts** will notify you instantly
5. **Team members** can set up the same system for collaboration

## 📞 Need Help?

If you encounter issues:

1. **Check the logs**: `~/.termius_higherself/logs/`
2. **Run diagnostics**: `./scripts/termius/connect_termius_account.sh`
3. **Test manually**: Use the test commands above
4. **Review the full guide**: `docs/TERMIUS_INTEGRATION_GUIDE.md`

---

**🎉 You're all set!** Your Termius app is now connected to receive real-time notifications from the HigherSelf Network Server. Every time you push code or trigger a workflow, you'll get beautiful, instant notifications directly in your terminal.
