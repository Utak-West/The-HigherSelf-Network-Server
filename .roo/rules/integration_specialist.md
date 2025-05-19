# HigherSelf Integration Specialist

## Description
Specialized mode for developing and maintaining integrations between Notion, Airtable, and other services

## Instructions
- Focus on bidirectional sync between Notion and Airtable
- Implement proper error handling and retry logic
- Use Pydantic models for data validation
- Ensure proper rate limit handling
- Implement logging for all API operations
- Create data transformations between systems
- Maintain configuration in environment variables

## Capabilities
- Analyze API documentation
- Generate integration code
- Create Pydantic models for data validation
- Implement webhook handlers
- Design efficient data synchronization patterns

## Integration Template

```python
"""
{integration_name} Integration for The HigherSelf Network Server.

This module provides integration between {source_system} and {target_system},
ensuring data consistency and synchronization.
"""

import os
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field

from loguru import logger
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Define Pydantic models for data validation

class {source_system}Record(BaseModel):
    """Data model for {source_system} records."""
    id: str = Field(..., description="Unique identifier")
    name: str = Field(..., description="Record name")
    # Add additional fields as needed
    
class {target_system}Record(BaseModel):
    """Data model for {target_system} records."""
    record_id: str = Field(..., description="Unique identifier")
    record_name: str = Field(..., description="Record name")
    # Add additional fields as needed
    last_updated: str = Field(..., description="Last update timestamp")

# Define transformation functions

def transform_{source_system}_to_{target_system}(source_record: {source_system}Record) -> {target_system}Record:
    """
    Transform a {source_system} record to a {target_system} record.
    
    Args:
        source_record: The source record to transform
        
    Returns:
        Transformed record for the target system
    """
    return {target_system}Record(
        record_id=source_record.id,
        record_name=source_record.name,
        # Map additional fields
        last_updated=datetime.now().isoformat()
    )

# Define synchronization functions

async def sync_{source_system}_to_{target_system}(
    source_client, 
    target_client,
    last_sync_time: Optional[datetime] = None
) -> Dict[str, Any]:
    """
    Synchronize records from {source_system} to {target_system}.
    
    Args:
        source_client: Client for the source system
        target_client: Client for the target system
        last_sync_time: Optional timestamp of last synchronization
        
    Returns:
        Dict containing synchronization results
    """
    try:
        # Fetch records from source system
        # Transform records
        # Update target system
        # Log results
        
        return {
            "status": "success",
            "records_processed": 0,
            "records_created": 0,
            "records_updated": 0,
            "records_failed": 0,
            "sync_time": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error synchronizing {source_system} to {target_system}: {e}")
        return {
            "status": "error",
            "error": str(e),
            "sync_time": datetime.now().isoformat()
        }

# Main synchronization function

async def run_sync(
    bidirectional: bool = False,
    force_full_sync: bool = False
) -> Dict[str, Any]:
    """
    Run the synchronization process.
    
    Args:
        bidirectional: Whether to sync in both directions
        force_full_sync: Whether to force a full sync regardless of last sync time
        
    Returns:
        Dict containing overall synchronization results
    """
    results = {}
    
    # Initialize clients
    source_client = None  # Initialize source client
    target_client = None  # Initialize target client
    
    # Get last sync time
    last_sync_time = None  # Get from persistent storage
    
    # Sync source to target
    results["source_to_target"] = await sync_{source_system}_to_{target_system}(
        source_client,
        target_client,
        last_sync_time
    )
    
    # Optionally sync target to source
    if bidirectional:
        results["target_to_source"] = await sync_{target_system}_to_{source_system}(
            target_client,
            source_client,
            last_sync_time
        )
    
    # Store last sync time
    # Update persistent storage with current time
    
    return results
```

## Key Integrations

### Notion-Airtable Integration
- Primary purpose: Operational dashboards and reporting
- Key databases: Master Tasks, Workflow Instances, Contacts
- Sync frequency: Every 15 minutes
- Direction: Bidirectional with conflict resolution

### Notion-WooCommerce Integration
- Primary purpose: Order management and product inventory
- Key databases: Products, Orders, Customers
- Sync frequency: Near real-time (webhook-driven)
- Direction: Bidirectional with WooCommerce as source of truth for orders

### Notion-Amelia Integration
- Primary purpose: Booking management
- Key databases: Services, Appointments, Customers
- Sync frequency: Near real-time (webhook-driven)
- Direction: Bidirectional with Amelia as source of truth for appointments

### Notion-Circle.so Integration
- Primary purpose: Community engagement tracking
- Key databases: Community Members, Spaces, Events
- Sync frequency: Hourly
- Direction: Primarily Circle.so to Notion with limited write-back

### Notion-Beehiiv Integration
- Primary purpose: Email marketing campaign management
- Key databases: Campaigns, Subscribers, Content
- Sync frequency: Daily with webhook triggers for specific events
- Direction: Primarily Notion to Beehiiv with subscriber sync back to Notion
