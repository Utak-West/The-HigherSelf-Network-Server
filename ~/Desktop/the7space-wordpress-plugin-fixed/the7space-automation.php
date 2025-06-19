<?php
/**
 * Plugin Name: The 7 Space Automation
 * Plugin URI: https://the7space.com
 * Description: Integration plugin for The 7 Space Art Gallery & Wellness Center with HigherSelf Network Server automation platform.
 * Version: 1.0.1
 * Author: The HigherSelf Network
 * Author URI: https://higherself.network
 * License: GPL v2 or later
 * License URI: https://www.gnu.org/licenses/gpl-2.0.html
 * Text Domain: the7space-automation
 * Domain Path: /languages
 * Requires at least: 5.0
 * Tested up to: 6.4
 * Requires PHP: 7.4
 * Network: false
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
        echo '<div class="notice notice-error"><p><strong>The 7 Space Automation:</strong> This plugin requires WordPress 5.0 or higher. You are running WordPress ' . get_bloginfo('version') . '</p></div>';
    });
    return;
}

// Define plugin constants
define('THE7SPACE_PLUGIN_VERSION', '1.0.1');
define('THE7SPACE_PLUGIN_URL', plugin_dir_url(__FILE__));
define('THE7SPACE_PLUGIN_PATH', plugin_dir_path(__FILE__));
define('THE7SPACE_PLUGIN_BASENAME', plugin_basename(__FILE__));

// Default configuration constants
if (!defined('THE7SPACE_API_URL')) {
    define('THE7SPACE_API_URL', 'http://localhost:8000');
}
if (!defined('THE7SPACE_API_VERSION')) {
    define('THE7SPACE_API_VERSION', 'v1');
}
if (!defined('THE7SPACE_BUSINESS_ENTITY')) {
    define('THE7SPACE_BUSINESS_ENTITY', 'the_7_space');
}

/**
 * Main plugin class
 */
class The7SpaceAutomation {
    
    private static $instance = null;
    private $api_client = null;
    private $errors = array();
    
    public static function get_instance() {
        if (null === self::$instance) {
            self::$instance = new self();
        }
        return self::$instance;
    }
    
    private function __construct() {
        try {
            $this->init();
        } catch (Exception $e) {
            $this->add_error('Plugin initialization failed: ' . $e->getMessage());
            add_action('admin_notices', array($this, 'show_errors'));
        }
    }
    
    private function init() {
        // Load dependencies with error checking
        if (!$this->load_dependencies()) {
            return false;
        }
        
        $this->init_components();
        $this->setup_hooks();
        
        add_action('plugins_loaded', array($this, 'load_textdomain'));
        
        return true;
    }
    
    private function load_dependencies() {
        $required_files = array(
            'includes/class-logger.php',
            'includes/class-api-client.php',
            'includes/class-contact-sync.php'
        );
        
        foreach ($required_files as $file) {
            $file_path = THE7SPACE_PLUGIN_PATH . $file;
            if (!file_exists($file_path)) {
                $this->add_error("Required file missing: {$file}");
                return false;
            }
            
            try {
                require_once $file_path;
            } catch (Exception $e) {
                $this->add_error("Failed to load {$file}: " . $e->getMessage());
                return false;
            }
        }
        
        // Load admin files only in admin
        if (is_admin()) {
            $admin_files = array(
                'admin/class-admin.php',
                'admin/class-settings.php'
            );
            
            foreach ($admin_files as $file) {
                $file_path = THE7SPACE_PLUGIN_PATH . $file;
                if (file_exists($file_path)) {
                    try {
                        require_once $file_path;
                    } catch (Exception $e) {
                        $this->add_error("Failed to load admin file {$file}: " . $e->getMessage());
                    }
                }
            }
        }
        
        return true;
    }
    
    private function init_components() {
        try {
            // Initialize API client
            if (class_exists('The7Space_API_Client')) {
                $this->api_client = new The7Space_API_Client();
            }
            
            // Initialize contact sync
            if (class_exists('The7Space_Contact_Sync') && $this->api_client) {
                new The7Space_Contact_Sync($this->api_client);
            }
            
            // Initialize admin components
            if (is_admin()) {
                if (class_exists('The7Space_Admin')) {
                    new The7Space_Admin();
                }
                if (class_exists('The7Space_Settings')) {
                    new The7Space_Settings();
                }
            }
        } catch (Exception $e) {
            $this->add_error('Component initialization failed: ' . $e->getMessage());
        }
    }
    
    private function setup_hooks() {
        register_activation_hook(__FILE__, array($this, 'activate'));
        register_deactivation_hook(__FILE__, array($this, 'deactivate'));
        
        add_filter('plugin_action_links_' . THE7SPACE_PLUGIN_BASENAME, array($this, 'plugin_action_links'));
        
        // Only add AJAX hooks if in admin
        if (is_admin()) {
            add_action('wp_ajax_the7space_test_connection', array($this, 'ajax_test_connection'));
        }
        
        // Only add REST API hooks if REST API is available
        if (function_exists('register_rest_route')) {
            add_action('rest_api_init', array($this, 'register_rest_routes'));
        }
    }
    
    public function load_textdomain() {
        load_plugin_textdomain(
            'the7space-automation',
            false,
            dirname(THE7SPACE_PLUGIN_BASENAME) . '/languages'
        );
    }
    
    public function activate() {
        try {
            $this->set_default_options();
            $this->log_message('Plugin activated', 'info');
        } catch (Exception $e) {
            $this->add_error('Activation failed: ' . $e->getMessage());
        }
    }
    
    public function deactivate() {
        try {
            $this->log_message('Plugin deactivated', 'info');
        } catch (Exception $e) {
            // Silent fail on deactivation
        }
    }
    
    private function set_default_options() {
        $default_options = array(
            'api_url' => THE7SPACE_API_URL,
            'api_key' => '',
            'webhook_secret' => '',
            'wp_username' => '',
            'wp_app_password' => 'hZKd OEjZ w07V K64h CtVw MFdC',
            'business_entity' => THE7SPACE_BUSINESS_ENTITY,
            'enable_gallery_sync' => true,
            'enable_wellness_sync' => true,
            'enable_contact_sync' => true,
            'enable_debug_logging' => false,
        );
        
        foreach ($default_options as $key => $value) {
            if (get_option('the7space_' . $key) === false) {
                add_option('the7space_' . $key, $value);
            }
        }
    }
    
    public function plugin_action_links($links) {
        $settings_link = '<a href="' . admin_url('options-general.php?page=the7space-settings') . '">' . __('Settings', 'the7space-automation') . '</a>';
        array_unshift($links, $settings_link);
        return $links;
    }
    
    public function ajax_test_connection() {
        // Check nonce
        if (!wp_verify_nonce($_POST['nonce'] ?? '', 'the7space_admin_nonce')) {
            wp_die(__('Security check failed', 'the7space-automation'));
        }
        
        if (!current_user_can('manage_options')) {
            wp_die(__('Insufficient permissions', 'the7space-automation'));
        }
        
        try {
            if ($this->api_client && method_exists($this->api_client, 'test_connection')) {
                $result = $this->api_client->test_connection();
                wp_send_json($result);
            } else {
                wp_send_json(array(
                    'success' => false,
                    'message' => 'API client not available'
                ));
            }
        } catch (Exception $e) {
            wp_send_json(array(
                'success' => false,
                'message' => 'Connection test failed: ' . $e->getMessage()
            ));
        }
    }
    
    public function register_rest_routes() {
        try {
            register_rest_route('the7space/v1', '/webhook', array(
                'methods' => 'POST',
                'callback' => array($this, 'handle_webhook'),
                'permission_callback' => '__return_true',
            ));
            
            register_rest_route('the7space/v1', '/health', array(
                'methods' => 'GET',
                'callback' => array($this, 'health_check'),
                'permission_callback' => '__return_true',
            ));
        } catch (Exception $e) {
            $this->add_error('REST API registration failed: ' . $e->getMessage());
        }
    }
    
    public function handle_webhook($request) {
        try {
            $data = $request->get_json_params();
            $this->log_message('Webhook received: ' . json_encode($data), 'info');
            
            return new WP_REST_Response(array('status' => 'success'), 200);
        } catch (Exception $e) {
            return new WP_REST_Response(array('error' => $e->getMessage()), 500);
        }
    }
    
    public function health_check() {
        $health_data = array(
            'status' => 'healthy',
            'plugin_version' => THE7SPACE_PLUGIN_VERSION,
            'wordpress_version' => get_bloginfo('version'),
            'php_version' => PHP_VERSION,
            'timestamp' => current_time('mysql'),
            'errors' => $this->errors
        );
        
        return new WP_REST_Response($health_data, 200);
    }
    
    public function get_api_client() {
        return $this->api_client;
    }
    
    private function add_error($message) {
        $this->errors[] = $message;
        $this->log_message($message, 'error');
    }
    
    public function show_errors() {
        if (!empty($this->errors)) {
            echo '<div class="notice notice-error">';
            echo '<p><strong>The 7 Space Automation Errors:</strong></p>';
            echo '<ul>';
            foreach ($this->errors as $error) {
                echo '<li>' . esc_html($error) . '</li>';
            }
            echo '</ul>';
            echo '</div>';
        }
    }
    
    private function log_message($message, $level = 'info') {
        if (class_exists('The7Space_Logger')) {
            The7Space_Logger::log($message, $level);
        } else {
            // Fallback logging
            if (defined('WP_DEBUG') && WP_DEBUG && defined('WP_DEBUG_LOG') && WP_DEBUG_LOG) {
                error_log("The7Space Plugin [{$level}]: {$message}");
            }
        }
    }
}

// Safe initialization
function the7space_automation_init() {
    try {
        return The7SpaceAutomation::get_instance();
    } catch (Exception $e) {
        if (defined('WP_DEBUG') && WP_DEBUG) {
            error_log('The7Space Plugin initialization failed: ' . $e->getMessage());
        }
        return false;
    }
}

// Initialize plugin
add_action('plugins_loaded', 'the7space_automation_init');

// Helper function
function the7space() {
    return The7SpaceAutomation::get_instance();
}

// Uninstall hook
register_uninstall_hook(__FILE__, 'the7space_automation_uninstall');

function the7space_automation_uninstall() {
    $options = array(
        'the7space_api_url',
        'the7space_api_key',
        'the7space_webhook_secret',
        'the7space_wp_username',
        'the7space_wp_app_password',
        'the7space_business_entity',
        'the7space_enable_gallery_sync',
        'the7space_enable_wellness_sync',
        'the7space_enable_contact_sync',
        'the7space_enable_debug_logging',
    );
    
    foreach ($options as $option) {
        delete_option($option);
    }
}
