/**
 * The 7 Space Direct Integration
 * Add this JavaScript to your WordPress site to capture contact form submissions
 * No plugin required!
 */

(function() {
    'use strict';
    
    // Configuration - UPDATE THE API_URL WITH YOUR NGROK URL
    const CONFIG = {
        API_URL: 'https://your-ngrok-url.ngrok.io', // UPDATE THIS!
        API_KEY: 'the7space_automation_api_key_2024',
        DEBUG: true
    };
    
    // Log function
    function log(message, data = null) {
        if (CONFIG.DEBUG) {
            console.log('[The7Space Integration]', message, data || '');
        }
    }
    
    // Send contact to API
    async function sendContactToAPI(contactData) {
        try {
            log('Sending contact to API:', contactData);
            
            const response = await fetch(CONFIG.API_URL + '/api/the7space/contacts', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer ' + CONFIG.API_KEY
                },
                body: JSON.stringify(contactData)
            });
            
            if (response.ok) {
                const result = await response.json();
                log('Contact sent successfully:', result);
                return true;
            } else {
                log('API Error:', response.status, response.statusText);
                return false;
            }
        } catch (error) {
            log('Network Error:', error);
            return false;
        }
    }
    
    // Extract form data
    function extractFormData(form) {
        const formData = new FormData(form);
        const data = {};
        
        // Common field mappings
        const fieldMappings = {
            'your-name': 'name',
            'your-email': 'email',
            'your-phone': 'phone',
            'your-message': 'message',
            'your-subject': 'subject',
            'name': 'name',
            'email': 'email',
            'phone': 'phone',
            'message': 'message',
            'subject': 'subject',
            'contact-name': 'name',
            'contact-email': 'email',
            'contact-phone': 'phone',
            'contact-message': 'message'
        };
        
        // Extract data using mappings
        for (const [key, value] of formData.entries()) {
            const mappedKey = fieldMappings[key] || key;
            data[mappedKey] = value;
        }
        
        return data;
    }
    
    // Handle Contact Form 7 submissions
    function handleContactForm7() {
        document.addEventListener('wpcf7mailsent', function(event) {
            log('Contact Form 7 submission detected');
            
            const form = event.target;
            const formData = extractFormData(form);
            
            const contactData = {
                business_entity: 'the_7_space',
                lead_source: 'website_contact_form',
                form_type: 'contact_form_7',
                submission_time: new Date().toISOString(),
                name: formData.name || '',
                email: formData.email || '',
                phone: formData.phone || '',
                message: formData.message || '',
                subject: formData.subject || '',
                contact_type: 'general_inquiry'
            };
            
            sendContactToAPI(contactData);
        });
    }
    
    // Handle generic form submissions
    function handleGenericForms() {
        // Look for common contact forms
        const selectors = [
            'form[class*="contact"]',
            'form[id*="contact"]',
            'form[class*="wpcf7"]',
            'form.contact-form',
            '#contact-form',
            '.contact-form'
        ];
        
        selectors.forEach(selector => {
            const forms = document.querySelectorAll(selector);
            forms.forEach(form => {
                form.addEventListener('submit', function(event) {
                    log('Generic form submission detected:', selector);
                    
                    // Don't prevent default - let form submit normally
                    setTimeout(() => {
                        const formData = extractFormData(form);
                        
                        const contactData = {
                            business_entity: 'the_7_space',
                            lead_source: 'website_contact_form',
                            form_type: 'generic_form',
                            submission_time: new Date().toISOString(),
                            name: formData.name || '',
                            email: formData.email || '',
                            phone: formData.phone || '',
                            message: formData.message || '',
                            subject: formData.subject || '',
                            contact_type: 'general_inquiry'
                        };
                        
                        sendContactToAPI(contactData);
                    }, 100);
                });
            });
        });
    }
    
    // Initialize when DOM is ready
    function init() {
        log('The 7 Space Integration initialized');
        log('API URL:', CONFIG.API_URL);
        
        // Test API connection
        fetch(CONFIG.API_URL + '/health')
            .then(response => response.json())
            .then(data => {
                log('API Connection Test:', data);
            })
            .catch(error => {
                log('API Connection Failed:', error);
                console.warn('[The7Space] API connection failed. Please check your API_URL configuration.');
            });
        
        // Set up form handlers
        handleContactForm7();
        handleGenericForms();
    }
    
    // Start when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    
    // Expose for debugging
    window.The7SpaceIntegration = {
        config: CONFIG,
        sendContact: sendContactToAPI,
        log: log
    };
    
})();
