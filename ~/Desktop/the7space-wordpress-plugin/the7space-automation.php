<?php
/**
 * Plugin Name: The 7 Space Automation
 * Plugin URI: https://the7space.com
 * Description: Integration plugin for The 7 Space Art Gallery & Wellness Center with HigherSelf Network Server automation platform.
 * Version: 1.0.0
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

// Define plugin constants
define('THE7SPACE_PLUGIN_VERSION', '1.0.0');
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
        $this->load_dependencies();
        $this->init_components();
        $this->setup_hooks();
        add_action('plugins_loaded', array($this, 'load_textdomain'));
    }
    
    private function load_dependencies() {
        require_once THE7SPACE_PLUGIN_PATH . 'includes/class-logger.php';
        require_once THE7SPACE_PLUGIN_PATH . 'includes/class-api-client.php';
        require_once THE7SPACE_PLUGIN_PATH . 'includes/class-contact-sync.php';
        
        if (is_admin()) {
            require_once THE7SPACE_PLUGIN_PATH . 'admin/class-admin.php';
            require_once THE7SPACE_PLUGIN_PATH . 'admin/class-settings.php';
        }
    }
    
    private function init_components() {
        $this->api_client = new The7Space_API_Client();
        new The7Space_Contact_Sync($this->api_client);
        
        if (is_admin()) {
            new The7Space_Admin();
            new The7Space_Settings();
        }
    }
    
    private function setup_hooks() {
        register_activation_hook(__FILE__, array($this, 'activate'));
        register_deactivation_hook(__FILE__, array($this, 'deactivate'));
        
        add_filter('plugin_action_links_' . THE7SPACE_PLUGIN_BASENAME, array($this, 'plugin_action_links'));
        add_action('wp_ajax_the7space_test_connection', array($this, 'ajax_test_connection'));
        add_action('rest_api_init', array($this, 'register_rest_routes'));
    }
    
    public function load_textdomain() {
        load_plugin_textdomain(
            'the7space-automation',
            false,
            dirname(THE7SPACE_PLUGIN_BASENAME) . '/languages'
        );
    }
    
    public function activate() {
        $this->set_default_options();
        The7Space_Logger::log('Plugin activated', 'info');
    }
    
    public function deactivate() {
        The7Space_Logger::log('Plugin deactivated', 'info');
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
        check_ajax_referer('the7space_admin_nonce', 'nonce');
        
        if (!current_user_can('manage_options')) {
            wp_die(__('Insufficient permissions', 'the7space-automation'));
        }
        
        $result = $this->api_client->test_connection();
        wp_send_json($result);
    }
    
    public function register_rest_routes() {
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
    }
    
    public function handle_webhook($request) {
        $data = $request->get_json_params();
        The7Space_Logger::log('Webhook received: ' . json_encode($data), 'info');
        
        return new WP_REST_Response(array('status' => 'success'), 200);
    }
    
    public function health_check() {
        $health_data = array(
            'status' => 'healthy',
            'plugin_version' => THE7SPACE_PLUGIN_VERSION,
            'wordpress_version' => get_bloginfo('version'),
            'php_version' => PHP_VERSION,
            'timestamp' => current_time('mysql'),
        );
        
        return new WP_REST_Response($health_data, 200);
    }
    
    public function get_api_client() {
        return $this->api_client;
    }
}

function the7space_automation_init() {
    return The7SpaceAutomation::get_instance();
}

add_action('plugins_loaded', 'the7space_automation_init');

function the7space() {
    return The7SpaceAutomation::get_instance();
}

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
