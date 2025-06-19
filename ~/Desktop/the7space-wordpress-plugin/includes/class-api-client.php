<?php
/**
 * The 7 Space API Client
 */

if (!defined('ABSPATH')) {
    exit;
}

class The7Space_API_Client {
    
    private $api_url;
    private $api_key;
    private $timeout;
    
    public function __construct() {
        $this->api_url = get_option('the7space_api_url', 'http://localhost:8000');
        $this->api_key = get_option('the7space_api_key', '');
        $this->timeout = 30;
    }
    
    public function test_connection() {
        $response = $this->make_request('GET', '/health');
        
        if (is_wp_error($response)) {
            return array(
                'success' => false,
                'message' => $response->get_error_message()
            );
        }
        
        $status_code = wp_remote_retrieve_response_code($response);
        
        if ($status_code === 200) {
            return array(
                'success' => true,
                'message' => 'Connection successful'
            );
        } else {
            return array(
                'success' => false,
                'message' => 'Connection failed: HTTP ' . $status_code
            );
        }
    }
    
    public function submit_contact($contact_data) {
        $contact_data['business_entity'] = 'the_7_space';
        
        $response = $this->make_request('POST', '/api/the7space/contacts', $contact_data);
        
        if (is_wp_error($response)) {
            The7Space_Logger::log('Contact submission failed: ' . $response->get_error_message(), 'error');
            return false;
        }
        
        $status_code = wp_remote_retrieve_response_code($response);
        
        if ($status_code === 200 || $status_code === 201) {
            The7Space_Logger::log('Contact submitted successfully', 'info');
            return true;
        } else {
            The7Space_Logger::log('Contact submission failed: HTTP ' . $status_code, 'error');
            return false;
        }
    }
    
    private function make_request($method, $endpoint, $data = null) {
        $url = rtrim($this->api_url, '/') . $endpoint;
        
        $args = array(
            'method' => $method,
            'timeout' => $this->timeout,
            'headers' => array(
                'Content-Type' => 'application/json',
                'User-Agent' => 'The7Space-WordPress-Plugin/1.0'
            )
        );
        
        if (!empty($this->api_key)) {
            $args['headers']['Authorization'] = 'Bearer ' . $this->api_key;
        }
        
        if ($data && in_array($method, array('POST', 'PUT', 'PATCH'))) {
            $args['body'] = json_encode($data);
        }
        
        return wp_remote_request($url, $args);
    }
}
