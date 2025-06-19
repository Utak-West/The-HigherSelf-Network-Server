# The 7 Space WordPress Integration Setup Guide

## ✅ **Current Status: Server Running Successfully**

Your automation server is running and ready for WordPress integration!

- **Server URL**: `http://localhost:8000` (for local testing)
- **API Key**: `the7space_automation_api_key_2024`
- **Status**: All integration tests passed ✅

---

## 🔧 **WordPress Configuration Steps**

### **Step 1: Access WordPress Admin**
1. Go to: https://the7space.com/wp-admin
2. Login with: `utak@the7space.com`
3. Use your WordPress password

### **Step 2: Configure Plugin Settings**
1. Navigate to: **Settings → The 7 Space Integration**
2. Enter these settings:

```
API URL: http://YOUR_SERVER_IP:8000
API Key: the7space_automation_api_key_2024
Webhook Secret: [leave blank for now]
WordPress Username: utak@the7space.com
WordPress App Password: hZKd OEjZ w07V K64h CtVw MFdC

✅ Enable Contact Sync
✅ Enable Gallery Sync  
✅ Enable Wellness Sync
✅ Enable Analytics
```

### **Step 3: Update Server URL for Production**

**For SiteGround hosting, you need to:**

1. **Get your server's public IP** or use a service like ngrok for testing:
   ```bash
   # Option 1: Use ngrok for testing (recommended)
   ngrok http 8000
   # This gives you a public URL like: https://abc123.ngrok.io
   
   # Option 2: Find your public IP
   curl ifconfig.me
   ```

2. **Update WordPress plugin settings** with the public URL

---

## 🧪 **Testing Steps**

### **Step 1: Test Contact Form Integration**

1. **Go to your website**: https://the7space.com
2. **Find a contact form** (Contact Form 7 or Gravity Forms)
3. **Submit a test contact** with:
   - Name: Test Integration
   - Email: test@example.com
   - Message: Testing WordPress automation integration

### **Step 2: Verify Server Receives Data**

Check your server terminal for output like:
```
📧 New contact received from Test Integration (test@example.com)
   Form Type: contact_form_7
   Message: Testing WordPress automation integration...
   Contact Type: general_inquiry
```

---

## 🚀 **Available Functionality**

Once integrated, your system will automatically:

### **Contact Form Automation**
- ✅ Capture all contact form submissions
- ✅ Classify contacts by type (gallery, wellness, general)
- ✅ Store in automation database
- ✅ Trigger follow-up workflows

### **Gallery Integration**
- ✅ Sync artwork information
- ✅ Track gallery inquiries
- ✅ Automate artist communications

### **Wellness Center Integration**
- ✅ Process appointment requests
- ✅ Sync service bookings
- ✅ Automate wellness program notifications

### **Analytics & Reporting**
- ✅ Track website engagement
- ✅ Monitor form conversion rates
- ✅ Generate contact reports

---

## 🔍 **Verification Checklist**

- [ ] WordPress plugin activated
- [ ] Plugin settings configured
- [ ] Server URL accessible from WordPress
- [ ] API key working
- [ ] Contact form test successful
- [ ] Server logs showing received data

---

## 🆘 **Troubleshooting**

### **Plugin Not Connecting**
1. Check server is running: `curl http://localhost:8000/health`
2. Verify API key in WordPress settings
3. Check server logs for connection attempts

### **Contact Forms Not Working**
1. Ensure Contact Form 7 or Gravity Forms is installed
2. Check plugin hooks are properly configured
3. Test with debug mode enabled

### **Server Not Accessible**
1. Use ngrok for public access: `ngrok http 8000`
2. Update WordPress settings with ngrok URL
3. Check firewall settings

---

## 📞 **Next Steps**

1. **Configure WordPress settings** as outlined above
2. **Test contact form integration** 
3. **Verify automation workflows** are triggered
4. **Monitor server logs** for successful data processing

**Ready to proceed with WordPress configuration?**
