#!/usr/bin/env python3
"""
Architecture Visualization Updater for The HigherSelf Network Server

This script automatically detects services in the codebase and updates the 
architecture visualization HTML file. It ensures that Notion is always 
represented as the central hub for all data and workflows.
"""

import os
import re
import json
from datetime import datetime
import inspect
import importlib.util
from typing import Dict, List, Any, Optional

# Path configurations
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVICES_DIR = os.path.join(BASE_DIR, "services")
ARCHITECTURE_HTML = os.path.join(BASE_DIR, "architecture", "index.html")

# Service information templates
SERVICE_DESCRIPTION_TEMPLATE = {
    "TypeFormService": "Handles form submissions and webhook notifications.",
    "WooCommerceService": "Manages products and orders with Notion integration.",
    "AcuityService": "Handles scheduling and appointment management.",
    "AmeliaService": "Manages bookings and synchronizes with Notion.",
    "UserFeedbackService": "Collects and processes user feedback.",
    "TutorLMService": "Manages AI tutoring functionalities.",
    "AIProviderService": "Routes requests to OpenAI and Anthropic.",
    "IntegrationManager": "Coordinates all service integrations.",
    "NotionService": "Core service that maintains Notion as the central hub.",
}

SERVICE_FUNCTIONS_TEMPLATE = {
    "TypeFormService": [
        "Form submission processing",
        "Webhook handling",
        "Response data synchronization"
    ],
    "WooCommerceService": [
        "Product management",
        "Order processing",
        "Customer data synchronization"
    ],
    "AcuityService": [
        "Appointment creation/updating",
        "Calendar management",
        "Client data synchronization"
    ],
    "AmeliaService": [
        "Booking management",
        "Service provider coordination",
        "Client notification"
    ],
    "UserFeedbackService": [
        "Feedback collection",
        "Sentiment analysis",
        "Response tracking"
    ],
    "TutorLMService": [
        "Session scheduling",
        "Tutor-student matching",
        "Progress tracking"
    ],
    "AIProviderService": [
        "Provider management",
        "Request routing",
        "Response processing"
    ],
    "IntegrationManager": [
        "Service initialization",
        "Notion synchronization",
        "Cross-service operations"
    ],
    "NotionService": [
        "Data synchronization",
        "Page creation and updates",
        "Database management"
    ],
}

class ServiceDetector:
    """
    Detects services in the codebase and extracts their information.
    """
    def __init__(self):
        self.services = []
    
    def scan_services_directory(self) -> List[Dict[str, Any]]:
        """Scan the services directory for service classes."""
        service_files = [f for f in os.listdir(SERVICES_DIR) 
                         if f.endswith('.py') and not f.startswith('__')]
        
        print(f"Found {len(service_files)} potential service files")
        
        for file_name in service_files:
            self._process_service_file(file_name)
        
        # Always ensure Notion service is included and highlighted as central hub
        notion_service_included = any(s['name'] == 'Notion Service' for s in self.services)
        if not notion_service_included:
            self.services.append({
                'name': 'Notion Service',
                'description': 'Core service that maintains Notion as the central hub.',
                'functions': SERVICE_FUNCTIONS_TEMPLATE.get('NotionService', [])
            })
        
        # Always include Integration Manager
        integration_manager_included = any(s['name'] == 'Integration Manager' for s in self.services)
        if not integration_manager_included:
            self.services.append({
                'name': 'Integration Manager',
                'description': 'Coordinates all service integrations.',
                'functions': SERVICE_FUNCTIONS_TEMPLATE.get('IntegrationManager', [])
            })
        
        return self.services
    
    def _process_service_file(self, file_name: str) -> None:
        """Process a single service file to extract service information."""
        file_path = os.path.join(SERVICES_DIR, file_name)
        service_name_match = re.match(r'(.+)_service\.py', file_name)
        
        if not service_name_match:
            return
        
        service_base_name = service_name_match.group(1)
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Check for class definitions that might be services
        class_matches = re.finditer(r'class\s+(\w+)(?:\((\w+)\))?:', content)
        for match in class_matches:
            class_name = match.group(1)
            parent_class = match.group(2)
            
            # Look for classes that inherit from BaseService or have "Service" in their name
            if parent_class == 'BaseService' or 'Service' in class_name:
                name_parts = re.findall(r'[A-Z][a-z0-9]*', class_name)
                display_name = ' '.join(name_parts)
                
                # Extract docstring for description
                docstring_match = re.search(r'class\s+' + class_name + r'[^:]*:\s*"""(.*?)"""', 
                                           content, re.DOTALL)
                description = ""
                if docstring_match:
                    full_docstring = docstring_match.group(1).strip()
                    # Use first sentence or line as description
                    description = full_docstring.split('.')[0].strip()
                
                if not description and class_name in SERVICE_DESCRIPTION_TEMPLATE:
                    description = SERVICE_DESCRIPTION_TEMPLATE[class_name]
                
                # Extract functions based on method definitions
                functions = []
                method_matches = re.finditer(r'def\s+(\w+)\s*\([^)]*\):\s*"""([^"]*)"""', content)
                for method_match in method_matches:
                    method_name = method_match.group(1)
                    method_desc = method_match.group(2).strip().split('.')[0]
                    if method_name not in ('__init__', '_get_headers', '_verify_webhook_signature'):
                        functions.append(method_desc or method_name.replace('_', ' '))
                
                # Use template functions if we couldn't extract meaningful ones
                if not functions and class_name in SERVICE_FUNCTIONS_TEMPLATE:
                    functions = SERVICE_FUNCTIONS_TEMPLATE[class_name]
                
                # Limit to top 3 functions
                functions = functions[:3]
                
                # Add service to our list
                self.services.append({
                    'name': display_name,
                    'description': description,
                    'functions': functions
                })
                
                print(f"Detected service: {display_name}")


class ArchitectureUpdater:
    """
    Updates the architecture visualization based on detected services.
    """
    def __init__(self, services: List[Dict[str, Any]]):
        self.services = services
    
    def update_html(self) -> bool:
        """Update the architecture HTML file with the current services."""
        try:
            with open(ARCHITECTURE_HTML, 'r') as f:
                content = f.read()
            
            # Update the services JavaScript array
            services_json = json.dumps(self.services, indent=4)
            updated_content = re.sub(
                r'const serviceDefinitions = \[[\s\S]*?\];',
                f'const serviceDefinitions = {services_json};',
                content
            )
            
            # Update the timestamp
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            updated_content = re.sub(
                r'<span id="updateTimestamp">.*?</span>',
                f'<span id="updateTimestamp">{timestamp}</span>',
                updated_content
            )
            
            with open(ARCHITECTURE_HTML, 'w') as f:
                f.write(updated_content)
            
            print(f"Updated architecture visualization with {len(self.services)} services")
            return True
        except Exception as e:
            print(f"Error updating architecture visualization: {e}")
            return False


def main():
    """Main function to detect services and update visualization."""
    print("Starting architecture visualization update...")
    
    # Detect services
    detector = ServiceDetector()
    services = detector.scan_services_directory()
    
    # Update visualization
    updater = ArchitectureUpdater(services)
    success = updater.update_html()
    
    if success:
        print("Successfully updated architecture visualization!")
    else:
        print("Failed to update architecture visualization.")


if __name__ == "__main__":
    main()