<?php
/**
 * The 7 Space Settings Page
 * 
 * WordPress admin settings for The 7 Space automation plugin
 */

if (!defined('ABSPATH')) {
    exit;
}

class The7Space_Settings {
    
    public function __construct() {
        add_action('admin_menu', array($this, 'add_settings_page'));
        add_action('admin_init', array($this, 'register_settings'));
    }
    
    /**
     * Add settings page to WordPress admin
     */
    public function add_settings_page() {
        add_options_page(
            'The 7 Space Integration',
            'The 7 Space Integration',
            'manage_options',
            'the7space-settings',
            array($this, 'settings_page_html')
        );
    }
    
    /**
     * Register plugin settings
     */
    public function register_settings() {
        // API Settings Section
        add_settings_section(
            'the7space_api_settings',
            'API Configuration',
            array($this, 'api_settings_section_callback'),
            'the7space-settings'
        );
        
        // API URL
        add_settings_field(
            'the7space_api_url',
            'API URL',
            array($this, 'api_url_field_callback'),
            'the7space-settings',
            'the7space_api_settings'
        );
        
        // API Key
        add_settings_field(
            'the7space_api_key',
            'API Key',
            array($this, 'api_key_field_callback'),
            'the7space-settings',
            'the7space_api_settings'
        );
        
        // Webhook Secret
        add_settings_field(
            'the7space_webhook_secret',
            'Webhook Secret',
            array($this, 'webhook_secret_field_callback'),
            'the7space-settings',
            'the7space_api_settings'
        );
        
        // WordPress Credentials Section
        add_settings_section(
            'the7space_wp_credentials',
            'WordPress Credentials',
            array($this, 'wp_credentials_section_callback'),
            'the7space-settings'
        );
        
        // WordPress Username
        add_settings_field(
            'the7space_wp_username',
            'WordPress Username',
            array($this, 'wp_username_field_callback'),
            'the7space-settings',
            'the7space_wp_credentials'
        );
        
        // WordPress Application Password
        add_settings_field(
            'the7space_wp_app_password',
            'Application Password',
            array($this, 'wp_app_password_field_callback'),
            'the7space-settings',
            'the7space_wp_credentials'
        );
        
        // Feature Settings Section
        add_settings_section(
            'the7space_features',
            'Feature Configuration',
            array($this, 'features_section_callback'),
            'the7space-settings'
        );
        
        // Enable Gallery Sync
        add_settings_field(
            'the7space_enable_gallery_sync',
            'Enable Gallery Sync',
            array($this, 'enable_gallery_sync_field_callback'),
            'the7space-settings',
            'the7space_features'
        );
        
        // Enable Wellness Sync
        add_settings_field(
            'the7space_enable_wellness_sync',
            'Enable Wellness Sync',
            array($this, 'enable_wellness_sync_field_callback'),
            'the7space-settings',
            'the7space_features'
        );
        
        // Enable Contact Sync
        add_settings_field(
            'the7space_enable_contact_sync',
            'Enable Contact Sync',
            array($this, 'enable_contact_sync_field_callback'),
            'the7space-settings',
            'the7space_features'
        );
        
        // Register all settings
        $settings = array(
            'the7space_api_url',
            'the7space_api_key',
            'the7space_webhook_secret',
            'the7space_wp_username',
            'the7space_wp_app_password',
            'the7space_enable_gallery_sync',
            'the7space_enable_wellness_sync',
            'the7space_enable_contact_sync'
        );
        
        foreach ($settings as $setting) {
            register_setting('the7space_settings', $setting);
        }
    }
    
    /**
     * Settings page HTML
     */
    public function settings_page_html() {
        if (!current_user_can('manage_options')) {
            return;
        }
        
        // Handle form submission
        if (isset($_POST['submit'])) {
            // WordPress will handle saving the settings
            echo '<div class="notice notice-success"><p>Settings saved!</p></div>';
        }
        ?>
        <div class="wrap">
            <h1>The 7 Space Integration Settings</h1>
            <p>Configure the integration between your WordPress site and The 7 Space automation platform.</p>
            
            <form method="post" action="options.php">
                <?php
                settings_fields('the7space_settings');
                do_settings_sections('the7space-settings');
                ?>
                
                <div style="margin: 20px 0; padding: 15px; background: #f0f8ff; border-left: 4px solid #0073aa;">
                    <h3>🔑 Your WordPress Application Password</h3>
                    <p><strong>Application Password:</strong> <code>hZKd OEjZ w07V K64h CtVw MFdC</code></p>
                    <p><em>This password has been automatically configured for The 7 Space automation.</em></p>
                </div>
                
                <div style="margin: 20px 0; padding: 15px; background: #f9f9f9; border-left: 4px solid #00a32a;">
                    <h3>🧪 Test Connection</h3>
                    <button type="button" id="test-connection" class="button button-secondary">Test API Connection</button>
                    <div id="connection-result" style="margin-top: 10px;"></div>
                </div>
                
                <?php submit_button(); ?>
            </form>
        </div>
        
        <script>
        jQuery(document).ready(function($) {
            $('#test-connection').click(function() {
                var button = $(this);
                var result = $('#connection-result');
                
                button.prop('disabled', true).text('Testing...');
                result.html('<p>Testing connection...</p>');
                
                $.ajax({
                    url: ajaxurl,
                    type: 'POST',
                    data: {
                        action: 'the7space_test_connection',
                        nonce: '<?php echo wp_create_nonce('the7space_admin_nonce'); ?>'
                    },
                    success: function(response) {
                        if (response.success) {
                            result.html('<p style="color: green;">✅ ' + response.data.message + '</p>');
                        } else {
                            result.html('<p style="color: red;">❌ ' + response.data.message + '</p>');
                        }
                    },
                    error: function() {
                        result.html('<p style="color: red;">❌ Connection test failed</p>');
                    },
                    complete: function() {
                        button.prop('disabled', false).text('Test API Connection');
                    }
                });
            });
        });
        </script>
        <?php
    }
    
    // Section callbacks
    public function api_settings_section_callback() {
        echo '<p>Configure the connection to The 7 Space automation server.</p>';
    }
    
    public function wp_credentials_section_callback() {
        echo '<p>WordPress credentials for API authentication.</p>';
    }
    
    public function features_section_callback() {
        echo '<p>Enable or disable specific automation features.</p>';
    }
    
    // Field callbacks
    public function api_url_field_callback() {
        $value = get_option('the7space_api_url', 'http://localhost:8000');
        echo '<input type="url" name="the7space_api_url" value="' . esc_attr($value) . '" class="regular-text" />';
        echo '<p class="description">The URL of your HigherSelf Network Server (e.g., http://localhost:8000)</p>';
    }
    
    public function api_key_field_callback() {
        $value = get_option('the7space_api_key', '');
        echo '<input type="password" name="the7space_api_key" value="' . esc_attr($value) . '" class="regular-text" />';
        echo '<p class="description">API key generated from HigherSelf Network Server</p>';
    }
    
    public function webhook_secret_field_callback() {
        $value = get_option('the7space_webhook_secret', '');
        echo '<input type="password" name="the7space_webhook_secret" value="' . esc_attr($value) . '" class="regular-text" />';
        echo '<p class="description">Webhook secret for secure communication</p>';
    }
    
    public function wp_username_field_callback() {
        $value = get_option('the7space_wp_username', '');
        echo '<input type="text" name="the7space_wp_username" value="' . esc_attr($value) . '" class="regular-text" />';
        echo '<p class="description">Your WordPress admin username</p>';
    }
    
    public function wp_app_password_field_callback() {
        $value = get_option('the7space_wp_app_password', 'hZKd OEjZ w07V K64h CtVw MFdC');
        echo '<input type="password" name="the7space_wp_app_password" value="' . esc_attr($value) . '" class="regular-text" readonly />';
        echo '<p class="description">WordPress Application Password (pre-configured)</p>';
    }
    
    public function enable_gallery_sync_field_callback() {
        $value = get_option('the7space_enable_gallery_sync', true);
        echo '<input type="checkbox" name="the7space_enable_gallery_sync" value="1" ' . checked(1, $value, false) . ' />';
        echo '<label>Enable automatic gallery content synchronization</label>';
    }
    
    public function enable_wellness_sync_field_callback() {
        $value = get_option('the7space_enable_wellness_sync', true);
        echo '<input type="checkbox" name="the7space_enable_wellness_sync" value="1" ' . checked(1, $value, false) . ' />';
        echo '<label>Enable wellness center appointment synchronization</label>';
    }
    
    public function enable_contact_sync_field_callback() {
        $value = get_option('the7space_enable_contact_sync', true);
        echo '<input type="checkbox" name="the7space_enable_contact_sync" value="1" ' . checked(1, $value, false) . ' />';
        echo '<label>Enable contact form synchronization</label>';
    }
}
