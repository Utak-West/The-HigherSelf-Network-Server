<?php
/**
 * The 7 Space Logger
 */

if (!defined('ABSPATH')) {
    exit;
}

class The7Space_Logger {
    
    public static function log($message, $level = 'info') {
        if (!get_option('the7space_enable_debug_logging', false)) {
            return;
        }
        
        $timestamp = current_time('Y-m-d H:i:s');
        $log_entry = "[{$timestamp}] [{$level}] {$message}" . PHP_EOL;
        
        if (defined('WP_DEBUG') && WP_DEBUG && defined('WP_DEBUG_LOG') && WP_DEBUG_LOG) {
            error_log("The7Space Plugin: {$log_entry}");
        }
        
        $log_file = WP_CONTENT_DIR . '/the7space-plugin.log';
        file_put_contents($log_file, $log_entry, FILE_APPEND | LOCK_EX);
    }
}
