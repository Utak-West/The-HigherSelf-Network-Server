<?php
// The 7 Space Direct Integration Hook
// Add this code to your theme's functions.php file

add_action('wpcf7_mail_sent', 'the7space_direct_integration');
function the7space_direct_integration($contact_form) {
    // Your ngrok URL - ALREADY CONFIGURED!
    $api_url = 'https://665a-69-120-120-253.ngrok-free.app';
    $api_key = 'the7space_automation_api_key_2024';
    
    $submission = WPCF7_Submission::get_instance();
    if (!$submission) return;
    
    $posted_data = $submission->get_posted_data();
    
    $contact_data = array(
        'business_entity' => 'the_7_space',
        'lead_source' => 'website_contact_form',
        'form_type' => 'contact_form_7_php',
        'submission_time' => current_time('c'),
        'name' => isset($posted_data['your-name']) ? $posted_data['your-name'] : '',
        'email' => isset($posted_data['your-email']) ? $posted_data['your-email'] : '',
        'phone' => isset($posted_data['your-phone']) ? $posted_data['your-phone'] : '',
        'message' => isset($posted_data['your-message']) ? $posted_data['your-message'] : '',
        'subject' => isset($posted_data['your-subject']) ? $posted_data['your-subject'] : '',
        'contact_type' => 'general_inquiry'
    );
    
    $response = wp_remote_post($api_url . '/api/the7space/contacts', array(
        'body' => json_encode($contact_data),
        'headers' => array(
            'Content-Type' => 'application/json',
            'Authorization' => 'Bearer ' . $api_key
        ),
        'timeout' => 15
    ));
    
    if (is_wp_error($response)) {
        error_log('The7Space Integration Error: ' . $response->get_error_message());
    } else {
        error_log('The7Space Integration: Contact sent successfully');
    }
}
?>
