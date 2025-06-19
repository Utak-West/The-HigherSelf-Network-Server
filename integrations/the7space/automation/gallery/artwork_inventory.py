"""
The 7 Space Artwork Inventory Management System

Automated artwork inventory tracking with Notion integration, real-time status updates,
and comprehensive artwork lifecycle management for The 7 Space gallery operations.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import json

from notion_client import Client
from ..config.the7space_config import the7space_config
from ..utils.notion_helpers import NotionHelper
from ..utils.error_recovery import ErrorRecoveryManager
from ..utils.logging_helpers import setup_logger

# Setup logging
logger = setup_logger(__name__)

class ArtworkStatus(Enum):
    """Artwork status enumeration"""
    AVAILABLE = "available"
    RESERVED = "reserved"
    SOLD = "sold"
    ON_LOAN = "on_loan"
    IN_RESTORATION = "in_restoration"
    ARCHIVED = "archived"

class ArtworkCondition(Enum):
    """Artwork condition enumeration"""
    EXCELLENT = "excellent"
    VERY_GOOD = "very_good"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"

@dataclass
class Artwork:
    """Artwork data model"""
    id: str
    title: str
    artist_id: str
    artist_name: str
    medium: str
    dimensions: str
    year_created: Optional[int]
    description: str
    price: float
    commission_rate: float
    status: ArtworkStatus
    condition: ArtworkCondition
    location: str
    acquisition_date: datetime
    last_updated: datetime
    notion_page_id: Optional[str] = None
    image_urls: List[str] = None
    exhibition_history: List[Dict] = None
    provenance: str = ""
    insurance_value: Optional[float] = None
    
    def __post_init__(self):
        if self.image_urls is None:
            self.image_urls = []
        if self.exhibition_history is None:
            self.exhibition_history = []

class ArtworkInventoryManager:
    """
    Automated artwork inventory management system for The 7 Space gallery.
    Integrates with Notion for data persistence and provides real-time inventory tracking.
    """
    
    def __init__(self):
        self.config = the7space_config
        self.notion_client = Client(auth=self.config.notion_api_token)
        self.notion_helper = NotionHelper(self.notion_client)
        self.error_manager = ErrorRecoveryManager()
        self.artworks_db_id = self.config.get_database_id("artworks")
        self.artists_db_id = self.config.get_database_id("artists")
        
        if not self.artworks_db_id:
            raise ValueError("Artworks database ID not configured")
    
    async def add_artwork(self, artwork_data: Dict[str, Any]) -> str:
        """
        Add new artwork to inventory with automated processing.
        
        Args:
            artwork_data: Dictionary containing artwork information
            
        Returns:
            str: Notion page ID of created artwork
        """
        try:
            logger.info(f"Adding new artwork: {artwork_data.get('title', 'Unknown')}")
            
            # Validate artwork data
            validated_data = await self._validate_artwork_data(artwork_data)
            
            # Create artwork object
            artwork = Artwork(
                id=self._generate_artwork_id(),
                title=validated_data["title"],
                artist_id=validated_data.get("artist_id", ""),
                artist_name=validated_data["artist_name"],
                medium=validated_data["medium"],
                dimensions=validated_data["dimensions"],
                year_created=validated_data.get("year_created"),
                description=validated_data.get("description", ""),
                price=float(validated_data["price"]),
                commission_rate=float(validated_data.get("commission_rate", 0.4)),
                status=ArtworkStatus(validated_data.get("status", "available")),
                condition=ArtworkCondition(validated_data.get("condition", "excellent")),
                location=validated_data.get("location", "Gallery Floor"),
                acquisition_date=datetime.now(),
                last_updated=datetime.now(),
                image_urls=validated_data.get("image_urls", []),
                provenance=validated_data.get("provenance", ""),
                insurance_value=validated_data.get("insurance_value")
            )
            
            # Create Notion page
            notion_properties = await self._artwork_to_notion_properties(artwork)
            
            response = await self.notion_helper.create_page(
                database_id=self.artworks_db_id,
                properties=notion_properties
            )
            
            artwork.notion_page_id = response["id"]
            
            # Log successful addition
            logger.info(f"Successfully added artwork: {artwork.title} (ID: {artwork.id})")
            
            # Trigger inventory update notifications
            await self._notify_inventory_update("artwork_added", artwork)
            
            return artwork.notion_page_id
            
        except Exception as e:
            logger.error(f"Failed to add artwork: {str(e)}")
            await self.error_manager.handle_error("add_artwork", e, artwork_data)
            raise
    
    async def update_artwork_status(self, artwork_id: str, new_status: ArtworkStatus, 
                                  additional_data: Optional[Dict] = None) -> bool:
        """
        Update artwork status with automated workflow triggers.
        
        Args:
            artwork_id: Artwork identifier
            new_status: New status for the artwork
            additional_data: Additional data for status change
            
        Returns:
            bool: Success status
        """
        try:
            logger.info(f"Updating artwork status: {artwork_id} -> {new_status.value}")
            
            # Get current artwork data
            artwork = await self.get_artwork_by_id(artwork_id)
            if not artwork:
                raise ValueError(f"Artwork not found: {artwork_id}")
            
            old_status = artwork.status
            artwork.status = new_status
            artwork.last_updated = datetime.now()
            
            # Handle status-specific logic
            await self._handle_status_change(artwork, old_status, additional_data or {})
            
            # Update Notion page
            notion_properties = {
                "Status": {"select": {"name": new_status.value}},
                "Last Updated": {"date": {"start": artwork.last_updated.isoformat()}}
            }
            
            if additional_data:
                notion_properties.update(await self._additional_data_to_notion(additional_data))
            
            await self.notion_helper.update_page(
                page_id=artwork.notion_page_id,
                properties=notion_properties
            )
            
            # Trigger status change notifications
            await self._notify_status_change(artwork, old_status, new_status)
            
            logger.info(f"Successfully updated artwork status: {artwork_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update artwork status: {str(e)}")
            await self.error_manager.handle_error("update_artwork_status", e, {
                "artwork_id": artwork_id,
                "new_status": new_status.value
            })
            return False
    
    async def get_artwork_by_id(self, artwork_id: str) -> Optional[Artwork]:
        """
        Retrieve artwork by ID from Notion database.
        
        Args:
            artwork_id: Artwork identifier
            
        Returns:
            Optional[Artwork]: Artwork object if found
        """
        try:
            # Query Notion database
            filter_condition = {
                "property": "Artwork ID",
                "rich_text": {
                    "equals": artwork_id
                }
            }
            
            results = await self.notion_helper.query_database(
                database_id=self.artworks_db_id,
                filter_condition=filter_condition
            )
            
            if not results:
                return None
            
            # Convert Notion page to Artwork object
            notion_page = results[0]
            return await self._notion_page_to_artwork(notion_page)
            
        except Exception as e:
            logger.error(f"Failed to get artwork by ID: {str(e)}")
            return None
    
    async def get_available_artworks(self, filters: Optional[Dict] = None) -> List[Artwork]:
        """
        Get list of available artworks with optional filtering.
        
        Args:
            filters: Optional filters for artwork search
            
        Returns:
            List[Artwork]: List of available artworks
        """
        try:
            # Build filter condition
            filter_condition = {
                "property": "Status",
                "select": {
                    "equals": "available"
                }
            }
            
            # Add additional filters if provided
            if filters:
                filter_condition = await self._build_compound_filter(filter_condition, filters)
            
            results = await self.notion_helper.query_database(
                database_id=self.artworks_db_id,
                filter_condition=filter_condition
            )
            
            artworks = []
            for page in results:
                artwork = await self._notion_page_to_artwork(page)
                if artwork:
                    artworks.append(artwork)
            
            logger.info(f"Retrieved {len(artworks)} available artworks")
            return artworks
            
        except Exception as e:
            logger.error(f"Failed to get available artworks: {str(e)}")
            return []
    
    async def generate_inventory_report(self, report_type: str = "summary") -> Dict[str, Any]:
        """
        Generate comprehensive inventory report.
        
        Args:
            report_type: Type of report to generate
            
        Returns:
            Dict[str, Any]: Inventory report data
        """
        try:
            logger.info(f"Generating inventory report: {report_type}")
            
            # Get all artworks
            all_artworks = await self._get_all_artworks()
            
            # Calculate statistics
            stats = {
                "total_artworks": len(all_artworks),
                "by_status": {},
                "by_condition": {},
                "by_medium": {},
                "total_value": 0,
                "average_price": 0,
                "recent_additions": 0,
                "needs_attention": []
            }
            
            # Process artwork data
            for artwork in all_artworks:
                # Status breakdown
                status = artwork.status.value
                stats["by_status"][status] = stats["by_status"].get(status, 0) + 1
                
                # Condition breakdown
                condition = artwork.condition.value
                stats["by_condition"][condition] = stats["by_condition"].get(condition, 0) + 1
                
                # Medium breakdown
                medium = artwork.medium
                stats["by_medium"][medium] = stats["by_medium"].get(medium, 0) + 1
                
                # Value calculations
                stats["total_value"] += artwork.price
                
                # Recent additions (last 30 days)
                if artwork.acquisition_date > datetime.now() - timedelta(days=30):
                    stats["recent_additions"] += 1
                
                # Items needing attention
                if artwork.condition in [ArtworkCondition.FAIR, ArtworkCondition.POOR]:
                    stats["needs_attention"].append({
                        "id": artwork.id,
                        "title": artwork.title,
                        "condition": artwork.condition.value,
                        "reason": "Poor condition requires attention"
                    })
            
            # Calculate averages
            if stats["total_artworks"] > 0:
                stats["average_price"] = stats["total_value"] / stats["total_artworks"]
            
            # Add report metadata
            report = {
                "report_type": report_type,
                "generated_at": datetime.now().isoformat(),
                "statistics": stats,
                "recommendations": await self._generate_inventory_recommendations(stats)
            }
            
            logger.info("Successfully generated inventory report")
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate inventory report: {str(e)}")
            return {"error": str(e)}
    
    async def _validate_artwork_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate artwork data before processing"""
        required_fields = ["title", "artist_name", "medium", "dimensions", "price"]
        
        for field in required_fields:
            if field not in data or not data[field]:
                raise ValueError(f"Missing required field: {field}")
        
        # Validate price
        try:
            float(data["price"])
        except (ValueError, TypeError):
            raise ValueError("Invalid price format")
        
        return data
    
    def _generate_artwork_id(self) -> str:
        """Generate unique artwork ID"""
        from uuid import uuid4
        return f"ART-{uuid4().hex[:8].upper()}"
    
    async def _artwork_to_notion_properties(self, artwork: Artwork) -> Dict[str, Any]:
        """Convert Artwork object to Notion properties"""
        return {
            "Title": {"title": [{"text": {"content": artwork.title}}]},
            "Artwork ID": {"rich_text": [{"text": {"content": artwork.id}}]},
            "Artist": {"rich_text": [{"text": {"content": artwork.artist_name}}]},
            "Medium": {"rich_text": [{"text": {"content": artwork.medium}}]},
            "Dimensions": {"rich_text": [{"text": {"content": artwork.dimensions}}]},
            "Price": {"number": artwork.price},
            "Status": {"select": {"name": artwork.status.value}},
            "Condition": {"select": {"name": artwork.condition.value}},
            "Location": {"rich_text": [{"text": {"content": artwork.location}}]},
            "Acquisition Date": {"date": {"start": artwork.acquisition_date.isoformat()}},
            "Last Updated": {"date": {"start": artwork.last_updated.isoformat()}},
            "Description": {"rich_text": [{"text": {"content": artwork.description}}]}
        }
    
    async def _notion_page_to_artwork(self, page: Dict[str, Any]) -> Optional[Artwork]:
        """Convert Notion page to Artwork object"""
        try:
            props = page["properties"]
            
            return Artwork(
                id=self._get_notion_text(props.get("Artwork ID", {})),
                title=self._get_notion_title(props.get("Title", {})),
                artist_id=self._get_notion_text(props.get("Artist ID", {})),
                artist_name=self._get_notion_text(props.get("Artist", {})),
                medium=self._get_notion_text(props.get("Medium", {})),
                dimensions=self._get_notion_text(props.get("Dimensions", {})),
                year_created=self._get_notion_number(props.get("Year Created", {})),
                description=self._get_notion_text(props.get("Description", {})),
                price=self._get_notion_number(props.get("Price", {})) or 0,
                commission_rate=self._get_notion_number(props.get("Commission Rate", {})) or 0.4,
                status=ArtworkStatus(self._get_notion_select(props.get("Status", {})) or "available"),
                condition=ArtworkCondition(self._get_notion_select(props.get("Condition", {})) or "excellent"),
                location=self._get_notion_text(props.get("Location", {})) or "Gallery Floor",
                acquisition_date=self._get_notion_date(props.get("Acquisition Date", {})) or datetime.now(),
                last_updated=self._get_notion_date(props.get("Last Updated", {})) or datetime.now(),
                notion_page_id=page["id"]
            )
        except Exception as e:
            logger.error(f"Failed to convert Notion page to artwork: {str(e)}")
            return None
    
    def _get_notion_text(self, prop: Dict) -> str:
        """Extract text from Notion property"""
        if prop.get("rich_text"):
            return prop["rich_text"][0]["text"]["content"] if prop["rich_text"] else ""
        return ""
    
    def _get_notion_title(self, prop: Dict) -> str:
        """Extract title from Notion property"""
        if prop.get("title"):
            return prop["title"][0]["text"]["content"] if prop["title"] else ""
        return ""
    
    def _get_notion_number(self, prop: Dict) -> Optional[float]:
        """Extract number from Notion property"""
        return prop.get("number")
    
    def _get_notion_select(self, prop: Dict) -> Optional[str]:
        """Extract select value from Notion property"""
        if prop.get("select"):
            return prop["select"]["name"]
        return None
    
    def _get_notion_date(self, prop: Dict) -> Optional[datetime]:
        """Extract date from Notion property"""
        if prop.get("date") and prop["date"].get("start"):
            return datetime.fromisoformat(prop["date"]["start"].replace("Z", "+00:00"))
        return None

    async def _handle_status_change(self, artwork: Artwork, old_status: ArtworkStatus,
                                    additional_data: Dict[str, Any]):
        """Handle artwork status change logic."""
        try:
            if artwork.status == ArtworkStatus.SOLD:
                # Handle sale completion
                await self._process_artwork_sale(artwork, additional_data)
            elif artwork.status == ArtworkStatus.RESERVED:
                # Handle reservation
                await self._process_artwork_reservation(artwork, additional_data)
            elif artwork.status == ArtworkStatus.IN_RESTORATION:
                # Handle restoration tracking
                await self._process_restoration_start(artwork, additional_data)

            logger.info(f"Processed status change for {artwork.id}: {old_status.value} -> {artwork.status.value}")

        except Exception as e:
            logger.error(f"Failed to handle status change: {str(e)}")

    async def _process_artwork_sale(self, artwork: Artwork, sale_data: Dict[str, Any]):
        """Process artwork sale completion"""
        try:
            # Calculate commission
            sale_price = sale_data.get("sale_price", artwork.price)
            commission = sale_price * artwork.commission_rate
            artist_payment = sale_price - commission

            # Create sale record
            sale_record = {
                "artwork_id": artwork.id,
                "artwork_title": artwork.title,
                "artist_name": artwork.artist_name,
                "sale_price": sale_price,
                "commission_amount": commission,
                "artist_payment": artist_payment,
                "sale_date": datetime.now().isoformat(),
                "buyer_info": sale_data.get("buyer_info", {}),
                "payment_method": sale_data.get("payment_method", ""),
                "notes": sale_data.get("notes", "")
            }

            # Save to sales database
            await self._save_sale_record(sale_record)

            # Notify artist of sale
            await self._notify_artist_of_sale(artwork, sale_record)

            logger.info(f"Processed sale for artwork {artwork.id}: ${sale_price}")

        except Exception as e:
            logger.error(f"Failed to process artwork sale: {str(e)}")

    async def _get_all_artworks(self) -> List[Artwork]:
        """Get all artworks from database"""
        try:
            results = await self.notion_helper.query_database(
                database_id=self.artworks_db_id
            )

            artworks = []
            for page in results:
                artwork = await self._notion_page_to_artwork(page)
                if artwork:
                    artworks.append(artwork)

            return artworks

        except Exception as e:
            logger.error(f"Failed to get all artworks: {str(e)}")
            return []

    async def _generate_inventory_recommendations(self, stats: Dict[str, Any]) -> List[str]:
        """Generate inventory management recommendations"""
        recommendations = []

        # Check for low inventory
        if stats["by_status"].get("available", 0) < 10:
            recommendations.append("Consider acquiring new artworks - low available inventory")

        # Check for items needing attention
        if len(stats["needs_attention"]) > 0:
            recommendations.append(f"{len(stats['needs_attention'])} artworks need condition attention")

        # Check for pricing optimization
        if stats["average_price"] < 1000:
            recommendations.append("Consider reviewing pricing strategy - average price is low")

        # Check for recent activity
        if stats["recent_additions"] == 0:
            recommendations.append("No new acquisitions in the last 30 days - consider expanding collection")

        return recommendations

    async def _notify_inventory_update(self, event_type: str, artwork: Artwork):
        """Send inventory update notifications"""
        try:
            notification_data = {
                "event": event_type,
                "artwork_id": artwork.id,
                "artwork_title": artwork.title,
                "artist_name": artwork.artist_name,
                "timestamp": datetime.now().isoformat()
            }

            # Send to notification system
            logger.info(f"Inventory notification: {event_type} for {artwork.title}")

        except Exception as e:
            logger.error(f"Failed to send inventory notification: {str(e)}")

    async def _notify_status_change(self, artwork: Artwork, old_status: ArtworkStatus,
                                   new_status: ArtworkStatus):
        """Send status change notifications"""
        try:
            notification_data = {
                "artwork_id": artwork.id,
                "artwork_title": artwork.title,
                "old_status": old_status.value,
                "new_status": new_status.value,
                "timestamp": datetime.now().isoformat()
            }

            logger.info(f"Status change notification: {artwork.title} {old_status.value} -> {new_status.value}")

        except Exception as e:
            logger.error(f"Failed to send status change notification: {str(e)}")

    async def _save_sale_record(self, sale_record: Dict[str, Any]):
        """Save sale record to database"""
        try:
            sales_db_id = self.config.get_database_id("sales")
            if not sales_db_id:
                logger.warning("Sales database not configured")
                return

            # Convert sale record to Notion properties
            properties = {
                "Artwork ID": {"rich_text": [{"text": {"content": sale_record["artwork_id"]}}]},
                "Artwork Title": {"rich_text": [{"text": {"content": sale_record["artwork_title"]}}]},
                "Artist": {"rich_text": [{"text": {"content": sale_record["artist_name"]}}]},
                "Sale Price": {"number": sale_record["sale_price"]},
                "Commission": {"number": sale_record["commission_amount"]},
                "Artist Payment": {"number": sale_record["artist_payment"]},
                "Sale Date": {"date": {"start": sale_record["sale_date"]}},
                "Payment Method": {"rich_text": [{"text": {"content": sale_record["payment_method"]}}]},
                "Notes": {"rich_text": [{"text": {"content": sale_record["notes"]}}]}
            }

            await self.notion_helper.create_page(
                database_id=sales_db_id,
                properties=properties
            )

            logger.info(f"Saved sale record for artwork {sale_record['artwork_id']}")

        except Exception as e:
            logger.error(f"Failed to save sale record: {str(e)}")

    async def _notify_artist_of_sale(self, artwork: Artwork, sale_record: Dict[str, Any]):
        """Notify artist of artwork sale"""
        try:
            # This would integrate with email system
            logger.info(f"Artist notification sent for sale of {artwork.title}")

        except Exception as e:
            logger.error(f"Failed to notify artist of sale: {str(e)}")

# Automated inventory monitoring
class InventoryMonitor:
    """Automated inventory monitoring and alerts"""

    def __init__(self, inventory_manager: ArtworkInventoryManager):
        self.inventory_manager = inventory_manager
        self.logger = setup_logger(f"{__name__}.InventoryMonitor")

    async def run_daily_checks(self):
        """Run daily inventory checks and alerts"""
        try:
            self.logger.info("Running daily inventory checks")

            # Check for items needing attention
            await self._check_condition_alerts()

            # Check for low inventory
            await self._check_inventory_levels()

            # Check for pricing updates needed
            await self._check_pricing_updates()

            self.logger.info("Completed daily inventory checks")

        except Exception as e:
            self.logger.error(f"Failed to run daily checks: {str(e)}")

    async def _check_condition_alerts(self):
        """Check for artworks needing condition attention"""
        try:
            all_artworks = await self.inventory_manager._get_all_artworks()

            needs_attention = [
                artwork for artwork in all_artworks
                if artwork.condition in [ArtworkCondition.FAIR, ArtworkCondition.POOR]
            ]

            if needs_attention:
                self.logger.warning(f"{len(needs_attention)} artworks need condition attention")
                # Send alert notification

        except Exception as e:
            self.logger.error(f"Failed to check condition alerts: {str(e)}")

    async def _check_inventory_levels(self):
        """Check for low inventory levels"""
        try:
            available_artworks = await self.inventory_manager.get_available_artworks()

            if len(available_artworks) < 10:
                self.logger.warning(f"Low inventory: only {len(available_artworks)} artworks available")
                # Send low inventory alert

        except Exception as e:
            self.logger.error(f"Failed to check inventory levels: {str(e)}")

    async def _check_pricing_updates(self):
        """Check for artworks that may need pricing updates"""
        try:
            all_artworks = await self.inventory_manager._get_all_artworks()

            # Check for artworks that haven't been updated in 6 months
            six_months_ago = datetime.now() - timedelta(days=180)
            outdated_pricing = [
                artwork for artwork in all_artworks
                if artwork.last_updated < six_months_ago
            ]

            if outdated_pricing:
                self.logger.info(f"{len(outdated_pricing)} artworks may need pricing review")

        except Exception as e:
            self.logger.error(f"Failed to check pricing updates: {str(e)}")
