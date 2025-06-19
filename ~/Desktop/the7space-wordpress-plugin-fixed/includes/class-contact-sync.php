<?php
/**
 * The 7 Space Contact Sync - Improved with error handling
 */

if (!defined('ABSPATH')) {
    exit;
}

class The7Space_Contact_Sync {
    
    private $api_client;
    
    public function __construct($api_client) {
        $this->api_client = $api_client;
        
        // Only hook into contact forms if they exist
        if (function_exists('wpcf7_get_current_contact_form')) {
            add_action('wpcf7_mail_sent', array($this, 'handle_cf7_submission'));
        }
        
        if (class_exists('GFForms')) {
            add_action('gform_after_submission', array($this, 'handle_gravity_form_submission'), 10, 2);
        }
    }
    
    public function handle_cf7_submission($contact_form) {
        try {
            if (class_exists('WPCF7_Submission')) {
                $submission = WPCF7_Submission::get_instance();
                
                if ($submission) {
                    $posted_data = $submission->get_posted_data();
                    $this->process_contact_form_submission($posted_data, 'contact_form_7');
                }
            }
        } catch (Exception $e) {
            $this->log_message('CF7 submission handling failed: ' . $e->getMessage(), 'error');
        }
    }
    
    public function handle_gravity_form_submission($entry, $form) {
        try {
            $this->process_contact_form_submission($entry, 'gravity_forms');
        } catch (Exception $e) {
            $this->log_message('Gravity Forms submission handling failed: ' . $e->getMessage(), 'error');
        }
    }
    
    public function process_contact_form_submission($data, $form_type) {
        try {
            if (!get_option('the7space_enable_contact_sync', true)) {
                return;
            }
            
            $contact_data = $this->extract_contact_data($data, $form_type);
            
            if (!empty($contact_data) && !empty($contact_data['email'])) {
                $result = $this->api_client->submit_contact($contact_data);
                
                if ($result) {
                    $this->log_message('Contact submitted successfully: ' . $contact_data['email'], 'info');
                } else {
                    $this->log_message('Failed to submit contact: ' . $contact_data['email'], 'error');
                }
            } else {
                $this->log_message('Contact data incomplete or missing email', 'warning');
            }
        } catch (Exception $e) {
            $this->log_message('Contact processing failed: ' . $e->getMessage(), 'error');
        }
    }
    
    private function extract_contact_data($data, $form_type) {
        try {
            $contact_data = array(
                'business_entity' => 'the_7_space',
                'lead_source' => 'website_contact_form',
                'form_type' => $form_type,
                'submission_time' => current_time('mysql')
            );
            
            $field_mapping = array(
                'name' => array('your-name', 'name', 'full_name', 'contact_name', 'first_name', 'last_name'),
                'email' => array('your-email', 'email', 'email_address', 'contact_email'),
                'phone' => array('your-phone', 'phone', 'phone_number', 'contact_phone'),
                'message' => array('your-message', 'message', 'comments', 'inquiry', 'description'),
                'subject' => array('your-subject', 'subject', 'topic'),
                'interest' => array('interest', 'service_interest', 'inquiry_type')
            );
            
            foreach ($field_mapping as $standard_field => $possible_names) {
                foreach ($possible_names as $field_name) {
                    if (isset($data[$field_name]) && !empty($data[$field_name])) {
                        $contact_data[$standard_field] = sanitize_text_field($data[$field_name]);
                        break;
                    }
                }
            }
            
            // Ensure we have at least an email
            if (empty($contact_data['email'])) {
                return array();
            }
            
            $contact_data['contact_type'] = $this->determine_contact_type($contact_data);
            
            return $contact_data;
        } catch (Exception $e) {
            $this->log_message('Contact data extraction failed: ' . $e->getMessage(), 'error');
            return array();
        }
    }
    
    private function determine_contact_type($contact_data) {
        try {
            $message = strtolower($contact_data['message'] ?? '');
            $subject = strtolower($contact_data['subject'] ?? '');
            $interest = strtolower($contact_data['interest'] ?? '');
            
            $content = $message . ' ' . $subject . ' ' . $interest;
            
            $keywords = array(
                'artist' => array('artist', 'artwork', 'exhibition', 'gallery', 'painting', 'sculpture', 'art show'),
                'wellness_client' => array('wellness', 'meditation', 'healing', 'therapy', 'appointment', 'session'),
                'event_attendee' => array('event', 'workshop', 'class', 'seminar', 'opening'),
                'business_partner' => array('partnership', 'collaboration', 'business', 'sponsor', 'vendor')
            );
            
            foreach ($keywords as $type => $type_keywords) {
                foreach ($type_keywords as $keyword) {
                    if (strpos($content, $keyword) !== false) {
                        return $type;
                    }
                }
            }
            
            return 'general_inquiry';
        } catch (Exception $e) {
            $this->log_message('Contact type determination failed: ' . $e->getMessage(), 'error');
            return 'general_inquiry';
        }
    }
    
    private function log_message($message, $level = 'info') {
        if (class_exists('The7Space_Logger')) {
            The7Space_Logger::log($message, $level);
        }
    }
}
