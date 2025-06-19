# The 7 Space Automation Setup Guide

## 🚀 Complete Implementation Guide

This guide provides step-by-step instructions for setting up The 7 Space automation system with your existing HigherSelf Network Server infrastructure.

## Prerequisites

✅ **Already Satisfied:**
- HigherSelf Network Server deployed and operational
- Notion API integration configured
- The 7 Space contact database (191 contacts) ready
- Docker/VM deployment infrastructure in place

## Phase 1: Server Configuration

### Step 1: Generate API Keys

Run these commands on your server to generate secure API keys:

```bash
# Generate The 7 Space API Key
python3 -c "import secrets; print('THE7SPACE_API_KEY=' + secrets.token_urlsafe(32))"

# Generate Webhook Secret
python3 -c "import secrets; print('THE7SPACE_WEBHOOK_SECRET=' + secrets.token_urlsafe(32))"
```

**Example Output:**
```bash
THE7SPACE_API_KEY=Kx9mP2nQ8rS5tU7vW1xY3zA6bC9dE2fG4hI7jK0lM3nO5pQ8rS1tU4vW7xY0zA3b
THE7SPACE_WEBHOOK_SECRET=A1bC3dE5fG7hI9jK1lM3nO5pQ7rS9tU1vW3xY5zA7bC9dE1fG3hI5jK7lM9nO1pQ
```

### Step 2: Update Environment Variables

Add these variables to **ALL** your environment files:

#### **File: .env.demo**
```bash
# The 7 Space WordPress Integration
THE7SPACE_API_KEY=your_generated_api_key_from_step1
THE7SPACE_API_URL=http://localhost:8000
THE7SPACE_WEBHOOK_SECRET=your_generated_webhook_secret_from_step1
THE7SPACE_WORDPRESS_ENABLED=true

# The 7 Space Database IDs (use your existing Notion database IDs)
THE7SPACE_CONTACTS_DB=your_existing_contacts_database_id
THE7SPACE_ARTWORKS_DB=your_artworks_database_id
THE7SPACE_ARTISTS_DB=your_artists_database_id
THE7SPACE_EVENTS_DB=your_events_database_id
THE7SPACE_SERVICES_DB=your_services_database_id
THE7SPACE_APPOINTMENTS_DB=your_appointments_database_id
THE7SPACE_CLASSES_DB=your_classes_database_id
THE7SPACE_SALES_DB=your_sales_database_id
THE7SPACE_MARKETING_DB=your_marketing_database_id
THE7SPACE_ANALYTICS_DB=your_analytics_database_id
```

#### **File: .env.vm.production**
```bash
# The 7 Space WordPress Integration
THE7SPACE_API_KEY=your_generated_api_key_from_step1
THE7SPACE_API_URL=http://localhost:8000  # Change to production URL when ready
THE7SPACE_WEBHOOK_SECRET=your_generated_webhook_secret_from_step1
THE7SPACE_WORDPRESS_ENABLED=true

# Database IDs (same as demo)
THE7SPACE_CONTACTS_DB=your_existing_contacts_database_id
THE7SPACE_ARTWORKS_DB=your_artworks_database_id
THE7SPACE_ARTISTS_DB=your_artists_database_id
THE7SPACE_EVENTS_DB=your_events_database_id
THE7SPACE_SERVICES_DB=your_services_database_id
THE7SPACE_APPOINTMENTS_DB=your_appointments_database_id
THE7SPACE_CLASSES_DB=your_classes_database_id
THE7SPACE_SALES_DB=your_sales_database_id
THE7SPACE_MARKETING_DB=your_marketing_database_id
THE7SPACE_ANALYTICS_DB=your_analytics_database_id
```

### Step 3: Restart HigherSelf Network Server

```bash
# If using Docker Compose
docker-compose down
docker-compose up -d

# If using VM deployment
./deploy-vm.sh

# Verify server is running
curl http://localhost:8000/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0"
}
```

## Phase 2: WordPress Plugin Installation

### Step 1: Upload Plugin Files

1. **Download** the plugin folder: `integrations/the7space/automation/wordpress-plugin/`
2. **Rename** the folder to: `the7space-automation`
3. **Upload** to your WordPress site: `/wp-content/plugins/the7space-automation/`

**File Structure on WordPress:**
```
wp-content/plugins/the7space-automation/
├── the7space-automation.php
├── includes/
│   ├── config.php
│   ├── api-client.php
│   ├── gallery-functions.php
│   ├── wellness-functions.php
│   ├── admin-functions.php
│   └── shortcodes.php
├── assets/
│   ├── js/the7space-frontend.js
│   └── css/the7space-styles.css
└── README.md
```

### Step 2: Configure WordPress Plugin

1. **Login** to WordPress admin
2. **Navigate** to: Plugins → Installed Plugins
3. **Activate** "The 7 Space Automation" plugin
4. **Go to** Settings → The 7 Space

**Configuration Settings:**
```
Server URL: http://localhost:8000
API Key: [paste THE7SPACE_API_KEY from Step 1]
```

### Step 3: Test Connection

After saving settings, you should see:
```
✅ Connected to HigherSelf Network Server
```

If you see an error, check:
- Server URL is correct
- API Key matches your environment variable
- HigherSelf Network Server is running

## Phase 3: Feature Configuration

### Enable Gallery Features
```php
// In WordPress admin: Settings → The 7 Space
☑ Enable Gallery Features
☑ Enable Wellness Features  
☑ Enable Analytics
```

### Add Shortcodes to Pages

#### **Gallery Page:**
```
[the7space_gallery limit="12" show_available_only="true"]
```

#### **Booking Page:**
```
[the7space_booking_form services="massage_60,yoga_private,meditation_guided"]
```

#### **Contact Page:**
```
[the7space_contact_form interests="gallery,wellness,events"]
```

#### **Events Page:**
```
[the7space_events limit="6" upcoming_only="true"]
```

## Phase 4: Testing & Validation

### Test 1: API Connection
```bash
# Test from command line
curl -H "Authorization: Bearer YOUR_API_KEY" http://localhost:8000/health
```

### Test 2: Contact Form Submission
1. **Fill out** contact form on WordPress site
2. **Check** Notion contacts database for new entry
3. **Verify** lead scoring is calculated

### Test 3: Appointment Booking
1. **Book** an appointment through WordPress
2. **Check** Notion appointments database
3. **Verify** confirmation email is sent

### Test 4: Gallery Integration
1. **View** gallery page on WordPress
2. **Verify** artworks load from Notion
3. **Test** artwork detail views

## Phase 5: Production Deployment (Future)

### When Ready for Production:

1. **Deploy** production server with domain
2. **Update** environment variable:
   ```bash
   THE7SPACE_API_URL=https://api.the7space.com
   ```
3. **Update** WordPress configuration:
   ```
   Server URL: https://api.the7space.com
   ```
4. **Test** all functionality in production

## Troubleshooting

### Common Issues:

#### ❌ "Connection Failed" Error
**Solution:**
```bash
# Check server is running
curl http://localhost:8000/health

# Check API key in WordPress matches server
grep THE7SPACE_API_KEY .env*

# Restart server
docker-compose restart
```

#### ❌ "Invalid API Key" Error
**Solution:**
1. Regenerate API key using Step 1 commands
2. Update environment variable
3. Update WordPress configuration
4. Restart server

#### ❌ "Database Not Found" Error
**Solution:**
1. Check Notion database IDs in environment variables
2. Verify Notion API token has access to databases
3. Test Notion connection: `python test_notion_connection.py`

#### ❌ WordPress Plugin Not Loading
**Solution:**
1. Check file permissions: `chmod -R 755 wp-content/plugins/the7space-automation/`
2. Verify PHP version: minimum PHP 7.4
3. Check WordPress error logs

### Debug Mode

Enable debug mode for detailed logging:

**WordPress:**
```php
// In wp-config.php
define('WP_DEBUG', true);
define('WP_DEBUG_LOG', true);
```

**Server:**
```bash
# In environment file
DEBUG=true
LOG_LEVEL=DEBUG
```

## Support & Monitoring

### Health Checks
- **Server Health:** `http://localhost:8000/health`
- **WordPress Admin:** Settings → The 7 Space (connection status)
- **Notion Integration:** Check database updates in real-time

### Log Files
- **WordPress:** `/wp-content/debug.log`
- **Server:** `./logs/the7space.log`
- **Docker:** `docker-compose logs the7space-demo`

### Performance Monitoring
- **API Response Times:** Built into WordPress admin
- **Database Sync Status:** Real-time in Notion
- **Error Rates:** Logged and tracked automatically

## Next Steps

Once setup is complete:
1. **Monitor** system for 24-48 hours
2. **Test** all major workflows
3. **Train** staff on new automation features
4. **Plan** production deployment timeline
5. **Consider** additional integrations (email marketing, social media)

## Security Notes

- ✅ API keys are stored securely in environment variables
- ✅ WordPress uses secure HTTPS communication
- ✅ Rate limiting prevents API abuse
- ✅ Input validation prevents injection attacks
- ✅ Webhook signatures verify authentic requests

**Setup Complete!** 🎉

Your The 7 Space automation system is now ready for testing and operation.
