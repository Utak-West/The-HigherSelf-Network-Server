<?php
/**
 * Plugin Name: The 7 Space Simple Integration
 * Plugin URI: https://the7space.com
 * Description: Simple integration plugin for The 7 Space with HigherSelf Network Server
 * Version: 1.0.0
 * Author: The HigherSelf Network
 * License: GPL v2 or later
 */

// Prevent direct access
if (!defined('ABSPATH')) {
    exit;
}

// Plugin activation
register_activation_hook(__FILE__, 'the7space_simple_activate');
function the7space_simple_activate() {
    add_option('the7space_api_url', 'http://localhost:8000');
    add_option('the7space_api_key', 'the7space_automation_api_key_2024');
    add_option('the7space_enabled', '1');
}

// Add admin menu
add_action('admin_menu', 'the7space_simple_admin_menu');
function the7space_simple_admin_menu() {
    add_options_page(
        'The 7 Space Integration',
        'The 7 Space',
        'manage_options',
        'the7space-simple-settings',
        'the7space_simple_settings_page'
    );
}

// Settings page
function the7space_simple_settings_page() {
    if (isset($_POST['submit'])) {
        update_option('the7space_api_url', sanitize_text_field($_POST['api_url']));
        update_option('the7space_api_key', sanitize_text_field($_POST['api_key']));
        update_option('the7space_enabled', isset($_POST['enabled']) ? '1' : '0');
        echo '<div class="notice notice-success"><p>Settings saved!</p></div>';
    }
    
    $api_url = get_option('the7space_api_url', 'http://localhost:8000');
    $api_key = get_option('the7space_api_key', 'the7space_automation_api_key_2024');
    $enabled = get_option('the7space_enabled', '1');
    ?>
    <div class="wrap">
        <h1>The 7 Space Integration Settings</h1>
        <form method="post" action="">
            <table class="form-table">
                <tr>
                    <th scope="row">API URL</th>
                    <td>
                        <input type="url" name="api_url" value="<?php echo esc_attr($api_url); ?>" class="regular-text" />
                        <p class="description">Enter your HigherSelf Network Server URL (e.g., https://abc123.ngrok.io)</p>
                    </td>
                </tr>
                <tr>
                    <th scope="row">API Key</th>
                    <td>
                        <input type="text" name="api_key" value="<?php echo esc_attr($api_key); ?>" class="regular-text" />
                        <p class="description">API key: the7space_automation_api_key_2024</p>
                    </td>
                </tr>
                <tr>
                    <th scope="row">Enable Integration</th>
                    <td>
                        <label>
                            <input type="checkbox" name="enabled" value="1" <?php checked($enabled, '1'); ?> />
                            Enable contact form integration
                        </label>
                    </td>
                </tr>
            </table>
            <?php submit_button(); ?>
        </form>
        
        <h2>Test Connection</h2>
        <p>
            <button type="button" id="test-connection" class="button">Test API Connection</button>
            <span id="test-result"></span>
        </p>
        
        <script>
        document.getElementById('test-connection').addEventListener('click', function() {
            var button = this;
            var result = document.getElementById('test-result');
            
            button.disabled = true;
            result.innerHTML = 'Testing...';
            
            var apiUrl = document.querySelector('input[name="api_url"]').value;
            
            fetch(apiUrl + '/health')
                .then(response => response.json())
                .then(data => {
                    result.innerHTML = '<span style="color: green;">✅ Connection successful! Status: ' + data.status + '</span>';
                })
                .catch(error => {
                    result.innerHTML = '<span style="color: red;">❌ Connection failed: ' + error.message + '</span>';
                })
                .finally(() => {
                    button.disabled = false;
                });
        });
        </script>
    </div>
    <?php
}

// Contact Form 7 integration
add_action('wpcf7_mail_sent', 'the7space_simple_handle_contact_form');
function the7space_simple_handle_contact_form($contact_form) {
    if (get_option('the7space_enabled') !== '1') {
        return;
    }
    
    $submission = WPCF7_Submission::get_instance();
    if (!$submission) {
        return;
    }
    
    $posted_data = $submission->get_posted_data();
    
    // Prepare contact data
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
    
    if (empty($api_url) || empty($api_key)) {
        error_log('The7Space: API URL or key not configured');
        return;
    }
    
    $response = wp_remote_post($api_url . '/api/the7space/contacts', array(
        'body' => json_encode($contact_data),
        'headers' => array(
            'Content-Type' => 'application/json',
            'Authorization' => 'Bearer ' . $api_key,
            'User-Agent' => 'The7Space-WordPress-Plugin/1.0.0'
        ),
        'timeout' => 15
    ));
    
    if (is_wp_error($response)) {
        error_log('The7Space: API request failed - ' . $response->get_error_message());
    } else {
        $status_code = wp_remote_retrieve_response_code($response);
        if ($status_code === 200) {
            error_log('The7Space: Contact submitted successfully - ' . $contact_data['email']);
        } else {
            error_log('The7Space: API returned status ' . $status_code);
        }
    }
}

// Admin notice if not configured
add_action('admin_notices', 'the7space_simple_admin_notice');
function the7space_simple_admin_notice() {
    $api_url = get_option('the7space_api_url');
    $api_key = get_option('the7space_api_key');
    
    if (empty($api_url) || $api_url === 'http://localhost:8000' || empty($api_key)) {
        echo '<div class="notice notice-warning is-dismissible">';
        echo '<p><strong>The 7 Space Integration:</strong> Please configure your API settings in ';
        echo '<a href="' . admin_url('options-general.php?page=the7space-simple-settings') . '">Settings → The 7 Space</a>';
        echo '</p>';
        echo '</div>';
    }
}
?>
