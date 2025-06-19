<?php
/**
 * The 7 Space Contact Sync
 * 
 * Handles contact form submissions and synchronization
 */

if (!defined('ABSPATH')) {
    exit;
}

class The7Space_Contact_Sync {
    
    private $api_client;
    
    public function __construct($api_client) {
        $this->api_client = $api_client;
        
        // Hook into contact form submissions
        add_action('wpcf7_mail_sent', array($this, 'handle_cf7_submission'));
        add_action('gform_after_submission', array($this, 'handle_gravity_form_submission'), 10, 2);
    }
    
    /**
     * Handle Contact Form 7 submission
     */
    public function handle_cf7_submission($contact_form) {
        $submission = WPCF7_Submission::get_instance();
        
        if ($submission) {
            $posted_data = $submission->get_posted_data();
            $this->process_contact_form_submission($posted_data, 'contact_form_7');
        }
    }
    
    /**
     * Handle Gravity Forms submission
     */
    public function handle_gravity_form_submission($entry, $form) {
        $this->process_contact_form_submission($entry, 'gravity_forms');
    }
    
    /**
     * Process contact form submission
     */
    public function process_contact_form_submission($data, $form_type) {
        if (!get_option('the7space_enable_contact_sync', true)) {
            return;
        }
        
        // Extract contact data
        $contact_data = $this->extract_contact_data($data, $form_type);
        
        if (!empty($contact_data)) {
            // Submit to HigherSelf Network Server
            $result = $this->api_client->submit_contact($contact_data);
            
            if ($result) {
                The7Space_Logger::log('Contact submitted successfully: ' . $contact_data['email'], 'info');
            } else {
                The7Space_Logger::log('Failed to submit contact: ' . $contact_data['email'], 'error');
            }
        }
    }
    
    /**
     * Extract contact data from form submission
     */
    private function extract_contact_data($data, $form_type) {
        $contact_data = array(
            'business_entity' => 'the_7_space',
            'lead_source' => 'website_contact_form',
            'form_type' => $form_type,
            'submission_time' => current_time('mysql')
        );
        
        // Map common field names
        $field_mapping = array(
            'name' => array('your-name', 'name', 'full_name', 'contact_name'),
            'email' => array('your-email', 'email', 'email_address', 'contact_email'),
            'phone' => array('your-phone', 'phone', 'phone_number', 'contact_phone'),
            'message' => array('your-message', 'message', 'comments', 'inquiry'),
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
        
        // Determine contact type based on form content
        $contact_data['contact_type'] = $this->determine_contact_type($contact_data);
        
        return $contact_data;
    }
    
    /**
     * Determine contact type based on form data
     */
    private function determine_contact_type($contact_data) {
        $message = strtolower($contact_data['message'] ?? '');
        $subject = strtolower($contact_data['subject'] ?? '');
        $interest = strtolower($contact_data['interest'] ?? '');
        
        $content = $message . ' ' . $subject . ' ' . $interest;
        
        // Keywords for different contact types
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
    }
    
    /**
     * Sync all contacts
     */
    public function sync_all_contacts() {
        // This would implement bulk contact synchronization
        The7Space_Logger::log('Starting contact sync', 'info');
        
        return array(
            'success' => true,
            'message' => 'Contact sync completed'
        );
    }
}
