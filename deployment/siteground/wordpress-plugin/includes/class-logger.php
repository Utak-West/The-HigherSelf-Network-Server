<?php
/**
 * The 7 Space Logger
 * 
 * Simple logging functionality for The 7 Space WordPress plugin
 */

if (!defined('ABSPATH')) {
    exit;
}

class The7Space_Logger {
    
    /**
     * Log a message
     */
    public static function log($message, $level = 'info') {
        if (!get_option('the7space_enable_debug_logging', false)) {
            return;
        }
        
        $timestamp = current_time('Y-m-d H:i:s');
        $log_entry = "[{$timestamp}] [{$level}] {$message}" . PHP_EOL;
        
        // Log to WordPress debug log if enabled
        if (defined('WP_DEBUG') && WP_DEBUG && defined('WP_DEBUG_LOG') && WP_DEBUG_LOG) {
            error_log("The7Space Plugin: {$log_entry}");
        }
        
        // Also store in plugin-specific log
        $log_file = WP_CONTENT_DIR . '/the7space-plugin.log';
        file_put_contents($log_file, $log_entry, FILE_APPEND | LOCK_EX);
    }
}
