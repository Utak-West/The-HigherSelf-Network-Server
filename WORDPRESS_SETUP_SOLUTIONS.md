# WordPress Integration Setup Solutions

## 🚨 **Current Issue: Cannot Access Plugin Settings**

You're unable to access the WordPress plugin settings page. Here are **3 solutions** in order of ease:

---

## 🔧 **Solution 1: Upload Simple Plugin (Recommended)**

### **Step 1: Upload the Simple Plugin**

1. **Download this file**: `the7space-simple-integration.php` (from your current directory)
2. **Upload to WordPress**:
   - Via FTP: Upload to `/wp-content/plugins/`
   - Via WordPress Admin: Plugins → Add New → Upload Plugin

### **Step 2: Activate Plugin**

1. Go to: **Plugins → Installed Plugins**
2. Find: **"The 7 Space Simple Integration"**
3. Click: **"Activate"**

### **Step 3: Configure Settings**

1. Go to: **Settings → The 7 Space** (should now appear)
2. Update **API URL** with your ngrok URL
3. Keep **API Key**: `the7space_automation_api_key_2024`
4. Check **"Enable Integration"**
5. Click **"Save Changes"**

---

## 🔧 **Solution 2: Direct Database Configuration**

If the plugin still doesn't work, configure directly:

### **Step 1: Upload Configuration Script**

1. **Download**: `wordpress-direct-config.php` (from your current directory)
2. **Edit the file**: Update `$api_url = 'https://your-ngrok-url.ngrok.io';`
3. **Upload to WordPress root** (same folder as wp-config.php)

### **Step 2: Run Configuration**

1. **Visit**: https://the7space.com/wordpress-direct-config.php
2. **Follow the instructions** on the page
3. **Delete the file** after running it

---

## 🔧 **Solution 3: Manual WordPress Functions**

Add this code to your theme's `functions.php`:

```php
// Add to wp-content/themes/your-theme/functions.php

// The 7 Space Integration
add_action('wpcf7_mail_sent', 'the7space_manual_integration');
function the7space_manual_integration($contact_form) {
    $submission = WPCF7_Submission::get_instance();
    if (!$submission) return;
    
    $posted_data = $submission->get_posted_data();
    
    $contact_data = array(
        'business_entity' => 'the_7_space',
        'lead_source' => 'website_contact_form',
        'form_type' => 'contact_form_7',
        'submission_time' => current_time('c'),
        'name' => isset($posted_data['your-name']) ? $posted_data['your-name'] : '',
        'email' => isset($posted_data['your-email']) ? $posted_data['your-email'] : '',
        'phone' => isset($posted_data['your-phone']) ? $posted_data['your-phone'] : '',
        'message' => isset($posted_data['your-message']) ? $posted_data['your-message'] : '',
        'contact_type' => 'general_inquiry'
    );
    
    // UPDATE THIS URL WITH YOUR NGROK URL
    $api_url = 'https://your-ngrok-url.ngrok.io';
    
    wp_remote_post($api_url . '/api/the7space/contacts', array(
        'body' => json_encode($contact_data),
        'headers' => array(
            'Content-Type' => 'application/json',
            'Authorization' => 'Bearer the7space_automation_api_key_2024'
        ),
        'timeout' => 15
    ));
}
```

---

## 🌐 **Getting Your Public URL (Required for All Solutions)**

### **Option A: Using ngrok (Recommended)**

1. **Install ngrok**:
   ```bash
   brew install ngrok
   ```

2. **Start ngrok** (in a new terminal):
   ```bash
   ngrok http 8000
   ```

3. **Copy the HTTPS URL** (e.g., `https://abc123.ngrok.io`)

### **Option B: Using Your Router**

1. **Configure port forwarding** on your router (port 8000)
2. **Get your public IP**: `curl ifconfig.me`
3. **Use**: `http://YOUR_PUBLIC_IP:8000`

---

## 🧪 **Testing Steps**

### **After Configuration:**

1. **Visit**: https://the7space.com
2. **Find a contact form** (usually on Contact page)
3. **Submit test data**:
   - Name: Integration Test
   - Email: test@example.com
   - Message: Testing WordPress integration

### **Verify Success:**

Check your server terminal for:
```
📧 New contact received from Integration Test (test@example.com)
   Form Type: contact_form_7
   Message: Testing WordPress integration...
```

---

## 🆘 **Troubleshooting**

### **Plugin Not Appearing**
- Check file permissions (755 for folders, 644 for files)
- Verify PHP syntax (no errors in error logs)
- Try deactivating other plugins temporarily

### **Settings Page Not Working**
- Use Solution 2 (Direct Database Configuration)
- Check WordPress user permissions (must be Administrator)

### **Contact Forms Not Triggering**
- Verify Contact Form 7 is installed and active
- Check WordPress error logs
- Test with Solution 3 (Manual Functions)

---

## 📋 **Quick Action Plan**

**Right Now:**

1. **Start ngrok**: `ngrok http 8000`
2. **Copy the HTTPS URL**
3. **Try Solution 1** (Upload Simple Plugin)
4. **If that fails, try Solution 2** (Direct Database Config)
5. **Test with a contact form submission**

**Which solution would you like to try first?**
