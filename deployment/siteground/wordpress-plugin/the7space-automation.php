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
    
    /**
     * Plugin instance
     */
    private static $instance = null;
    
    /**
     * API client instance
     */
    private $api_client = null;
    
    /**
     * Webhook handler instance
     */
    private $webhook_handler = null;
    
    /**
     * Get plugin instance
     */
    public static function get_instance() {
        if (null === self::$instance) {
            self::$instance = new self();
        }
        return self::$instance;
    }
    
    /**
     * Constructor
     */
    private function __construct() {
        $this->init();
    }
    
    /**
     * Initialize plugin
     */
    private function init() {
        // Load plugin files
        $this->load_dependencies();
        
        // Initialize components
        $this->init_components();
        
        // Setup hooks
        $this->setup_hooks();
        
        // Load textdomain
        add_action('plugins_loaded', array($this, 'load_textdomain'));
    }
    
    /**
     * Load plugin dependencies
     */
    private function load_dependencies() {
        require_once THE7SPACE_PLUGIN_PATH . 'includes/class-api-client.php';
        require_once THE7SPACE_PLUGIN_PATH . 'includes/class-webhook-handler.php';
        require_once THE7SPACE_PLUGIN_PATH . 'includes/class-contact-sync.php';
        require_once THE7SPACE_PLUGIN_PATH . 'includes/class-gallery-sync.php';
        require_once THE7SPACE_PLUGIN_PATH . 'includes/class-wellness-sync.php';
        require_once THE7SPACE_PLUGIN_PATH . 'includes/class-logger.php';
        
        if (is_admin()) {
            require_once THE7SPACE_PLUGIN_PATH . 'admin/class-admin.php';
            require_once THE7SPACE_PLUGIN_PATH . 'admin/class-settings.php';
        }
        
        require_once THE7SPACE_PLUGIN_PATH . 'public/class-shortcodes.php';
        require_once THE7SPACE_PLUGIN_PATH . 'public/class-frontend.php';
    }
    
    /**
     * Initialize plugin components
     */
    private function init_components() {
        // Initialize API client
        $this->api_client = new The7Space_API_Client();
        
        // Initialize webhook handler
        $this->webhook_handler = new The7Space_Webhook_Handler();
        
        // Initialize sync handlers
        new The7Space_Contact_Sync($this->api_client);
        new The7Space_Gallery_Sync($this->api_client);
        new The7Space_Wellness_Sync($this->api_client);
        
        // Initialize admin components
        if (is_admin()) {
            new The7Space_Admin();
            new The7Space_Settings();
        }
        
        // Initialize public components
        new The7Space_Shortcodes($this->api_client);
        new The7Space_Frontend($this->api_client);
    }
    
    /**
     * Setup WordPress hooks
     */
    private function setup_hooks() {
        // Activation and deactivation hooks
        register_activation_hook(__FILE__, array($this, 'activate'));
        register_deactivation_hook(__FILE__, array($this, 'deactivate'));
        
        // Plugin action links
        add_filter('plugin_action_links_' . THE7SPACE_PLUGIN_BASENAME, array($this, 'plugin_action_links'));
        
        // Enqueue scripts and styles
        add_action('wp_enqueue_scripts', array($this, 'enqueue_public_assets'));
        add_action('admin_enqueue_scripts', array($this, 'enqueue_admin_assets'));
        
        // AJAX hooks
        add_action('wp_ajax_the7space_test_connection', array($this, 'ajax_test_connection'));
        add_action('wp_ajax_the7space_sync_contacts', array($this, 'ajax_sync_contacts'));
        
        // REST API hooks
        add_action('rest_api_init', array($this, 'register_rest_routes'));
        
        // Cron hooks
        add_action('the7space_sync_data', array($this, 'cron_sync_data'));
        
        // Contact form hooks (Contact Form 7, Gravity Forms, etc.)
        add_action('wpcf7_mail_sent', array($this, 'handle_contact_form_submission'));
        add_action('gform_after_submission', array($this, 'handle_gravity_form_submission'), 10, 2);
    }
    
    /**
     * Load plugin textdomain
     */
    public function load_textdomain() {
        load_plugin_textdomain(
            'the7space-automation',
            false,
            dirname(THE7SPACE_PLUGIN_BASENAME) . '/languages'
        );
    }
    
    /**
     * Plugin activation
     */
    public function activate() {
        // Create database tables if needed
        $this->create_tables();
        
        // Set default options
        $this->set_default_options();
        
        // Schedule cron jobs
        $this->schedule_cron_jobs();
        
        // Flush rewrite rules
        flush_rewrite_rules();
        
        // Log activation
        The7Space_Logger::log('Plugin activated', 'info');
    }
    
    /**
     * Plugin deactivation
     */
    public function deactivate() {
        // Clear scheduled cron jobs
        $this->clear_cron_jobs();
        
        // Flush rewrite rules
        flush_rewrite_rules();
        
        // Log deactivation
        The7Space_Logger::log('Plugin deactivated', 'info');
    }
    
    /**
     * Create database tables
     */
    private function create_tables() {
        global $wpdb;
        
        $charset_collate = $wpdb->get_charset_collate();
        
        // Sync log table
        $table_name = $wpdb->prefix . 'the7space_sync_log';
        $sql = "CREATE TABLE $table_name (
            id mediumint(9) NOT NULL AUTO_INCREMENT,
            sync_type varchar(50) NOT NULL,
            status varchar(20) NOT NULL,
            message text,
            data longtext,
            created_at datetime DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (id),
            KEY sync_type (sync_type),
            KEY status (status),
            KEY created_at (created_at)
        ) $charset_collate;";
        
        require_once(ABSPATH . 'wp-admin/includes/upgrade.php');
        dbDelta($sql);
        
        // API cache table
        $table_name = $wpdb->prefix . 'the7space_api_cache';
        $sql = "CREATE TABLE $table_name (
            cache_key varchar(255) NOT NULL,
            cache_value longtext,
            expires_at datetime NOT NULL,
            created_at datetime DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (cache_key),
            KEY expires_at (expires_at)
        ) $charset_collate;";
        
        dbDelta($sql);
    }
    
    /**
     * Set default plugin options
     */
    private function set_default_options() {
        $default_options = array(
            'api_url' => THE7SPACE_API_URL,
            'api_key' => '',
            'webhook_secret' => '',
            'business_entity' => THE7SPACE_BUSINESS_ENTITY,
            'sync_frequency' => 'hourly',
            'enable_gallery_sync' => true,
            'enable_wellness_sync' => true,
            'enable_contact_sync' => true,
            'enable_debug_logging' => false,
            'cache_duration' => 300, // 5 minutes
        );
        
        foreach ($default_options as $key => $value) {
            if (get_option('the7space_' . $key) === false) {
                add_option('the7space_' . $key, $value);
            }
        }
    }
    
    /**
     * Schedule cron jobs
     */
    private function schedule_cron_jobs() {
        $sync_frequency = get_option('the7space_sync_frequency', 'hourly');
        
        if (!wp_next_scheduled('the7space_sync_data')) {
            wp_schedule_event(time(), $sync_frequency, 'the7space_sync_data');
        }
    }
    
    /**
     * Clear cron jobs
     */
    private function clear_cron_jobs() {
        wp_clear_scheduled_hook('the7space_sync_data');
    }
    
    /**
     * Add plugin action links
     */
    public function plugin_action_links($links) {
        $settings_link = '<a href="' . admin_url('options-general.php?page=the7space-settings') . '">' . __('Settings', 'the7space-automation') . '</a>';
        array_unshift($links, $settings_link);
        return $links;
    }
    
    /**
     * Enqueue public assets
     */
    public function enqueue_public_assets() {
        wp_enqueue_style(
            'the7space-public',
            THE7SPACE_PLUGIN_URL . 'assets/css/public.css',
            array(),
            THE7SPACE_PLUGIN_VERSION
        );
        
        wp_enqueue_script(
            'the7space-public',
            THE7SPACE_PLUGIN_URL . 'assets/js/public.js',
            array('jquery'),
            THE7SPACE_PLUGIN_VERSION,
            true
        );
        
        wp_localize_script('the7space-public', 'the7space_ajax', array(
            'ajax_url' => admin_url('admin-ajax.php'),
            'nonce' => wp_create_nonce('the7space_nonce'),
        ));
    }
    
    /**
     * Enqueue admin assets
     */
    public function enqueue_admin_assets($hook) {
        // Only load on plugin pages
        if (strpos($hook, 'the7space') === false) {
            return;
        }
        
        wp_enqueue_style(
            'the7space-admin',
            THE7SPACE_PLUGIN_URL . 'assets/css/admin.css',
            array(),
            THE7SPACE_PLUGIN_VERSION
        );
        
        wp_enqueue_script(
            'the7space-admin',
            THE7SPACE_PLUGIN_URL . 'assets/js/admin.js',
            array('jquery'),
            THE7SPACE_PLUGIN_VERSION,
            true
        );
        
        wp_localize_script('the7space-admin', 'the7space_admin', array(
            'ajax_url' => admin_url('admin-ajax.php'),
            'nonce' => wp_create_nonce('the7space_admin_nonce'),
            'strings' => array(
                'testing_connection' => __('Testing connection...', 'the7space-automation'),
                'connection_successful' => __('Connection successful!', 'the7space-automation'),
                'connection_failed' => __('Connection failed. Please check your settings.', 'the7space-automation'),
            ),
        ));
    }
    
    /**
     * Register REST API routes
     */
    public function register_rest_routes() {
        register_rest_route('the7space/v1', '/webhook', array(
            'methods' => 'POST',
            'callback' => array($this->webhook_handler, 'handle_webhook'),
            'permission_callback' => array($this->webhook_handler, 'verify_webhook_permission'),
        ));
        
        register_rest_route('the7space/v1', '/health', array(
            'methods' => 'GET',
            'callback' => array($this, 'health_check'),
            'permission_callback' => '__return_true',
        ));
    }
    
    /**
     * AJAX: Test API connection
     */
    public function ajax_test_connection() {
        check_ajax_referer('the7space_admin_nonce', 'nonce');
        
        if (!current_user_can('manage_options')) {
            wp_die(__('Insufficient permissions', 'the7space-automation'));
        }
        
        $result = $this->api_client->test_connection();
        
        wp_send_json($result);
    }
    
    /**
     * AJAX: Sync contacts
     */
    public function ajax_sync_contacts() {
        check_ajax_referer('the7space_admin_nonce', 'nonce');
        
        if (!current_user_can('manage_options')) {
            wp_die(__('Insufficient permissions', 'the7space-automation'));
        }
        
        $contact_sync = new The7Space_Contact_Sync($this->api_client);
        $result = $contact_sync->sync_all_contacts();
        
        wp_send_json($result);
    }
    
    /**
     * Cron: Sync data
     */
    public function cron_sync_data() {
        The7Space_Logger::log('Starting scheduled data sync', 'info');
        
        // Sync contacts
        if (get_option('the7space_enable_contact_sync', true)) {
            $contact_sync = new The7Space_Contact_Sync($this->api_client);
            $contact_sync->sync_all_contacts();
        }
        
        // Sync gallery data
        if (get_option('the7space_enable_gallery_sync', true)) {
            $gallery_sync = new The7Space_Gallery_Sync($this->api_client);
            $gallery_sync->sync_gallery_data();
        }
        
        // Sync wellness data
        if (get_option('the7space_enable_wellness_sync', true)) {
            $wellness_sync = new The7Space_Wellness_Sync($this->api_client);
            $wellness_sync->sync_wellness_data();
        }
        
        The7Space_Logger::log('Scheduled data sync completed', 'info');
    }
    
    /**
     * Handle Contact Form 7 submission
     */
    public function handle_contact_form_submission($contact_form) {
        $submission = WPCF7_Submission::get_instance();
        
        if ($submission) {
            $posted_data = $submission->get_posted_data();
            
            // Process contact data
            $contact_sync = new The7Space_Contact_Sync($this->api_client);
            $contact_sync->process_contact_form_submission($posted_data, 'contact_form_7');
        }
    }
    
    /**
     * Handle Gravity Forms submission
     */
    public function handle_gravity_form_submission($entry, $form) {
        // Process contact data
        $contact_sync = new The7Space_Contact_Sync($this->api_client);
        $contact_sync->process_contact_form_submission($entry, 'gravity_forms');
    }
    
    /**
     * Health check endpoint
     */
    public function health_check() {
        $health_data = array(
            'status' => 'healthy',
            'plugin_version' => THE7SPACE_PLUGIN_VERSION,
            'wordpress_version' => get_bloginfo('version'),
            'php_version' => PHP_VERSION,
            'api_connection' => $this->api_client->test_connection(),
            'timestamp' => current_time('mysql'),
        );
        
        return new WP_REST_Response($health_data, 200);
    }
    
    /**
     * Get API client instance
     */
    public function get_api_client() {
        return $this->api_client;
    }
    
    /**
     * Get webhook handler instance
     */
    public function get_webhook_handler() {
        return $this->webhook_handler;
    }
}

/**
 * Initialize plugin
 */
function the7space_automation_init() {
    return The7SpaceAutomation::get_instance();
}

// Initialize plugin
add_action('plugins_loaded', 'the7space_automation_init');

/**
 * Helper function to get plugin instance
 */
function the7space() {
    return The7SpaceAutomation::get_instance();
}

/**
 * Plugin uninstall hook
 */
register_uninstall_hook(__FILE__, 'the7space_automation_uninstall');

function the7space_automation_uninstall() {
    // Remove plugin options
    $options = array(
        'the7space_api_url',
        'the7space_api_key',
        'the7space_webhook_secret',
        'the7space_business_entity',
        'the7space_sync_frequency',
        'the7space_enable_gallery_sync',
        'the7space_enable_wellness_sync',
        'the7space_enable_contact_sync',
        'the7space_enable_debug_logging',
        'the7space_cache_duration',
    );
    
    foreach ($options as $option) {
        delete_option($option);
    }
    
    // Drop custom tables
    global $wpdb;
    $wpdb->query("DROP TABLE IF EXISTS {$wpdb->prefix}the7space_sync_log");
    $wpdb->query("DROP TABLE IF EXISTS {$wpdb->prefix}the7space_api_cache");
    
    // Clear scheduled cron jobs
    wp_clear_scheduled_hook('the7space_sync_data');
}
