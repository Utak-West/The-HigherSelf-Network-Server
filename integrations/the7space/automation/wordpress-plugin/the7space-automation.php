<?php
/**
 * Plugin Name: The 7 Space Automation
 * Plugin URI: https://the7space.com
 * Description: Automated integration with The 7 Space HigherSelf Network Server for gallery and wellness center operations.
 * Version: 1.0.0
 * Author: The 7 Space Development Team
 * License: GPL v2 or later
 * Text Domain: the7space-automation
 */

// Prevent direct access
if (!defined('ABSPATH')) {
    exit;
}

// Define plugin constants
define('THE7SPACE_PLUGIN_VERSION', '1.0.0');
define('THE7SPACE_PLUGIN_PATH', plugin_dir_path(__FILE__));
define('THE7SPACE_PLUGIN_URL', plugin_dir_url(__FILE__));
define('THE7SPACE_PLUGIN_FILE', __FILE__);

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
        // Load dependencies
        $this->load_dependencies();
        
        // Initialize hooks
        add_action('init', array($this, 'init_plugin'));
        add_action('wp_enqueue_scripts', array($this, 'enqueue_scripts'));
        add_action('admin_menu', array($this, 'add_admin_menu'));
        add_action('admin_init', array($this, 'admin_init'));
        
        // AJAX hooks for frontend
        add_action('wp_ajax_the7space_book_appointment', array($this, 'handle_appointment_booking'));
        add_action('wp_ajax_nopriv_the7space_book_appointment', array($this, 'handle_appointment_booking'));
        add_action('wp_ajax_the7space_contact_form', array($this, 'handle_contact_form'));
        add_action('wp_ajax_nopriv_the7space_contact_form', array($this, 'handle_contact_form'));
        add_action('wp_ajax_the7space_get_artworks', array($this, 'handle_get_artworks'));
        add_action('wp_ajax_nopriv_the7space_get_artworks', array($this, 'handle_get_artworks'));
        
        // Shortcode registration
        add_action('init', array($this, 'register_shortcodes'));
        
        // Plugin activation/deactivation
        register_activation_hook(__FILE__, array($this, 'activate'));
        register_deactivation_hook(__FILE__, array($this, 'deactivate'));
    }
    
    /**
     * Load plugin dependencies
     */
    private function load_dependencies() {
        require_once THE7SPACE_PLUGIN_PATH . 'includes/config.php';
        require_once THE7SPACE_PLUGIN_PATH . 'includes/api-client.php';
        require_once THE7SPACE_PLUGIN_PATH . 'includes/gallery-functions.php';
        require_once THE7SPACE_PLUGIN_PATH . 'includes/wellness-functions.php';
        require_once THE7SPACE_PLUGIN_PATH . 'includes/admin-functions.php';
        require_once THE7SPACE_PLUGIN_PATH . 'includes/shortcodes.php';
    }
    
    /**
     * Initialize plugin after WordPress loads
     */
    public function init_plugin() {
        // Initialize API client
        $this->api_client = new The7Space_API_Client();
        
        // Load text domain for translations
        load_plugin_textdomain('the7space-automation', false, dirname(plugin_basename(__FILE__)) . '/languages');
        
        // Initialize visitor tracking
        if (The7Space_Config::is_feature_enabled('visitor_tracking')) {
            $this->init_visitor_tracking();
        }
    }
    
    /**
     * Enqueue scripts and styles
     */
    public function enqueue_scripts() {
        // Enqueue main frontend script
        wp_enqueue_script(
            'the7space-frontend',
            THE7SPACE_PLUGIN_URL . 'assets/js/the7space-frontend.js',
            array('jquery'),
            THE7SPACE_PLUGIN_VERSION,
            true
        );
        
        // Enqueue styles
        wp_enqueue_style(
            'the7space-styles',
            THE7SPACE_PLUGIN_URL . 'assets/css/the7space-styles.css',
            array(),
            THE7SPACE_PLUGIN_VERSION
        );
        
        // Localize script with AJAX URL and nonce
        wp_localize_script('the7space-frontend', 'the7space_ajax', array(
            'ajax_url' => admin_url('admin-ajax.php'),
            'nonce' => wp_create_nonce('the7space_nonce'),
            'api_url' => The7Space_Config::get_api_url(),
            'debug_mode' => The7Space_Config::is_debug_mode(),
            'features' => array(
                'gallery_enabled' => The7Space_Config::is_feature_enabled('gallery'),
                'wellness_enabled' => The7Space_Config::is_feature_enabled('wellness'),
                'analytics_enabled' => The7Space_Config::is_feature_enabled('analytics')
            )
        ));
    }
    
    /**
     * Add admin menu
     */
    public function add_admin_menu() {
        add_options_page(
            __('The 7 Space Settings', 'the7space-automation'),
            __('The 7 Space', 'the7space-automation'),
            'manage_options',
            'the7space-settings',
            array($this, 'admin_page')
        );
    }
    
    /**
     * Initialize admin settings
     */
    public function admin_init() {
        register_setting('the7space_settings', 'the7space_options');
        
        // API Configuration Section
        add_settings_section(
            'the7space_api_section',
            __('API Configuration', 'the7space-automation'),
            array($this, 'api_section_callback'),
            'the7space_settings'
        );
        
        add_settings_field(
            'api_url',
            __('Server URL', 'the7space-automation'),
            array($this, 'api_url_callback'),
            'the7space_settings',
            'the7space_api_section'
        );
        
        add_settings_field(
            'api_key',
            __('API Key', 'the7space-automation'),
            array($this, 'api_key_callback'),
            'the7space_settings',
            'the7space_api_section'
        );
        
        // Feature Configuration Section
        add_settings_section(
            'the7space_features_section',
            __('Feature Configuration', 'the7space-automation'),
            array($this, 'features_section_callback'),
            'the7space_settings'
        );
        
        add_settings_field(
            'gallery_enabled',
            __('Enable Gallery Features', 'the7space-automation'),
            array($this, 'gallery_enabled_callback'),
            'the7space_settings',
            'the7space_features_section'
        );
        
        add_settings_field(
            'wellness_enabled',
            __('Enable Wellness Features', 'the7space-automation'),
            array($this, 'wellness_enabled_callback'),
            'the7space_settings',
            'the7space_features_section'
        );
    }
    
    /**
     * Admin page content
     */
    public function admin_page() {
        ?>
        <div class="wrap">
            <h1><?php echo esc_html(get_admin_page_title()); ?></h1>
            
            <?php
            // Show connection status
            $connection_status = $this->check_api_connection();
            if ($connection_status['connected']) {
                echo '<div class="notice notice-success"><p><strong>✅ Connected to HigherSelf Network Server</strong></p></div>';
            } else {
                echo '<div class="notice notice-error"><p><strong>❌ Connection Failed:</strong> ' . esc_html($connection_status['error']) . '</p></div>';
            }
            ?>
            
            <form action="options.php" method="post">
                <?php
                settings_fields('the7space_settings');
                do_settings_sections('the7space_settings');
                submit_button();
                ?>
            </form>
            
            <div class="the7space-admin-info">
                <h2><?php _e('System Information', 'the7space-automation'); ?></h2>
                <table class="widefat">
                    <tr>
                        <td><strong><?php _e('Plugin Version', 'the7space-automation'); ?></strong></td>
                        <td><?php echo THE7SPACE_PLUGIN_VERSION; ?></td>
                    </tr>
                    <tr>
                        <td><strong><?php _e('WordPress Version', 'the7space-automation'); ?></strong></td>
                        <td><?php echo get_bloginfo('version'); ?></td>
                    </tr>
                    <tr>
                        <td><strong><?php _e('PHP Version', 'the7space-automation'); ?></strong></td>
                        <td><?php echo PHP_VERSION; ?></td>
                    </tr>
                    <tr>
                        <td><strong><?php _e('Server URL', 'the7space-automation'); ?></strong></td>
                        <td><?php echo esc_html(The7Space_Config::get_api_url()); ?></td>
                    </tr>
                </table>
            </div>
        </div>
        <?php
    }
    
    /**
     * Handle appointment booking AJAX request
     */
    public function handle_appointment_booking() {
        // Verify nonce
        if (!wp_verify_nonce($_POST['nonce'], 'the7space_nonce')) {
            wp_die('Security check failed');
        }
        
        // Sanitize input data
        $booking_data = array(
            'client_name' => sanitize_text_field($_POST['client_name']),
            'client_email' => sanitize_email($_POST['client_email']),
            'client_phone' => sanitize_text_field($_POST['client_phone']),
            'service_id' => sanitize_text_field($_POST['service_id']),
            'appointment_datetime' => sanitize_text_field($_POST['appointment_datetime']),
            'notes' => sanitize_textarea_field($_POST['notes'])
        );
        
        // Send to API
        $result = $this->api_client->book_appointment($booking_data);
        
        if ($result && $result['success']) {
            wp_send_json_success(array(
                'message' => __('Appointment booked successfully!', 'the7space-automation'),
                'appointment_id' => $result['appointment_id']
            ));
        } else {
            wp_send_json_error(array(
                'message' => $result['error'] ?? __('Booking failed. Please try again.', 'the7space-automation')
            ));
        }
    }
    
    /**
     * Handle contact form AJAX request
     */
    public function handle_contact_form() {
        // Verify nonce
        if (!wp_verify_nonce($_POST['nonce'], 'the7space_nonce')) {
            wp_die('Security check failed');
        }
        
        // Sanitize input data
        $contact_data = array(
            'name' => sanitize_text_field($_POST['name']),
            'email' => sanitize_email($_POST['email']),
            'phone' => sanitize_text_field($_POST['phone']),
            'message' => sanitize_textarea_field($_POST['message']),
            'interests' => array_map('sanitize_text_field', $_POST['interests'] ?? array()),
            'source' => 'website_contact_form'
        );
        
        // Send to API
        $result = $this->api_client->create_contact($contact_data);
        
        if ($result && $result['success']) {
            wp_send_json_success(array(
                'message' => __('Thank you for your message! We\'ll be in touch soon.', 'the7space-automation')
            ));
        } else {
            wp_send_json_error(array(
                'message' => __('Message failed to send. Please try again.', 'the7space-automation')
            ));
        }
    }
    
    /**
     * Handle get artworks AJAX request
     */
    public function handle_get_artworks() {
        // Get artworks from API
        $artworks = $this->api_client->get_artworks(array(
            'status' => 'available',
            'limit' => 20
        ));
        
        if ($artworks) {
            wp_send_json_success($artworks);
        } else {
            wp_send_json_error(array(
                'message' => __('Failed to load artworks.', 'the7space-automation')
            ));
        }
    }
    
    /**
     * Register shortcodes
     */
    public function register_shortcodes() {
        add_shortcode('the7space_gallery', 'the7space_gallery_shortcode');
        add_shortcode('the7space_booking_form', 'the7space_booking_form_shortcode');
        add_shortcode('the7space_contact_form', 'the7space_contact_form_shortcode');
        add_shortcode('the7space_events', 'the7space_events_shortcode');
    }
    
    /**
     * Initialize visitor tracking
     */
    private function init_visitor_tracking() {
        if (!is_admin()) {
            add_action('wp_footer', array($this, 'add_tracking_script'));
        }
    }
    
    /**
     * Add tracking script to footer
     */
    public function add_tracking_script() {
        ?>
        <script>
        // The 7 Space visitor tracking
        (function() {
            var trackingData = {
                page_url: window.location.href,
                page_title: document.title,
                referrer: document.referrer,
                timestamp: new Date().toISOString(),
                user_agent: navigator.userAgent
            };
            
            // Send tracking data
            jQuery.post(the7space_ajax.ajax_url, {
                action: 'the7space_track_visitor',
                nonce: the7space_ajax.nonce,
                tracking_data: trackingData
            });
        })();
        </script>
        <?php
    }
    
    /**
     * Check API connection
     */
    private function check_api_connection() {
        if (!$this->api_client) {
            return array('connected' => false, 'error' => 'API client not initialized');
        }
        
        return $this->api_client->test_connection();
    }
    
    /**
     * Plugin activation
     */
    public function activate() {
        // Create default options
        $default_options = array(
            'api_url' => 'http://localhost:8000',
            'api_key' => '',
            'gallery_enabled' => true,
            'wellness_enabled' => true,
            'analytics_enabled' => true,
            'debug_mode' => false
        );
        
        add_option('the7space_options', $default_options);
        
        // Flush rewrite rules
        flush_rewrite_rules();
    }
    
    /**
     * Plugin deactivation
     */
    public function deactivate() {
        // Flush rewrite rules
        flush_rewrite_rules();
    }
    
    // Admin callback functions
    public function api_section_callback() {
        echo '<p>' . __('Configure your HigherSelf Network Server connection.', 'the7space-automation') . '</p>';
    }
    
    public function api_url_callback() {
        $options = get_option('the7space_options');
        echo '<input type="text" name="the7space_options[api_url]" value="' . esc_attr($options['api_url'] ?? '') . '" class="regular-text" placeholder="http://localhost:8000" />';
        echo '<p class="description">' . __('Your HigherSelf Network Server URL (e.g., http://localhost:8000 for development)', 'the7space-automation') . '</p>';
    }
    
    public function api_key_callback() {
        $options = get_option('the7space_options');
        echo '<input type="password" name="the7space_options[api_key]" value="' . esc_attr($options['api_key'] ?? '') . '" class="regular-text" />';
        echo '<p class="description">' . __('Your THE7SPACE_API_KEY from the server configuration', 'the7space-automation') . '</p>';
    }
    
    public function features_section_callback() {
        echo '<p>' . __('Enable or disable specific features.', 'the7space-automation') . '</p>';
    }
    
    public function gallery_enabled_callback() {
        $options = get_option('the7space_options');
        $checked = isset($options['gallery_enabled']) && $options['gallery_enabled'] ? 'checked' : '';
        echo '<input type="checkbox" name="the7space_options[gallery_enabled]" value="1" ' . $checked . ' />';
        echo '<label>' . __('Enable gallery automation features', 'the7space-automation') . '</label>';
    }
    
    public function wellness_enabled_callback() {
        $options = get_option('the7space_options');
        $checked = isset($options['wellness_enabled']) && $options['wellness_enabled'] ? 'checked' : '';
        echo '<input type="checkbox" name="the7space_options[wellness_enabled]" value="1" ' . $checked . ' />';
        echo '<label>' . __('Enable wellness center automation features', 'the7space-automation') . '</label>';
    }
}

// Initialize plugin
The7SpaceAutomation::get_instance();
