<?php
/**
 * The 7 Space API Client
 * 
 * Handles communication between WordPress and the HigherSelf Network Server
 */

if (!defined('ABSPATH')) {
    exit;
}

class The7Space_API_Client {
    
    /**
     * API base URL
     */
    private $api_url;
    
    /**
     * API key for authentication
     */
    private $api_key;
    
    /**
     * Request timeout in seconds
     */
    private $timeout = 30;
    
    /**
     * Constructor
     */
    public function __construct() {
        $this->api_url = The7Space_Config::get_api_url();
        $this->api_key = The7Space_Config::get_api_key();
    }
    
    /**
     * Test API connection
     */
    public function test_connection() {
        $response = $this->make_request('GET', '/health');
        
        if (is_wp_error($response)) {
            return array(
                'connected' => false,
                'error' => $response->get_error_message()
            );
        }
        
        $body = wp_remote_retrieve_body($response);
        $data = json_decode($body, true);
        
        if ($data && isset($data['status']) && $data['status'] === 'healthy') {
            return array('connected' => true);
        }
        
        return array(
            'connected' => false,
            'error' => 'Invalid response from server'
        );
    }
    
    /**
     * Create a new contact
     */
    public function create_contact($contact_data) {
        $endpoint = '/api/the7space/contacts';
        
        $response = $this->make_request('POST', $endpoint, $contact_data);
        
        if (is_wp_error($response)) {
            return array(
                'success' => false,
                'error' => $response->get_error_message()
            );
        }
        
        $body = wp_remote_retrieve_body($response);
        $data = json_decode($body, true);
        
        return $data;
    }
    
    /**
     * Book an appointment
     */
    public function book_appointment($booking_data) {
        $endpoint = '/api/the7space/appointments';
        
        $response = $this->make_request('POST', $endpoint, $booking_data);
        
        if (is_wp_error($response)) {
            return array(
                'success' => false,
                'error' => $response->get_error_message()
            );
        }
        
        $body = wp_remote_retrieve_body($response);
        $data = json_decode($body, true);
        
        return $data;
    }
    
    /**
     * Get available artworks
     */
    public function get_artworks($filters = array()) {
        $endpoint = '/api/the7space/artworks';
        
        if (!empty($filters)) {
            $endpoint .= '?' . http_build_query($filters);
        }
        
        $response = $this->make_request('GET', $endpoint);
        
        if (is_wp_error($response)) {
            return false;
        }
        
        $body = wp_remote_retrieve_body($response);
        $data = json_decode($body, true);
        
        return $data;
    }
    
    /**
     * Get upcoming events
     */
    public function get_events($filters = array()) {
        $endpoint = '/api/the7space/events';
        
        if (!empty($filters)) {
            $endpoint .= '?' . http_build_query($filters);
        }
        
        $response = $this->make_request('GET', $endpoint);
        
        if (is_wp_error($response)) {
            return false;
        }
        
        $body = wp_remote_retrieve_body($response);
        $data = json_decode($body, true);
        
        return $data;
    }
    
    /**
     * Get available appointment slots
     */
    public function get_available_slots($service_id, $date, $days_ahead = 7) {
        $endpoint = '/api/the7space/appointments/availability';
        
        $params = array(
            'service_id' => $service_id,
            'date' => $date,
            'days_ahead' => $days_ahead
        );
        
        $endpoint .= '?' . http_build_query($params);
        
        $response = $this->make_request('GET', $endpoint);
        
        if (is_wp_error($response)) {
            return false;
        }
        
        $body = wp_remote_retrieve_body($response);
        $data = json_decode($body, true);
        
        return $data;
    }
    
    /**
     * Get wellness services
     */
    public function get_services() {
        $endpoint = '/api/the7space/services';
        
        $response = $this->make_request('GET', $endpoint);
        
        if (is_wp_error($response)) {
            return false;
        }
        
        $body = wp_remote_retrieve_body($response);
        $data = json_decode($body, true);
        
        return $data;
    }
    
    /**
     * Track visitor activity
     */
    public function track_visitor($tracking_data) {
        $endpoint = '/api/the7space/analytics/track';
        
        $response = $this->make_request('POST', $endpoint, $tracking_data);
        
        if (is_wp_error($response)) {
            return false;
        }
        
        return true;
    }
    
    /**
     * Submit lead scoring data
     */
    public function submit_lead_data($lead_data) {
        $endpoint = '/api/the7space/leads';
        
        $response = $this->make_request('POST', $endpoint, $lead_data);
        
        if (is_wp_error($response)) {
            return array(
                'success' => false,
                'error' => $response->get_error_message()
            );
        }
        
        $body = wp_remote_retrieve_body($response);
        $data = json_decode($body, true);
        
        return $data;
    }
    
    /**
     * Make HTTP request to API
     */
    private function make_request($method, $endpoint, $data = null) {
        $url = rtrim($this->api_url, '/') . $endpoint;
        
        $args = array(
            'method' => $method,
            'timeout' => $this->timeout,
            'headers' => array(
                'Content-Type' => 'application/json',
                'Authorization' => 'Bearer ' . $this->api_key,
                'User-Agent' => 'The7Space-WordPress-Plugin/' . THE7SPACE_PLUGIN_VERSION
            )
        );
        
        if ($data && in_array($method, array('POST', 'PUT', 'PATCH'))) {
            $args['body'] = json_encode($data);
        }
        
        // Add debug logging if enabled
        if (The7Space_Config::is_debug_mode()) {
            error_log('The7Space API Request: ' . $method . ' ' . $url);
            if ($data) {
                error_log('The7Space API Data: ' . json_encode($data));
            }
        }
        
        $response = wp_remote_request($url, $args);
        
        // Log response if debug mode is enabled
        if (The7Space_Config::is_debug_mode()) {
            if (is_wp_error($response)) {
                error_log('The7Space API Error: ' . $response->get_error_message());
            } else {
                $status_code = wp_remote_retrieve_response_code($response);
                error_log('The7Space API Response: ' . $status_code);
            }
        }
        
        return $response;
    }
    
    /**
     * Get API health status
     */
    public function get_health_status() {
        $response = $this->make_request('GET', '/health');
        
        if (is_wp_error($response)) {
            return array(
                'status' => 'error',
                'message' => $response->get_error_message()
            );
        }
        
        $status_code = wp_remote_retrieve_response_code($response);
        $body = wp_remote_retrieve_body($response);
        $data = json_decode($body, true);
        
        if ($status_code === 200 && $data) {
            return $data;
        }
        
        return array(
            'status' => 'error',
            'message' => 'Invalid response from server'
        );
    }
    
    /**
     * Validate API configuration
     */
    public function validate_config() {
        $errors = array();
        
        if (empty($this->api_url)) {
            $errors[] = 'API URL is not configured';
        }
        
        if (empty($this->api_key)) {
            $errors[] = 'API Key is not configured';
        }
        
        // Test URL format
        if (!empty($this->api_url) && !filter_var($this->api_url, FILTER_VALIDATE_URL)) {
            $errors[] = 'API URL format is invalid';
        }
        
        return $errors;
    }
    
    /**
     * Get API statistics
     */
    public function get_api_stats() {
        $response = $this->make_request('GET', '/api/the7space/stats');
        
        if (is_wp_error($response)) {
            return false;
        }
        
        $body = wp_remote_retrieve_body($response);
        $data = json_decode($body, true);
        
        return $data;
    }
}
