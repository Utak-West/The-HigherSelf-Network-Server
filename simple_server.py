#!/usr/bin/env python3
"""
Simple test server for The 7 Space WordPress integration
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uvicorn
import json
from datetime import datetime

app = FastAPI(
    title="The 7 Space Automation Server",
    description="Simple test server for WordPress integration",
    version="1.0.0"
)

# Enable CORS for WordPress integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your WordPress domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple in-memory storage for testing
contacts_db = []
api_keys = {
    "the7space_automation_api_key_2024": {
        "name": "WordPress Integration",
        "created": datetime.now().isoformat(),
        "business_entity": "the_7_space"
    }
}

class ContactSubmission(BaseModel):
    business_entity: str
    lead_source: str
    form_type: str
    submission_time: str
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    message: Optional[str] = None
    subject: Optional[str] = None
    interest: Optional[str] = None
    contact_type: Optional[str] = "general_inquiry"

@app.get("/")
async def root():
    return {
        "message": "The 7 Space Automation Server",
        "status": "running",
        "version": "1.0.0",
        "business_entity": "the_7_space",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "The 7 Space Automation Server",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "uptime": "running",
        "business_entity": "the_7_space"
    }

@app.post("/api/the7space/contacts")
async def submit_contact(contact: ContactSubmission):
    """
    Receive contact form submissions from WordPress
    """
    try:
        # Validate required fields
        if not contact.email:
            raise HTTPException(status_code=400, detail="Email is required")
        
        # Add timestamp and ID
        contact_data = contact.dict()
        contact_data["id"] = len(contacts_db) + 1
        contact_data["received_at"] = datetime.now().isoformat()
        contact_data["status"] = "received"
        
        # Store contact
        contacts_db.append(contact_data)
        
        # Log the contact submission
        print(f"📧 New contact received from {contact.name} ({contact.email})")
        print(f"   Form Type: {contact.form_type}")
        print(f"   Message: {contact.message[:100]}..." if contact.message else "   No message")
        print(f"   Contact Type: {contact.contact_type}")
        
        return {
            "status": "success",
            "message": "Contact received successfully",
            "contact_id": contact_data["id"],
            "business_entity": contact.business_entity,
            "timestamp": contact_data["received_at"]
        }
        
    except Exception as e:
        print(f"❌ Error processing contact: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing contact: {str(e)}")

@app.get("/api/the7space/contacts/recent")
async def get_recent_contacts(limit: int = 10):
    """
    Get recent contact submissions
    """
    recent_contacts = contacts_db[-limit:] if contacts_db else []
    return {
        "status": "success",
        "contacts": recent_contacts,
        "total_count": len(contacts_db),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/the7space/contacts/{contact_id}")
async def get_contact(contact_id: int):
    """
    Get a specific contact by ID
    """
    for contact in contacts_db:
        if contact["id"] == contact_id:
            return {
                "status": "success",
                "contact": contact,
                "timestamp": datetime.now().isoformat()
            }
    
    raise HTTPException(status_code=404, detail="Contact not found")

@app.get("/api/the7space/workflows/status")
async def get_workflow_status():
    """
    Get workflow automation status
    """
    return {
        "status": "active",
        "workflows": {
            "contact_processing": "enabled",
            "email_automation": "enabled",
            "notion_sync": "enabled",
            "gallery_sync": "enabled",
            "wellness_booking": "enabled"
        },
        "processed_contacts": len(contacts_db),
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/the7space/generate-api-key")
async def generate_api_key(name: str = "WordPress Integration"):
    """
    Generate a new API key for WordPress integration
    """
    api_key = "the7space_automation_api_key_2024"
    api_keys[api_key] = {
        "name": name,
        "created": datetime.now().isoformat(),
        "business_entity": "the_7_space"
    }
    
    return {
        "status": "success",
        "api_key": api_key,
        "name": name,
        "created": api_keys[api_key]["created"],
        "message": "API key generated successfully"
    }

@app.get("/api/the7space/stats")
async def get_stats():
    """
    Get basic statistics
    """
    contact_types = {}
    for contact in contacts_db:
        contact_type = contact.get("contact_type", "unknown")
        contact_types[contact_type] = contact_types.get(contact_type, 0) + 1
    
    return {
        "status": "success",
        "stats": {
            "total_contacts": len(contacts_db),
            "contact_types": contact_types,
            "api_keys_active": len(api_keys),
            "server_uptime": "running"
        },
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    print("🚀 Starting The 7 Space Automation Server...")
    print("📧 Ready to receive WordPress contact form submissions")
    print("🔗 WordPress Integration URL: http://localhost:8000")
    print("🔑 API Key: the7space_automation_api_key_2024")
    print("👤 WordPress Username: utak@the7space.com")
    print("🔐 WordPress App Password: hZKd OEjZ w07V K64h CtVw MFdC")
    print("=" * 60)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
