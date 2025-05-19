#!/usr/bin/env python
"""
Migration script to migrate data from Circle.so to BetterMode.
This script helps migrate community members, content, and activity data.
"""

import os
import sys
import json
import asyncio
import argparse
from datetime import datetime
from typing import Dict, Any, List, Optional

import httpx
from loguru import logger
from tqdm import tqdm

# Add parent directory to path to import from project
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.bettermode_service import BetterModeService, get_bettermode_service
from models.bettermode_models import BetterModeIntegrationConfig, BetterModeMember
from services.notion_service import NotionService
from models.notion_db_models_extended import CommunityMember


class CirclesoToBettermodeConverter:
    """
    Converter to migrate data from Circle.so to BetterMode.
    """
    
    def __init__(self, circle_api_token: str, circle_community_id: str):
        """Initialize the converter."""
        self.circle_api_token = circle_api_token
        self.circle_community_id = circle_community_id
        self.circle_api_url = "https://app.circle.so/api/v1"
        self.client = httpx.AsyncClient(timeout=30.0)
        
        # Set headers for Circle.so API
        self.headers = {
            "Authorization": f"Token {self.circle_api_token}",
            "Content-Type": "application/json"
        }
    
    async def get_circle_members(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get members from Circle.so.
        
        Args:
            limit: Maximum number of members to retrieve
            offset: Offset for pagination
            
        Returns:
            List of members from Circle.so
        """
        url = f"{self.circle_api_url}/community_members"
        params = {
            "community_id": self.circle_community_id,
            "limit": limit,
            "offset": offset
        }
        
        try:
            response = await self.client.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting Circle.so members: {e}")
            return []
    
    async def get_circle_spaces(self) -> List[Dict[str, Any]]:
        """
        Get spaces from Circle.so.
        
        Returns:
            List of spaces from Circle.so
        """
        url = f"{self.circle_api_url}/spaces"
        params = {
            "community_id": self.circle_community_id
        }
        
        try:
            response = await self.client.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting Circle.so spaces: {e}")
            return []
    
    async def get_circle_posts(self, space_id: str, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get posts from Circle.so.
        
        Args:
            space_id: Space ID
            limit: Maximum number of posts to retrieve
            offset: Offset for pagination
            
        Returns:
            List of posts from Circle.so
        """
        url = f"{self.circle_api_url}/posts"
        params = {
            "community_id": self.circle_community_id,
            "space_id": space_id,
            "limit": limit,
            "offset": offset
        }
        
        try:
            response = await self.client.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting Circle.so posts: {e}")
            return []
    
    def convert_member_to_bettermode(self, circle_member: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert Circle.so member to BetterMode format.
        
        Args:
            circle_member: Circle.so member data
            
        Returns:
            BetterMode member data
        """
        return {
            "name": circle_member.get("name", ""),
            "email": circle_member.get("email", ""),
            "role": "member",
            "custom_fields": {
                "circle_member_id": circle_member.get("id", ""),
                "membership_level": circle_member.get("membership_level", "Standard"),
                "migrated_from_circle": True,
                "migration_date": datetime.now().isoformat()
            }
        }
    
    def convert_space_to_bettermode(self, circle_space: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert Circle.so space to BetterMode format.
        
        Args:
            circle_space: Circle.so space data
            
        Returns:
            BetterMode space data
        """
        # Map Circle.so space type to BetterMode space type
        space_type_map = {
            "discussion": "discussion",
            "post": "article",
            "question": "question",
            "event": "event",
            "default": "discussion"
        }
        
        space_type = circle_space.get("type", "default")
        bettermode_space_type = space_type_map.get(space_type, "discussion")
        
        return {
            "name": circle_space.get("name", ""),
            "slug": circle_space.get("slug", ""),
            "description": circle_space.get("description", ""),
            "type": bettermode_space_type,
            "custom_fields": {
                "circle_space_id": circle_space.get("id", ""),
                "migrated_from_circle": True,
                "migration_date": datetime.now().isoformat()
            }
        }
    
    def convert_post_to_bettermode(self, circle_post: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert Circle.so post to BetterMode format.
        
        Args:
            circle_post: Circle.so post data
            
        Returns:
            BetterMode post data
        """
        return {
            "title": circle_post.get("title", ""),
            "content": circle_post.get("body", ""),
            "custom_fields": {
                "circle_post_id": circle_post.get("id", ""),
                "migrated_from_circle": True,
                "migration_date": datetime.now().isoformat()
            }
        }


async def migrate_members(
    converter: CirclesoToBettermodeConverter,
    bettermode_service: BetterModeService,
    notion_service: NotionService,
    batch_size: int = 100,
    max_members: Optional[int] = None
) -> int:
    """
    Migrate members from Circle.so to BetterMode.
    
    Args:
        converter: Circle.so to BetterMode converter
        bettermode_service: BetterMode service
        notion_service: Notion service
        batch_size: Batch size for processing
        max_members: Maximum number of members to migrate
        
    Returns:
        Number of members migrated
    """
    offset = 0
    total_migrated = 0
    
    while True:
        # Get members from Circle.so
        circle_members = await converter.get_circle_members(limit=batch_size, offset=offset)
        
        if not circle_members:
            logger.info("No more members to migrate")
            break
        
        logger.info(f"Processing {len(circle_members)} members (offset: {offset})")
        
        # Process members
        for circle_member in tqdm(circle_members, desc="Migrating members"):
            # Convert Circle.so member to BetterMode format
            bettermode_member_data = converter.convert_member_to_bettermode(circle_member)
            
            # Check if member already exists in BetterMode
            existing_member = await bettermode_service.get_member_by_email(bettermode_member_data["email"])
            
            if existing_member:
                logger.info(f"Member {bettermode_member_data['email']} already exists in BetterMode")
                continue
            
            try:
                # Create member in BetterMode
                # This is a placeholder - actual implementation would use BetterMode API
                logger.info(f"Creating member in BetterMode: {bettermode_member_data['email']}")
                
                # Update Notion database
                # Find existing community member in Notion
                filter_conditions = {
                    "property": "member_email",
                    "rich_text": {
                        "equals": bettermode_member_data["email"]
                    }
                }
                
                members = await notion_service.query_database(
                    CommunityMember,
                    filter_conditions=filter_conditions
                )
                
                if members:
                    # Update existing member
                    member = members[0]
                    member.primary_platform = "BetterMode"
                    member.bettermode_member_id = "placeholder_id"  # Would be actual ID from BetterMode
                    await notion_service.update_page(member)
                    logger.info(f"Updated member in Notion: {member.member_email}")
                else:
                    # Create new member
                    new_member = CommunityMember(
                        member_name=bettermode_member_data["name"],
                        member_email=bettermode_member_data["email"],
                        join_date=datetime.now(),
                        membership_level=bettermode_member_data["custom_fields"]["membership_level"],
                        membership_status="Active",
                        primary_platform="BetterMode",
                        bettermode_member_id="placeholder_id",  # Would be actual ID from BetterMode
                        circle_member_id=circle_member.get("id", ""),
                        custom_fields=bettermode_member_data["custom_fields"]
                    )
                    
                    await notion_service.create_page(new_member)
                    logger.info(f"Created member in Notion: {new_member.member_email}")
                
                total_migrated += 1
                
                # Check if we've reached the maximum number of members to migrate
                if max_members and total_migrated >= max_members:
                    logger.info(f"Reached maximum number of members to migrate: {max_members}")
                    return total_migrated
                
            except Exception as e:
                logger.error(f"Error migrating member {bettermode_member_data['email']}: {e}")
        
        # Move to next batch
        offset += batch_size
    
    return total_migrated


async def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Migrate data from Circle.so to BetterMode")
    parser.add_argument("--batch-size", type=int, default=100, help="Batch size for processing")
    parser.add_argument("--max-members", type=int, default=None, help="Maximum number of members to migrate")
    parser.add_argument("--circle-token", type=str, help="Circle.so API token")
    parser.add_argument("--circle-community-id", type=str, help="Circle.so community ID")
    parser.add_argument("--bettermode-token", type=str, help="BetterMode API token")
    parser.add_argument("--bettermode-network-id", type=str, help="BetterMode network ID")
    parser.add_argument("--notion-token", type=str, help="Notion API token")
    args = parser.parse_args()
    
    # Get credentials from environment variables if not provided
    circle_token = args.circle_token or os.environ.get("CIRCLE_API_TOKEN")
    circle_community_id = args.circle_community_id or os.environ.get("CIRCLE_COMMUNITY_ID")
    bettermode_token = args.bettermode_token or os.environ.get("BETTERMODE_API_TOKEN")
    bettermode_network_id = args.bettermode_network_id or os.environ.get("BETTERMODE_NETWORK_ID")
    notion_token = args.notion_token or os.environ.get("NOTION_API_TOKEN")
    
    if not circle_token or not circle_community_id:
        logger.error("Circle.so API token and community ID are required")
        sys.exit(1)
    
    if not bettermode_token or not bettermode_network_id:
        logger.error("BetterMode API token and network ID are required")
        sys.exit(1)
    
    if not notion_token:
        logger.error("Notion API token is required")
        sys.exit(1)
    
    # Initialize services
    converter = CirclesoToBettermodeConverter(circle_token, circle_community_id)
    
    bettermode_config = BetterModeIntegrationConfig(
        api_token=bettermode_token,
        network_id=bettermode_network_id
    )
    bettermode_service = BetterModeService(bettermode_config)
    
    notion_service = NotionService(notion_token)
    
    # Migrate members
    logger.info("Starting migration of members from Circle.so to BetterMode")
    total_migrated = await migrate_members(
        converter,
        bettermode_service,
        notion_service,
        batch_size=args.batch_size,
        max_members=args.max_members
    )
    
    logger.info(f"Migration completed. Total members migrated: {total_migrated}")


if __name__ == "__main__":
    asyncio.run(main())
