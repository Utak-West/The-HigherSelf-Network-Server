<?php
/**
 * The 7 Space Admin Class
 * 
 * Handles WordPress admin functionality
 */

if (!defined('ABSPATH')) {
    exit;
}

class The7Space_Admin {
    
    public function __construct() {
        add_action('admin_init', array($this, 'init'));
        add_action('admin_notices', array($this, 'admin_notices'));
    }
    
    /**
     * Initialize admin functionality
     */
    public function init() {
        // Admin initialization code
    }
    
    /**
     * Display admin notices
     */
    public function admin_notices() {
        // Check if plugin is configured
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
}
