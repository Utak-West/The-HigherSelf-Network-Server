<?php
/**
 * Direct WordPress Configuration for The 7 Space Integration
 * 
 * Upload this file to your WordPress root directory and run it once
 * to configure the integration settings directly in the database.
 */

// WordPress configuration
require_once('wp-config.php');
require_once('wp-includes/wp-db.php');

// Your ngrok URL (update this with your actual ngrok URL)
$api_url = 'https://your-ngrok-url.ngrok.io'; // UPDATE THIS!

// Configuration settings
$settings = array(
    'the7space_api_url' => $api_url,
    'the7space_api_key' => 'the7space_automation_api_key_2024',
    'the7space_webhook_secret' => '',
    'the7space_wp_username' => 'utak@the7space.com',
    'the7space_wp_app_password' => 'hZKd OEjZ w07V K64h CtVw MFdC',
    'the7space_enable_contact_sync' => '1',
    'the7space_enable_gallery_sync' => '1',
    'the7space_enable_wellness_sync' => '1',
    'the7space_enable_analytics' => '1',
    'the7space_debug_mode' => '1'
);

echo "<h1>The 7 Space WordPress Integration Setup</h1>\n";
echo "<p>Configuring WordPress database settings...</p>\n";

// Update WordPress options
foreach ($settings as $option_name => $option_value) {
    $result = update_option($option_name, $option_value);
    if ($result) {
        echo "<p>✅ Set {$option_name}: {$option_value}</p>\n";
    } else {
        // Check if option already exists with same value
        $existing = get_option($option_name);
        if ($existing === $option_value) {
            echo "<p>✅ {$option_name} already set correctly</p>\n";
        } else {
            echo "<p>❌ Failed to set {$option_name}</p>\n";
        }
    }
}

// Test the API connection
echo "<h2>Testing API Connection</h2>\n";

$test_url = $api_url . '/health';
$response = wp_remote_get($test_url, array(
    'timeout' => 10,
    'headers' => array(
        'Authorization' => 'Bearer the7space_automation_api_key_2024'
    )
));

if (is_wp_error($response)) {
    echo "<p>❌ API Connection Failed: " . $response->get_error_message() . "</p>\n";
} else {
    $status_code = wp_remote_retrieve_response_code($response);
    if ($status_code === 200) {
        echo "<p>✅ API Connection Successful!</p>\n";
        $body = wp_remote_retrieve_body($response);
        $data = json_decode($body, true);
        if ($data) {
            echo "<p>Server Status: " . $data['status'] . "</p>\n";
            echo "<p>Business Entity: " . $data['business_entity'] . "</p>\n";
        }
    } else {
        echo "<p>❌ API Connection Failed: HTTP {$status_code}</p>\n";
    }
}

// Add contact form hooks directly
echo "<h2>Setting up Contact Form Hooks</h2>\n";

// Hook for Contact Form 7
if (function_exists('wpcf7_add_form_tag')) {
    echo "<p>✅ Contact Form 7 detected</p>\n";
    
    // Add action to handle form submissions
    add_action('wpcf7_mail_sent', function($contact_form) {
        $submission = WPCF7_Submission::get_instance();
        if ($submission) {
            $posted_data = $submission->get_posted_data();
            
            // Prepare data for API
            $contact_data = array(
                'business_entity' => 'the_7_space',
                'lead_source' => 'website_contact_form',
                'form_type' => 'contact_form_7',
                'submission_time' => current_time('c'),
                'name' => isset($posted_data['your-name']) ? $posted_data['your-name'] : '',
                'email' => isset($posted_data['your-email']) ? $posted_data['your-email'] : '',
                'phone' => isset($posted_data['your-phone']) ? $posted_data['your-phone'] : '',
                'message' => isset($posted_data['your-message']) ? $posted_data['your-message'] : '',
                'subject' => isset($posted_data['your-subject']) ? $posted_data['your-subject'] : '',
                'contact_type' => 'general_inquiry'
            );
            
            // Send to API
            $api_url = get_option('the7space_api_url');
            $api_key = get_option('the7space_api_key');
            
            if ($api_url && $api_key) {
                $response = wp_remote_post($api_url . '/api/the7space/contacts', array(
                    'body' => json_encode($contact_data),
                    'headers' => array(
                        'Content-Type' => 'application/json',
                        'Authorization' => 'Bearer ' . $api_key
                    ),
                    'timeout' => 15
                ));
                
                if (!is_wp_error($response)) {
                    error_log('The7Space: Contact submitted successfully');
                } else {
                    error_log('The7Space: Contact submission failed - ' . $response->get_error_message());
                }
            }
        }
    });
    
    echo "<p>✅ Contact Form 7 hook installed</p>\n";
} else {
    echo "<p>⚠️ Contact Form 7 not detected</p>\n";
}

echo "<h2>Configuration Complete!</h2>\n";
echo "<p><strong>Next Steps:</strong></p>\n";
echo "<ol>\n";
echo "<li>Update the \$api_url variable in this file with your ngrok URL</li>\n";
echo "<li>Test a contact form submission on your website</li>\n";
echo "<li>Check your server logs for contact submissions</li>\n";
echo "<li>Delete this file after testing</li>\n";
echo "</ol>\n";

echo "<p><strong>Important:</strong> Delete this file after running it for security!</p>\n";
?>
