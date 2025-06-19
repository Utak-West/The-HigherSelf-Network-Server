<?php
/**
 * The 7 Space Logger - Improved with error handling
 */

if (!defined('ABSPATH')) {
    exit;
}

class The7Space_Logger {
    
    public static function log($message, $level = 'info') {
        try {
            if (!get_option('the7space_enable_debug_logging', false)) {
                return;
            }
            
            $timestamp = current_time('Y-m-d H:i:s');
            $log_entry = "[{$timestamp}] [{$level}] {$message}" . PHP_EOL;
            
            // Log to WordPress debug log if enabled
            if (defined('WP_DEBUG') && WP_DEBUG && defined('WP_DEBUG_LOG') && WP_DEBUG_LOG) {
                error_log("The7Space Plugin: {$log_entry}");
            }
            
            // Also store in plugin-specific log with error handling
            $log_file = WP_CONTENT_DIR . '/the7space-plugin.log';
            
            // Check if we can write to the log file
            if (is_writable(WP_CONTENT_DIR) || (file_exists($log_file) && is_writable($log_file))) {
                file_put_contents($log_file, $log_entry, FILE_APPEND | LOCK_EX);
            }
        } catch (Exception $e) {
            // Silent fail - don't break the site if logging fails
            if (defined('WP_DEBUG') && WP_DEBUG) {
                error_log('The7Space Logger error: ' . $e->getMessage());
            }
        }
    }
}
