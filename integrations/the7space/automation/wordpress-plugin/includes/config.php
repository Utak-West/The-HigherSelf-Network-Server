<?php
/**
 * The 7 Space Configuration
 * 
 * Configuration management for The 7 Space WordPress plugin
 */

if (!defined('ABSPATH')) {
    exit;
}

class The7Space_Config {
    
    /**
     * Default configuration values
     */
    private static $defaults = array(
        'api_url' => 'http://localhost:8000',
        'api_key' => '',
        'webhook_secret' => '',
        'gallery_enabled' => true,
        'wellness_enabled' => true,
        'analytics_enabled' => true,
        'debug_mode' => false,
        'cache_enabled' => true,
        'cache_duration' => 300, // 5 minutes
        'rate_limit_enabled' => true,
        'rate_limit_requests' => 100,
        'rate_limit_window' => 3600 // 1 hour
    );
    
    /**
     * Get plugin options
     */
    private static function get_options() {
        $options = get_option('the7space_options', array());
        return wp_parse_args($options, self::$defaults);
    }
    
    /**
     * Get API URL
     */
    public static function get_api_url() {
        $options = self::get_options();
        $api_url = $options['api_url'];
        
        // Environment-based URL detection
        if (defined('WP_DEBUG') && WP_DEBUG) {
            // Development environment
            if (empty($api_url) || $api_url === self::$defaults['api_url']) {
                return 'http://localhost:8000';
            }
        }
        
        return rtrim($api_url, '/');
    }
    
    /**
     * Get API Key
     */
    public static function get_api_key() {
        $options = self::get_options();
        return $options['api_key'];
    }
    
    /**
     * Get webhook secret
     */
    public static function get_webhook_secret() {
        $options = self::get_options();
        return $options['webhook_secret'];
    }
    
    /**
     * Check if a feature is enabled
     */
    public static function is_feature_enabled($feature) {
        $options = self::get_options();
        
        switch ($feature) {
            case 'gallery':
                return !empty($options['gallery_enabled']);
            case 'wellness':
                return !empty($options['wellness_enabled']);
            case 'analytics':
                return !empty($options['analytics_enabled']);
            case 'visitor_tracking':
                return !empty($options['analytics_enabled']);
            case 'cache':
                return !empty($options['cache_enabled']);
            case 'rate_limit':
                return !empty($options['rate_limit_enabled']);
            default:
                return false;
        }
    }
    
    /**
     * Check if debug mode is enabled
     */
    public static function is_debug_mode() {
        $options = self::get_options();
        return !empty($options['debug_mode']) || (defined('WP_DEBUG') && WP_DEBUG);
    }
    
    /**
     * Get cache duration
     */
    public static function get_cache_duration() {
        $options = self::get_options();
        return intval($options['cache_duration']);
    }
    
    /**
     * Get rate limit settings
     */
    public static function get_rate_limit_settings() {
        $options = self::get_options();
        return array(
            'requests' => intval($options['rate_limit_requests']),
            'window' => intval($options['rate_limit_window'])
        );
    }
    
    /**
     * Validate configuration
     */
    public static function validate_config() {
        $errors = array();
        $options = self::get_options();
        
        // Validate API URL
        if (empty($options['api_url'])) {
            $errors[] = __('API URL is required', 'the7space-automation');
        } elseif (!filter_var($options['api_url'], FILTER_VALIDATE_URL)) {
            $errors[] = __('API URL must be a valid URL', 'the7space-automation');
        }
        
        // Validate API Key
        if (empty($options['api_key'])) {
            $errors[] = __('API Key is required', 'the7space-automation');
        } elseif (strlen($options['api_key']) < 16) {
            $errors[] = __('API Key appears to be too short', 'the7space-automation');
        }
        
        // Validate cache duration
        if (!empty($options['cache_duration']) && (!is_numeric($options['cache_duration']) || $options['cache_duration'] < 60)) {
            $errors[] = __('Cache duration must be at least 60 seconds', 'the7space-automation');
        }
        
        return $errors;
    }
    
    /**
     * Get environment information
     */
    public static function get_environment_info() {
        return array(
            'wordpress_version' => get_bloginfo('version'),
            'php_version' => PHP_VERSION,
            'plugin_version' => THE7SPACE_PLUGIN_VERSION,
            'debug_mode' => self::is_debug_mode(),
            'api_url' => self::get_api_url(),
            'features_enabled' => array(
                'gallery' => self::is_feature_enabled('gallery'),
                'wellness' => self::is_feature_enabled('wellness'),
                'analytics' => self::is_feature_enabled('analytics'),
                'cache' => self::is_feature_enabled('cache')
            )
        );
    }
    
    /**
     * Get API endpoints
     */
    public static function get_api_endpoints() {
        $base_url = self::get_api_url();
        
        return array(
            'health' => $base_url . '/health',
            'contacts' => $base_url . '/api/the7space/contacts',
            'artworks' => $base_url . '/api/the7space/artworks',
            'appointments' => $base_url . '/api/the7space/appointments',
            'events' => $base_url . '/api/the7space/events',
            'services' => $base_url . '/api/the7space/services',
            'analytics' => $base_url . '/api/the7space/analytics',
            'leads' => $base_url . '/api/the7space/leads'
        );
    }
    
    /**
     * Update configuration option
     */
    public static function update_option($key, $value) {
        $options = self::get_options();
        $options[$key] = $value;
        return update_option('the7space_options', $options);
    }
    
    /**
     * Get configuration option
     */
    public static function get_option($key, $default = null) {
        $options = self::get_options();
        return isset($options[$key]) ? $options[$key] : $default;
    }
    
    /**
     * Reset configuration to defaults
     */
    public static function reset_to_defaults() {
        return update_option('the7space_options', self::$defaults);
    }
    
    /**
     * Export configuration
     */
    public static function export_config() {
        $options = self::get_options();
        
        // Remove sensitive data from export
        $export_options = $options;
        unset($export_options['api_key']);
        unset($export_options['webhook_secret']);
        
        return $export_options;
    }
    
    /**
     * Import configuration
     */
    public static function import_config($config) {
        if (!is_array($config)) {
            return false;
        }
        
        $current_options = self::get_options();
        
        // Merge with current options, preserving sensitive data
        $new_options = array_merge($current_options, $config);
        
        // Validate before saving
        $temp_options = get_option('the7space_options');
        update_option('the7space_options', $new_options);
        
        $errors = self::validate_config();
        if (!empty($errors)) {
            // Restore previous options if validation fails
            update_option('the7space_options', $temp_options);
            return false;
        }
        
        return true;
    }
    
    /**
     * Get default services configuration
     */
    public static function get_default_services() {
        return array(
            'massage_60' => array(
                'name' => __('Therapeutic Massage (60 min)', 'the7space-automation'),
                'duration' => 60,
                'price' => 120,
                'description' => __('Full body therapeutic massage for relaxation and healing', 'the7space-automation')
            ),
            'yoga_private' => array(
                'name' => __('Private Yoga Session', 'the7space-automation'),
                'duration' => 90,
                'price' => 100,
                'description' => __('One-on-one yoga instruction tailored to your needs', 'the7space-automation')
            ),
            'meditation_guided' => array(
                'name' => __('Guided Meditation', 'the7space-automation'),
                'duration' => 45,
                'price' => 60,
                'description' => __('Personalized meditation guidance and instruction', 'the7space-automation')
            ),
            'reiki_healing' => array(
                'name' => __('Reiki Healing Session', 'the7space-automation'),
                'duration' => 75,
                'price' => 90,
                'description' => __('Energy healing and chakra balancing', 'the7space-automation')
            ),
            'wellness_consultation' => array(
                'name' => __('Wellness Consultation', 'the7space-automation'),
                'duration' => 60,
                'price' => 80,
                'description' => __('Comprehensive wellness assessment and planning', 'the7space-automation')
            )
        );
    }
    
    /**
     * Get business hours
     */
    public static function get_business_hours() {
        return array(
            'monday' => array('open' => '10:00', 'close' => '18:00'),
            'tuesday' => array('open' => '10:00', 'close' => '18:00'),
            'wednesday' => array('open' => '10:00', 'close' => '18:00'),
            'thursday' => array('open' => '10:00', 'close' => '18:00'),
            'friday' => array('open' => '10:00', 'close' => '18:00'),
            'saturday' => array('open' => '10:00', 'close' => '17:00'),
            'sunday' => array('closed' => true)
        );
    }
    
    /**
     * Check if business is open
     */
    public static function is_business_open($day = null, $time = null) {
        if (!$day) {
            $day = strtolower(date('l'));
        }
        if (!$time) {
            $time = date('H:i');
        }
        
        $hours = self::get_business_hours();
        $day_hours = isset($hours[$day]) ? $hours[$day] : array();
        
        if (isset($day_hours['closed']) && $day_hours['closed']) {
            return false;
        }
        
        if (!isset($day_hours['open']) || !isset($day_hours['close'])) {
            return false;
        }
        
        $current_time = strtotime($time);
        $open_time = strtotime($day_hours['open']);
        $close_time = strtotime($day_hours['close']);
        
        return $current_time >= $open_time && $current_time <= $close_time;
    }
}
