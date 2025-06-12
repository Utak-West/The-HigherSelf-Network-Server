#!/usr/bin/env python3
"""
HigherSelf Network Barter System Demo Script.

This script demonstrates the complete functionality of the barter system
including creating profiles, listings, requests, finding matches, and managing transactions.
"""

import asyncio
import json
from datetime import datetime, timezone
from uuid import uuid4

from config.barter_config import get_barter_config
from models.barter_models import (
    BarterListing,
    BarterProfile,
    BarterRequest,
    CulturalRegion,
    Location,
    ServiceCategory,
    SkillLevel,
)
from services.barter_notification_service import BarterNotificationService
from services.barter_service import BarterService


class BarterSystemDemo:
    """Demonstration of the HigherSelf Network Barter System."""

    def __init__(self):
        self.barter_service = BarterService()
        self.notification_service = BarterNotificationService()
        self.config = get_barter_config()

        # Demo entities
        self.entities = {}
        self.listings = {}
        self.requests = {}
        self.matches = {}
        self.transactions = {}

    async def run_demo(self):
        """Run the complete barter system demonstration."""
        print("🌟 HigherSelf Network Barter System Demo")
        print("=" * 50)

        try:
            # Step 1: Create demo entities and profiles
            await self.create_demo_profiles()

            # Step 2: Create service listings
            await self.create_demo_listings()

            # Step 3: Create service requests
            await self.create_demo_requests()

            # Step 4: Find and display matches
            await self.find_and_display_matches()

            # Step 5: Create transactions
            await self.create_demo_transactions()

            # Step 6: Demonstrate notifications
            await self.demonstrate_notifications()

            # Step 7: Show system statistics
            await self.show_system_statistics()

            print("\n🎉 Demo completed successfully!")

        except Exception as e:
            print(f"❌ Demo failed: {e}")
            raise

    async def create_demo_profiles(self):
        """Create demonstration profiles for different entity types."""
        print("\n📋 Creating Demo Profiles...")

        # Wellness Center Profile
        wellness_location = Location(
            city="San Francisco",
            state_province="California",
            country="United States",
            cultural_region=CulturalRegion.NORTH_AMERICA,
            latitude=37.7749,
            longitude=-122.4194,
        )

        wellness_profile = BarterProfile(
            entity_id="wellness_center_sf",
            entity_type="business",
            name="Harmony Wellness Center",
            description="Holistic wellness center offering comprehensive health services",
            location=wellness_location,
            offered_services=[
                ServiceCategory.WELLNESS_CONSULTATION,
                ServiceCategory.MASSAGE_THERAPY,
                ServiceCategory.YOGA_INSTRUCTION,
                ServiceCategory.MEDITATION_GUIDANCE,
            ],
            needed_services=[
                ServiceCategory.MARKETING_CONSULTATION,
                ServiceCategory.WEB_DEVELOPMENT,
                ServiceCategory.GRAPHIC_DESIGN,
            ],
            available_hours_per_week=40,
            max_travel_distance_km=30,
        )

        # Art Gallery Profile
        art_location = Location(
            city="New York",
            state_province="New York",
            country="United States",
            cultural_region=CulturalRegion.NORTH_AMERICA,
            latitude=40.7128,
            longitude=-74.0060,
        )

        art_profile = BarterProfile(
            entity_id="modern_art_gallery_ny",
            entity_type="business",
            name="Modern Expressions Gallery",
            description="Contemporary art gallery showcasing emerging artists",
            location=art_location,
            offered_services=[
                ServiceCategory.ART_CREATION,
                ServiceCategory.ART_CURATION,
                ServiceCategory.CREATIVE_WORKSHOPS,
                ServiceCategory.PHOTOGRAPHY,
            ],
            needed_services=[
                ServiceCategory.BUSINESS_STRATEGY,
                ServiceCategory.DIGITAL_MARKETING,
                ServiceCategory.FINANCIAL_PLANNING,
            ],
            available_hours_per_week=25,
            max_travel_distance_km=50,
        )

        # Individual Practitioner Profile
        practitioner_location = Location(
            city="Los Angeles",
            state_province="California",
            country="United States",
            cultural_region=CulturalRegion.NORTH_AMERICA,
            latitude=34.0522,
            longitude=-118.2437,
        )

        practitioner_profile = BarterProfile(
            entity_id="tech_consultant_la",
            entity_type="individual",
            name="Alex Chen - Tech Consultant",
            description="Senior technology consultant specializing in digital transformation",
            location=practitioner_location,
            offered_services=[
                ServiceCategory.TECHNOLOGY_CONSULTING,
                ServiceCategory.WEB_DEVELOPMENT,
                ServiceCategory.DIGITAL_MARKETING,
            ],
            needed_services=[
                ServiceCategory.WELLNESS_CONSULTATION,
                ServiceCategory.YOGA_INSTRUCTION,
                ServiceCategory.TRADITIONAL_HEALING,
            ],
            available_hours_per_week=15,
            max_travel_distance_km=40,
        )

        # Store profiles
        self.entities["wellness_center"] = await self.barter_service.update_profile(
            wellness_profile
        )
        self.entities["art_gallery"] = await self.barter_service.update_profile(
            art_profile
        )
        self.entities["tech_consultant"] = await self.barter_service.update_profile(
            practitioner_profile
        )

        print(f"✅ Created {len(self.entities)} demo profiles")

    async def create_demo_listings(self):
        """Create demonstration service listings."""
        print("\n📝 Creating Demo Listings...")

        # Wellness consultation listing
        wellness_listing = BarterListing(
            provider_id="wellness_center_sf",
            provider_type="business",
            title="Comprehensive Wellness Consultation",
            description="60-minute holistic wellness assessment including nutrition, lifestyle, and stress management guidance",
            category=ServiceCategory.WELLNESS_CONSULTATION,
            skill_level=SkillLevel.EXPERT,
            location=self.entities["wellness_center"].location,
            available_hours_per_week=20,
            estimated_session_duration=1.0,
            base_value_per_hour=150,
            preferred_exchange_types=[
                ServiceCategory.MARKETING_CONSULTATION,
                ServiceCategory.WEB_DEVELOPMENT,
            ],
            virtual_available=True,
        )

        # Art curation listing
        art_listing = BarterListing(
            provider_id="modern_art_gallery_ny",
            provider_type="business",
            title="Professional Art Curation Services",
            description="Expert art curation for exhibitions, private collections, and corporate spaces",
            category=ServiceCategory.ART_CURATION,
            skill_level=SkillLevel.EXPERT,
            location=self.entities["art_gallery"].location,
            available_hours_per_week=15,
            estimated_session_duration=2.0,
            base_value_per_hour=200,
            preferred_exchange_types=[
                ServiceCategory.BUSINESS_STRATEGY,
                ServiceCategory.DIGITAL_MARKETING,
            ],
            virtual_available=False,
        )

        # Technology consulting listing
        tech_listing = BarterListing(
            provider_id="tech_consultant_la",
            provider_type="individual",
            title="Digital Transformation Consulting",
            description="Strategic technology consulting for small businesses and startups",
            category=ServiceCategory.TECHNOLOGY_CONSULTING,
            skill_level=SkillLevel.EXPERT,
            location=self.entities["tech_consultant"].location,
            available_hours_per_week=12,
            estimated_session_duration=1.5,
            base_value_per_hour=180,
            preferred_exchange_types=[
                ServiceCategory.WELLNESS_CONSULTATION,
                ServiceCategory.YOGA_INSTRUCTION,
            ],
            virtual_available=True,
        )

        # Store listings
        self.listings["wellness"] = await self.barter_service.create_listing(
            wellness_listing
        )
        self.listings["art"] = await self.barter_service.create_listing(art_listing)
        self.listings["tech"] = await self.barter_service.create_listing(tech_listing)

        print(f"✅ Created {len(self.listings)} demo listings")

    async def create_demo_requests(self):
        """Create demonstration service requests."""
        print("\n🔍 Creating Demo Requests...")

        # Marketing consultation request
        marketing_request = BarterRequest(
            requester_id="wellness_center_sf",
            requester_type="business",
            title="Digital Marketing Strategy Consultation",
            description="Need help developing a comprehensive digital marketing strategy for wellness services",
            category=ServiceCategory.MARKETING_CONSULTATION,
            preferred_skill_level=SkillLevel.ADVANCED,
            preferred_location=self.entities["wellness_center"].location,
            max_distance_km=100,
            virtual_acceptable=True,
            offered_service_category=ServiceCategory.WELLNESS_CONSULTATION,
            offered_service_description="Comprehensive wellness consultations",
            offered_value_per_hour=150,
            offered_total_hours=8,
            required_total_hours=6,
        )

        # Wellness consultation request
        wellness_request = BarterRequest(
            requester_id="tech_consultant_la",
            requester_type="individual",
            title="Holistic Wellness Assessment",
            description="Seeking comprehensive wellness consultation to improve work-life balance",
            category=ServiceCategory.WELLNESS_CONSULTATION,
            preferred_skill_level=SkillLevel.EXPERT,
            preferred_location=self.entities["tech_consultant"].location,
            max_distance_km=75,
            virtual_acceptable=True,
            offered_service_category=ServiceCategory.TECHNOLOGY_CONSULTING,
            offered_service_description="Technology strategy and implementation",
            offered_value_per_hour=180,
            offered_total_hours=5,
            required_total_hours=6,
        )

        # Store requests
        self.requests["marketing"] = await self.barter_service.create_request(
            marketing_request
        )
        self.requests["wellness"] = await self.barter_service.create_request(
            wellness_request
        )

        print(f"✅ Created {len(self.requests)} demo requests")

    async def find_and_display_matches(self):
        """Find and display potential matches."""
        print("\n🎯 Finding Matches...")

        for request_name, request in self.requests.items():
            print(f"\nFinding matches for: {request.title}")

            matches = await self.barter_service.find_matches(request, limit=5)
            self.matches[request_name] = matches

            if matches:
                print(f"Found {len(matches)} potential matches:")
                for i, match in enumerate(matches, 1):
                    print(f"  {i}. Compatibility: {match.compatibility_score:.1%}")
                    print(
                        f"     Distance: {match.distance_km:.1f}km"
                        if match.distance_km
                        else "     Virtual available"
                    )
                    print(
                        f"     Category match: {'Yes' if match.category_match else 'No'}"
                    )
                    print(f"     Value balance: {match.value_balance_ratio:.1%}")
            else:
                print("  No matches found")

    async def create_demo_transactions(self):
        """Create demonstration transactions from matches."""
        print("\n💼 Creating Demo Transactions...")

        # Create a transaction from the first match if available
        if self.matches.get("wellness") and len(self.matches["wellness"]) > 0:
            best_match = self.matches["wellness"][0]

            transaction = await self.barter_service.create_transaction(
                match=best_match,
                provider_id="wellness_center_sf",
                requester_id="tech_consultant_la",
            )

            self.transactions["wellness_tech"] = transaction
            print(f"✅ Created transaction: {transaction.id}")
            print(f"   Provider: {transaction.provider_id}")
            print(f"   Requester: {transaction.requester_id}")
            print(f"   Total value: ${transaction.total_value_exchanged}")
        else:
            print("⚠️ No matches available for transaction creation")

    async def demonstrate_notifications(self):
        """Demonstrate the notification system."""
        print("\n🔔 Demonstrating Notifications...")

        # Create sample notifications
        await self.notification_service.create_notification(
            recipient_id="wellness_center_sf",
            notification_type="new_match_found",
            data={
                "service_type": "Technology Consulting",
                "provider_name": "Alex Chen",
                "compatibility_score": "92%",
                "distance": "Virtual",
            },
        )

        await self.notification_service.create_notification(
            recipient_id="tech_consultant_la",
            notification_type="match_accepted",
            data={
                "provider_name": "Harmony Wellness Center",
                "service_type": "Wellness Consultation",
            },
        )

        # Retrieve notifications
        for entity_id in ["wellness_center_sf", "tech_consultant_la"]:
            notifications = await self.notification_service.get_user_notifications(
                entity_id, limit=5
            )
            print(f"📬 {entity_id}: {len(notifications)} notifications")

    async def show_system_statistics(self):
        """Display system statistics and summary."""
        print("\n📊 System Statistics")
        print("-" * 30)
        print(f"Profiles created: {len(self.entities)}")
        print(f"Listings created: {len(self.listings)}")
        print(f"Requests created: {len(self.requests)}")
        print(
            f"Matches found: {sum(len(matches) for matches in self.matches.values())}"
        )
        print(f"Transactions created: {len(self.transactions)}")

        # Show configuration
        print(f"\nConfiguration:")
        print(f"Default search radius: {self.config.default_search_radius_km}km")
        print(f"Min compatibility score: {self.config.min_compatibility_score}")
        print(
            f"Cultural adaptation: {'Enabled' if self.config.enable_cultural_adaptation else 'Disabled'}"
        )
        print(
            f"Notifications: {'Enabled' if self.config.enable_notifications else 'Disabled'}"
        )

    def print_demo_data(self):
        """Print all demo data in JSON format for inspection."""
        print("\n📄 Demo Data Summary")
        print("=" * 50)

        demo_data = {
            "entities": {k: v.model_dump() for k, v in self.entities.items()},
            "listings": {k: v.model_dump() for k, v in self.listings.items()},
            "requests": {k: v.model_dump() for k, v in self.requests.items()},
            "matches": {
                k: [m.model_dump() for m in matches]
                for k, matches in self.matches.items()
            },
            "transactions": {k: v.model_dump() for k, v in self.transactions.items()},
        }

        print(json.dumps(demo_data, indent=2, default=str))


async def main():
    """Main demo function."""
    demo = BarterSystemDemo()

    try:
        await demo.run_demo()

        # Optionally print all demo data
        if (
            input("\nWould you like to see the detailed demo data? (y/n): ").lower()
            == "y"
        ):
            demo.print_demo_data()

    except Exception as e:
        print(f"Demo failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    print("Starting HigherSelf Network Barter System Demo...")
    asyncio.run(main())
