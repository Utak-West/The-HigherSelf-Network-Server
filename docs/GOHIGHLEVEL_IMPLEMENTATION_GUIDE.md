# GoHighLevel Implementation Guide
## Technical Specifications for 7-Business Portfolio Integration

### **IMPLEMENTATION OVERVIEW**

**Objective**: Integrate GoHighLevel CRM with The HigherSelf Network Server's 7-business portfolio using Agency Unlimited Plan with 5 sub-account architecture.

**Technical Stack**:
- **GoHighLevel API v2**: OAuth 2.0, REST endpoints, webhooks
- **Rate Limits**: 100 requests/10 seconds, 200,000/day
- **Authentication**: OAuth 2.0 with refresh token rotation
- **Webhook Security**: HMAC-SHA256 signature verification

---

### **SUB-ACCOUNT ARCHITECTURE**

#### **GoHighLevel Sub-Account Structure**
```
HigherSelf Network (Master Agency Account)
├── Core Business Hub (Sub-Account 1)
│   ├── Art Gallery
│   ├── Wellness Center  
│   └── Consultancy
├── Home Services Hub (Sub-Account 2)
│   ├── Interior Design
│   ├── Luxury Renovations
│   └── Wellness Home Design
├── Extended Wellness Hub (Sub-Account 3)
│   ├── Executive Wellness Coaching
│   ├── Corporate Wellness Programs
│   └── Luxury Spa Services
├── Development/Testing (Sub-Account 4)
└── Analytics/Reporting (Sub-Account 5)
```

#### **Environment Variables Required**
```bash
# GoHighLevel Master Configuration
GOHIGHLEVEL_CLIENT_ID=your_client_id
GOHIGHLEVEL_CLIENT_SECRET=your_client_secret
GOHIGHLEVEL_REDIRECT_URI=https://your-domain.com/auth/gohighlevel/callback
GOHIGHLEVEL_WEBHOOK_SECRET=your_webhook_secret
GOHIGHLEVEL_SCOPE=contacts.read contacts.write opportunities.read opportunities.write campaigns.read campaigns.write calendars.read calendars.write

# Sub-Account Specific Tokens
GOHIGHLEVEL_CORE_BUSINESS_TOKEN=core_business_access_token
GOHIGHLEVEL_HOME_SERVICES_TOKEN=home_services_access_token
GOHIGHLEVEL_EXTENDED_WELLNESS_TOKEN=extended_wellness_access_token
GOHIGHLEVEL_DEVELOPMENT_TOKEN=development_access_token
GOHIGHLEVEL_ANALYTICS_TOKEN=analytics_access_token

# Sub-Account Location IDs
GOHIGHLEVEL_CORE_BUSINESS_LOCATION=core_location_id
GOHIGHLEVEL_HOME_SERVICES_LOCATION=home_services_location_id
GOHIGHLEVEL_EXTENDED_WELLNESS_LOCATION=extended_wellness_location_id
```

---

### **BUSINESS-SPECIFIC PIPELINE CONFIGURATIONS**

#### **Art Gallery Pipeline**
```python
art_gallery_pipeline = {
    "name": "Art Gallery Sales Pipeline",
    "stages": [
        {"name": "Initial Inquiry", "position": 1},
        {"name": "Gallery Visit Scheduled", "position": 2},
        {"name": "Artwork Interest Identified", "position": 3},
        {"name": "Price Discussion", "position": 4},
        {"name": "Purchase Decision", "position": 5},
        {"name": "Sale Completed", "position": 6},
        {"name": "Cross-Sell Opportunity", "position": 7}
    ],
    "custom_fields": {
        "artwork_interest": {"type": "multi_select", "options": ["Paintings", "Sculptures", "Photography", "Mixed Media"]},
        "budget_range": {"type": "dropdown", "options": ["$1K-5K", "$5K-15K", "$15K-50K", "$50K+"]},
        "collector_type": {"type": "radio", "options": ["New Collector", "Experienced Collector", "Investment Buyer"]},
        "interior_design_interest": {"type": "radio", "options": ["Yes", "No", "Maybe"]}
    }
}
```

#### **Executive Wellness Coaching Pipeline**
```python
executive_wellness_pipeline = {
    "name": "Executive Wellness Coaching Pipeline",
    "stages": [
        {"name": "Executive Assessment", "position": 1},
        {"name": "Wellness Audit Completed", "position": 2},
        {"name": "Program Proposal", "position": 3},
        {"name": "Enrollment", "position": 4},
        {"name": "Coaching Active", "position": 5},
        {"name": "Program Completion", "position": 6},
        {"name": "Corporate Program Upsell", "position": 7}
    ],
    "custom_fields": {
        "executive_level": {"type": "dropdown", "options": ["C-Suite", "VP", "Director", "Manager"]},
        "wellness_goals": {"type": "multi_select", "options": ["Stress Management", "Performance", "Work-Life Balance", "Leadership"]},
        "company_size": {"type": "dropdown", "options": ["1-50", "51-200", "201-1000", "1000+"]},
        "corporate_program_interest": {"type": "radio", "options": ["High", "Medium", "Low"]}
    }
}
```

#### **Luxury Home Renovations Pipeline**
```python
luxury_renovations_pipeline = {
    "name": "Luxury Home Renovations Pipeline",
    "stages": [
        {"name": "Project Inquiry", "position": 1},
        {"name": "Site Assessment Scheduled", "position": 2},
        {"name": "Design Consultation", "position": 3},
        {"name": "Detailed Quote", "position": 4},
        {"name": "Contract Negotiation", "position": 5},
        {"name": "Project Kickoff", "position": 6},
        {"name": "Construction Phase", "position": 7},
        {"name": "Project Completion", "position": 8}
    ],
    "custom_fields": {
        "project_type": {"type": "multi_select", "options": ["Kitchen", "Bathroom", "Whole House", "Addition", "Wellness Space"]},
        "project_budget": {"type": "dropdown", "options": ["$50K-100K", "$100K-250K", "$250K-500K", "$500K+"]},
        "timeline": {"type": "dropdown", "options": ["Immediate", "1-3 months", "3-6 months", "6+ months"]},
        "wellness_integration": {"type": "radio", "options": ["Yes", "No", "Considering"]}
    }
}
```

---

### **CROSS-BUSINESS AUTOMATION WORKFLOWS**

#### **High-Net-Worth Customer Journey Automation**
```python
hnw_customer_workflow = {
    "trigger": "art_gallery_purchase_over_25k",
    "workflow_name": "High-Net-Worth Customer Journey",
    "steps": [
        {
            "delay": "3 days",
            "action": "send_email",
            "template": "art_purchase_thank_you_with_interior_design_offer",
            "business_cross_sell": "interior_design"
        },
        {
            "delay": "1 week", 
            "condition": "email_opened",
            "action": "create_task",
            "assigned_to": "interior_design_consultant",
            "task": "Follow up on interior design interest"
        },
        {
            "delay": "2 weeks",
            "condition": "no_response",
            "action": "add_to_nurture_sequence",
            "sequence": "luxury_lifestyle_nurture"
        },
        {
            "delay": "1 month",
            "action": "send_executive_wellness_offer",
            "condition": "business_owner_tag_present"
        }
    ]
}
```

#### **Corporate Executive Cross-Sell Automation**
```python
corporate_executive_workflow = {
    "trigger": "consultancy_project_completion",
    "workflow_name": "Corporate Executive Cross-Sell",
    "steps": [
        {
            "delay": "1 week",
            "action": "send_success_celebration_email",
            "template": "consultancy_success_with_wellness_offer"
        },
        {
            "delay": "2 weeks",
            "condition": "email_engaged",
            "action": "offer_executive_wellness_assessment",
            "business_cross_sell": "executive_wellness"
        },
        {
            "delay": "1 month", 
            "condition": "executive_wellness_enrolled",
            "action": "offer_corporate_wellness_program",
            "business_cross_sell": "corporate_wellness"
        }
    ]
}
```

---

### **AI AGENT ENHANCEMENT SPECIFICATIONS**

#### **Nyra (Lead Capture Specialist) - Enhanced Capabilities**
```python
class EnhancedNyra(Nyra):
    """Enhanced Nyra for 7-business lead capture and routing."""
    
    async def process_multi_business_lead(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process leads with cross-business intelligence."""
        
        # Determine primary business interest
        primary_business = await self.classify_business_interest(lead_data)
        
        # Create contact in appropriate GoHighLevel sub-account
        sub_account = self.get_sub_account_for_business(primary_business)
        ghl_contact = await self.gohighlevel_service.create_contact(
            lead_data, sub_account=sub_account
        )
        
        # Analyze cross-sell potential
        cross_sell_opportunities = await self.analyze_cross_sell_potential(lead_data)
        
        # Create opportunities in relevant pipelines
        for opportunity in cross_sell_opportunities:
            await self.gohighlevel_service.create_opportunity({
                "contact_id": ghl_contact.id,
                "pipeline_id": opportunity["pipeline_id"],
                "name": f"{opportunity['business_type']} - {lead_data['name']}",
                "value": opportunity["estimated_value"]
            })
        
        # Sync to Notion with cross-business tags
        await self.sync_to_notion_with_cross_business_data(
            lead_data, ghl_contact.id, cross_sell_opportunities
        )
        
        return {
            "status": "success",
            "primary_business": primary_business,
            "cross_sell_opportunities": len(cross_sell_opportunities),
            "ghl_contact_id": ghl_contact.id
        }
```

#### **Solari (Booking & Project Manager) - Enhanced Capabilities**
```python
class EnhancedSolari(Solari):
    """Enhanced Solari for multi-business project and appointment management."""
    
    async def coordinate_cross_business_projects(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate projects that span multiple businesses."""
        
        # Example: Luxury renovation with wellness space and art display
        if project_data["type"] == "luxury_renovation_with_wellness":
            # Schedule renovation consultation
            renovation_appointment = await self.gohighlevel_service.create_appointment({
                "contact_id": project_data["contact_id"],
                "calendar_id": self.get_calendar_id("luxury_renovations"),
                "appointment_type": "renovation_consultation"
            })
            
            # Schedule wellness space design consultation
            wellness_appointment = await self.gohighlevel_service.create_appointment({
                "contact_id": project_data["contact_id"], 
                "calendar_id": self.get_calendar_id("wellness_home_design"),
                "appointment_type": "wellness_space_consultation"
            })
            
            # Create coordinated project timeline
            await self.create_multi_business_project_timeline([
                renovation_appointment, wellness_appointment
            ])
            
        return {"status": "coordinated", "appointments_created": 2}
```

---

### **OAUTH 2.0 IMPLEMENTATION REQUIREMENTS**

#### **Token Management Strategy**
```python
class GoHighLevelOAuthManager:
    """Manages OAuth 2.0 tokens for multiple sub-accounts."""
    
    def __init__(self, redis_client, mongodb_client):
        self.redis = redis_client
        self.mongodb = mongodb_client
        self.token_refresh_threshold = 300  # 5 minutes before expiry
    
    async def get_valid_token(self, sub_account: str) -> str:
        """Get valid access token for sub-account, refreshing if necessary."""
        
        # Check Redis cache first
        cached_token = await self.redis.get(f"ghl:token:{sub_account}")
        if cached_token and not await self.is_token_expired(cached_token):
            return cached_token
        
        # Refresh token if expired or missing
        refresh_token = await self.get_refresh_token(sub_account)
        new_tokens = await self.refresh_access_token(refresh_token)
        
        # Cache new token
        await self.redis.setex(
            f"ghl:token:{sub_account}",
            new_tokens["expires_in"] - self.token_refresh_threshold,
            new_tokens["access_token"]
        )
        
        # Store refresh token securely
        await self.store_refresh_token(sub_account, new_tokens["refresh_token"])
        
        return new_tokens["access_token"]
```

---

### **WEBHOOK PROCESSING ARCHITECTURE**

#### **Webhook Routing Strategy**
```python
webhook_routing_map = {
    "contact.created": {
        "handler": "process_new_contact",
        "agents": ["Nyra"],
        "cross_business_analysis": True
    },
    "opportunity.stage_changed": {
        "handler": "process_opportunity_update", 
        "agents": ["Liora", "Ruvo"],
        "trigger_cross_sell": True
    },
    "appointment.scheduled": {
        "handler": "process_appointment",
        "agents": ["Solari"],
        "coordinate_multi_business": True
    },
    "campaign.completed": {
        "handler": "process_campaign_completion",
        "agents": ["Liora", "Zevi"],
        "analyze_cross_business_impact": True
    }
}
```

This implementation guide provides the technical foundation for AI assistants to build the comprehensive GoHighLevel integration while maintaining the existing codebase patterns and achieving the projected $4.8M revenue target.
