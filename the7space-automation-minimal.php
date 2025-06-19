<?php
/**
 * Plugin Name: The 7 Space Automation (Minimal)
 * Plugin URI: https://the7space.com
 * Description: Minimal integration plugin for The 7 Space Art Gallery & Wellness Center.
 * Version: 1.0.0
 * Author: The HigherSelf Network
 * License: GPL v2 or later
 * Requires at least: 5.0
 * Tested up to: 6.4
 * Requires PHP: 7.4
 */

// Prevent direct access
if (!defined('ABSPATH')) {
    exit;
}

// Check minimum requirements
if (version_compare(PHP_VERSION, '7.4', '<')) {
    add_action('admin_notices', function() {
        echo '<div class="notice notice-error"><p><strong>The 7 Space Automation:</strong> This plugin requires PHP 7.4 or higher. You are running PHP ' . PHP_VERSION . '</p></div>';
    });
    return;
}

if (version_compare(get_bloginfo('version'), '5.0', '<')) {
    add_action('admin_notices', function() {
        echo '<div class="notice notice-error"><p><strong>The 7 Space Automation:</strong> This plugin requires WordPress 5.0 or higher.</p></div>';
    });
    return;
}

/**
 * Main plugin class
 */
class The7SpaceAutomationMinimal {
    
    private static $instance = null;
    
    public static function get_instance() {
        if (null === self::$instance) {
            self::$instance = new self();
        }
        return self::$instance;
    }
    
    private function __construct() {
        $this->init();
    }
    
    private function init() {
        // Plugin activation
        register_activation_hook(__FILE__, array($this, 'activate'));
        register_deactivation_hook(__FILE__, 'flush_rewrite_rules');
        
        // Admin hooks
        add_action('admin_menu', array($this, 'add_admin_menu'));
        add_action('admin_init', array($this, 'register_settings'));
        add_action('admin_notices', array($this, 'admin_notices'));
        
        // Contact form hooks (only if plugins exist)
        add_action('init', array($this, 'init_contact_hooks'));
        
        // REST API
        add_action('rest_api_init', array($this, 'register_rest_routes'));
    }
    
    public function activate() {
        // Set default options
        $defaults = array(
            'the7space_api_url' => 'http://localhost:8000',
            'the7space_api_key' => '',
            'the7space_wp_username' => '',
            'the7space_wp_app_password' => 'hZKd OEjZ w07V K64h CtVw MFdC',
            'the7space_enable_contact_sync' => true,
            'the7space_enable_debug_logging' => false
        );
        
        foreach ($defaults as $key => $value) {
            if (get_option($key) === false) {
                add_option($key, $value);
            }
        }
        
        flush_rewrite_rules();
    }
    
    public function add_admin_menu() {
        add_options_page(
            'The 7 Space Integration',
            'The 7 Space Integration',
            'manage_options',
            'the7space-settings',
            array($this, 'settings_page')
        );
    }
    
    public function register_settings() {
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
    }
    
    public function settings_page() {
        if (!current_user_can('manage_options')) {
            return;
        }
        ?>
        <div class="wrap">
            <h1>The 7 Space Integration Settings</h1>
            
            <div style="margin: 20px 0; padding: 15px; background: #f0f8ff; border-left: 4px solid #0073aa;">
                <h3>🔑 WordPress Application Password</h3>
                <p><strong>Your Application Password:</strong> <code>hZKd OEjZ w07V K64h CtVw MFdC</code></p>
                <p><em>This password is pre-configured for The 7 Space automation.</em></p>
            </div>
            
            <form method="post" action="options.php">
                <?php settings_fields('the7space_settings'); ?>
                
                <table class="form-table">
                    <tr>
                        <th scope="row">API URL</th>
                        <td>
                            <input type="url" name="the7space_api_url" value="<?php echo esc_attr(get_option('the7space_api_url', 'http://localhost:8000')); ?>" class="regular-text" />
                            <p class="description">The URL of your HigherSelf Network Server</p>
                        </td>
                    </tr>
                    <tr>
                        <th scope="row">API Key</th>
                        <td>
                            <input type="password" name="the7space_api_key" value="<?php echo esc_attr(get_option('the7space_api_key', '')); ?>" class="regular-text" />
                            <p class="description">API key from HigherSelf Network Server</p>
                        </td>
                    </tr>
                    <tr>
                        <th scope="row">WordPress Username</th>
                        <td>
                            <input type="text" name="the7space_wp_username" value="<?php echo esc_attr(get_option('the7space_wp_username', '')); ?>" class="regular-text" />
                            <p class="description">Your WordPress admin username</p>
                        </td>
                    </tr>
                    <tr>
                        <th scope="row">Application Password</th>
                        <td>
                            <input type="password" name="the7space_wp_app_password" value="<?php echo esc_attr(get_option('the7space_wp_app_password', 'hZKd OEjZ w07V K64h CtVw MFdC')); ?>" class="regular-text" readonly />
                            <p class="description">WordPress Application Password (pre-configured)</p>
                        </td>
                    </tr>
                    <tr>
                        <th scope="row">Enable Contact Sync</th>
                        <td>
                            <input type="checkbox" name="the7space_enable_contact_sync" value="1" <?php checked(1, get_option('the7space_enable_contact_sync', true)); ?> />
                            <label>Enable automatic contact form synchronization</label>
                        </td>
                    </tr>
                    <tr>
                        <th scope="row">Enable Debug Logging</th>
                        <td>
                            <input type="checkbox" name="the7space_enable_debug_logging" value="1" <?php checked(1, get_option('the7space_enable_debug_logging', false)); ?> />
                            <label>Enable debug logging for troubleshooting</label>
                        </td>
                    </tr>
                </table>
                
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
                var apiUrl = $('input[name="the7space_api_url"]').val();
                
                button.prop('disabled', true).text('Testing...');
                result.html('<p>Testing connection to ' + apiUrl + '...</p>');
                
                // Simple connection test
                $.ajax({
                    url: apiUrl + '/health',
                    type: 'GET',
                    timeout: 10000,
                    success: function(response) {
                        result.html('<p style="color: green;">✅ Connection successful! Server is responding.</p>');
                    },
                    error: function(xhr, status, error) {
                        if (status === 'timeout') {
                            result.html('<p style="color: orange;">⚠️ Connection timeout. Server may not be running yet.</p>');
                        } else {
                            result.html('<p style="color: red;">❌ Connection failed: ' + error + '</p>');
                        }
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
    
    public function admin_notices() {
        $api_url = get_option('the7space_api_url', '');
        $api_key = get_option('the7space_api_key', '');
        
        if (empty($api_url) || empty($api_key)) {
            echo '<div class="notice notice-warning is-dismissible">';
            echo '<p><strong>The 7 Space Integration:</strong> Please configure your API settings in ';
            echo '<a href="' . admin_url('options-general.php?page=the7space-settings') . '">Settings → The 7 Space Integration</a>';
            echo '</p>';
            echo '</div>';
        }
    }
    
    public function init_contact_hooks() {
        // Contact Form 7 integration
        if (function_exists('wpcf7_get_current_contact_form')) {
            add_action('wpcf7_mail_sent', array($this, 'handle_cf7_submission'));
        }
        
        // Gravity Forms integration
        if (class_exists('GFForms')) {
            add_action('gform_after_submission', array($this, 'handle_gravity_form_submission'), 10, 2);
        }
    }
    
    public function handle_cf7_submission($contact_form) {
        if (!get_option('the7space_enable_contact_sync', true)) {
            return;
        }
        
        if (class_exists('WPCF7_Submission')) {
            $submission = WPCF7_Submission::get_instance();
            if ($submission) {
                $posted_data = $submission->get_posted_data();
                $this->process_contact_submission($posted_data, 'contact_form_7');
            }
        }
    }
    
    public function handle_gravity_form_submission($entry, $form) {
        if (!get_option('the7space_enable_contact_sync', true)) {
            return;
        }
        
        $this->process_contact_submission($entry, 'gravity_forms');
    }
    
    private function process_contact_submission($data, $form_type) {
        $contact_data = array(
            'business_entity' => 'the_7_space',
            'lead_source' => 'website_contact_form',
            'form_type' => $form_type,
            'submission_time' => current_time('mysql')
        );
        
        // Extract common fields
        $field_mapping = array(
            'name' => array('your-name', 'name', 'full_name'),
            'email' => array('your-email', 'email', 'email_address'),
            'phone' => array('your-phone', 'phone', 'phone_number'),
            'message' => array('your-message', 'message', 'comments')
        );
        
        foreach ($field_mapping as $standard_field => $possible_names) {
            foreach ($possible_names as $field_name) {
                if (isset($data[$field_name]) && !empty($data[$field_name])) {
                    $contact_data[$standard_field] = sanitize_text_field($data[$field_name]);
                    break;
                }
            }
        }
        
        // Only proceed if we have an email
        if (empty($contact_data['email'])) {
            return;
        }
        
        // Send to API
        $this->send_contact_to_api($contact_data);
    }
    
    private function send_contact_to_api($contact_data) {
        $api_url = get_option('the7space_api_url', '');
        $api_key = get_option('the7space_api_key', '');
        
        if (empty($api_url)) {
            return;
        }
        
        $args = array(
            'method' => 'POST',
            'timeout' => 30,
            'headers' => array(
                'Content-Type' => 'application/json',
                'User-Agent' => 'The7Space-WordPress-Plugin/1.0.0'
            ),
            'body' => json_encode($contact_data),
            'sslverify' => false
        );
        
        if (!empty($api_key)) {
            $args['headers']['Authorization'] = 'Bearer ' . $api_key;
        }
        
        $response = wp_remote_post($api_url . '/api/the7space/contacts', $args);
        
        // Log result if debug logging is enabled
        if (get_option('the7space_enable_debug_logging', false)) {
            $status = is_wp_error($response) ? 'ERROR' : wp_remote_retrieve_response_code($response);
            $message = is_wp_error($response) ? $response->get_error_message() : 'Contact submitted';
            error_log("The7Space Contact Sync [{$status}]: {$message}");
        }
    }
    
    public function register_rest_routes() {
        register_rest_route('the7space/v1', '/health', array(
            'methods' => 'GET',
            'callback' => array($this, 'health_check'),
            'permission_callback' => '__return_true',
        ));
        
        register_rest_route('the7space/v1', '/webhook', array(
            'methods' => 'POST',
            'callback' => array($this, 'handle_webhook'),
            'permission_callback' => '__return_true',
        ));
    }
    
    public function health_check() {
        return new WP_REST_Response(array(
            'status' => 'healthy',
            'plugin' => 'The 7 Space Automation',
            'version' => '1.0.0',
            'wordpress_version' => get_bloginfo('version'),
            'php_version' => PHP_VERSION,
            'timestamp' => current_time('mysql')
        ), 200);
    }
    
    public function handle_webhook($request) {
        $data = $request->get_json_params();
        
        if (get_option('the7space_enable_debug_logging', false)) {
            error_log('The7Space Webhook received: ' . json_encode($data));
        }
        
        return new WP_REST_Response(array('status' => 'success'), 200);
    }
}

// Initialize plugin
add_action('plugins_loaded', function() {
    The7SpaceAutomationMinimal::get_instance();
});

// Uninstall hook
register_uninstall_hook(__FILE__, function() {
    $options = array(
        'the7space_api_url',
        'the7space_api_key',
        'the7space_wp_username',
        'the7space_wp_app_password',
        'the7space_enable_contact_sync',
        'the7space_enable_debug_logging'
    );
    
    foreach ($options as $option) {
        delete_option($option);
    }
});
