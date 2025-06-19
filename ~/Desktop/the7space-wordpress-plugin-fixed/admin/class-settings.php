<?php
/**
 * The 7 Space Settings Page - Improved with error handling
 */

if (!defined('ABSPATH')) {
    exit;
}

class The7Space_Settings {
    
    public function __construct() {
        add_action('admin_menu', array($this, 'add_settings_page'));
        add_action('admin_init', array($this, 'register_settings'));
    }
    
    public function add_settings_page() {
        add_options_page(
            'The 7 Space Integration',
            'The 7 Space Integration',
            'manage_options',
            'the7space-settings',
            array($this, 'settings_page_html')
        );
    }
    
    public function register_settings() {
        try {
            add_settings_section(
                'the7space_api_settings',
                'API Configuration',
                array($this, 'api_settings_section_callback'),
                'the7space-settings'
            );
            
            $fields = array(
                'the7space_api_url' => 'API URL',
                'the7space_api_key' => 'API Key',
                'the7space_wp_username' => 'WordPress Username',
                'the7space_wp_app_password' => 'Application Password'
            );
            
            foreach ($fields as $field_id => $field_title) {
                add_settings_field(
                    $field_id,
                    $field_title,
                    array($this, $field_id . '_field_callback'),
                    'the7space-settings',
                    'the7space_api_settings'
                );
            }
            
            add_settings_section(
                'the7space_features',
                'Feature Configuration',
                array($this, 'features_section_callback'),
                'the7space-settings'
            );
            
            add_settings_field(
                'the7space_enable_contact_sync',
                'Enable Contact Sync',
                array($this, 'enable_contact_sync_field_callback'),
                'the7space-settings',
                'the7space_features'
            );
            
            add_settings_field(
                'the7space_enable_debug_logging',
                'Enable Debug Logging',
                array($this, 'enable_debug_logging_field_callback'),
                'the7space-settings',
                'the7space_features'
            );
            
            $settings = array(
                'the7space_api_url',
                'the7space_api_key',
                'the7space_wp_username',
                'the7space_wp_app_password',
                'the7space_enable_contact_sync',
                'the7space_enable_debug_logging'
            );
            
            foreach ($settings as $setting) {
                register_setting('the7space_settings', $setting);
            }
        } catch (Exception $e) {
            // Log error but don't break admin
            if (defined('WP_DEBUG') && WP_DEBUG) {
                error_log('The7Space Settings registration failed: ' . $e->getMessage());
            }
        }
    }
    
    public function settings_page_html() {
        if (!current_user_can('manage_options')) {
            return;
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
                        if (response && response.success) {
                            result.html('<p style="color: green;">✅ ' + (response.message || 'Connection successful') + '</p>');
                        } else {
                            result.html('<p style="color: red;">❌ ' + (response.message || 'Connection failed') + '</p>');
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
    
    public function features_section_callback() {
        echo '<p>Enable or disable specific automation features.</p>';
    }
    
    // Field callbacks
    public function the7space_api_url_field_callback() {
        $value = get_option('the7space_api_url', 'http://localhost:8000');
        echo '<input type="url" name="the7space_api_url" value="' . esc_attr($value) . '" class="regular-text" />';
        echo '<p class="description">The URL of your HigherSelf Network Server</p>';
    }
    
    public function the7space_api_key_field_callback() {
        $value = get_option('the7space_api_key', '');
        echo '<input type="password" name="the7space_api_key" value="' . esc_attr($value) . '" class="regular-text" />';
        echo '<p class="description">API key generated from HigherSelf Network Server</p>';
    }
    
    public function the7space_wp_username_field_callback() {
        $value = get_option('the7space_wp_username', '');
        echo '<input type="text" name="the7space_wp_username" value="' . esc_attr($value) . '" class="regular-text" />';
        echo '<p class="description">Your WordPress admin username</p>';
    }
    
    public function the7space_wp_app_password_field_callback() {
        $value = get_option('the7space_wp_app_password', 'hZKd OEjZ w07V K64h CtVw MFdC');
        echo '<input type="password" name="the7space_wp_app_password" value="' . esc_attr($value) . '" class="regular-text" readonly />';
        echo '<p class="description">WordPress Application Password (pre-configured)</p>';
    }
    
    public function enable_contact_sync_field_callback() {
        $value = get_option('the7space_enable_contact_sync', true);
        echo '<input type="checkbox" name="the7space_enable_contact_sync" value="1" ' . checked(1, $value, false) . ' />';
        echo '<label>Enable automatic contact form synchronization</label>';
    }
    
    public function enable_debug_logging_field_callback() {
        $value = get_option('the7space_enable_debug_logging', false);
        echo '<input type="checkbox" name="the7space_enable_debug_logging" value="1" ' . checked(1, $value, false) . ' />';
        echo '<label>Enable debug logging for troubleshooting</label>';
    }
}
