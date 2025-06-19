"""
The 7 Space Appointment Scheduling System

Automated appointment scheduling with real-time availability tracking, client management,
and integrated booking system for The 7 Space wellness center operations.
"""

import asyncio
import logging
from datetime import datetime, timedelta, time
from typing import Dict, List, Optional, Any, Tuple
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

class AppointmentStatus(Enum):
    """Appointment status enumeration"""
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"
    RESCHEDULED = "rescheduled"

class ServiceType(Enum):
    """Wellness service types"""
    MASSAGE = "massage"
    YOGA = "yoga"
    MEDITATION = "meditation"
    REIKI = "reiki"
    ACUPUNCTURE = "acupuncture"
    COUNSELING = "counseling"
    NUTRITION = "nutrition"
    WELLNESS_CONSULTATION = "wellness_consultation"

@dataclass
class WellnessService:
    """Wellness service definition"""
    id: str
    name: str
    service_type: ServiceType
    duration_minutes: int
    price: float
    description: str
    practitioner_required: bool = True
    max_participants: int = 1
    preparation_time: int = 15  # minutes between appointments
    active: bool = True

@dataclass
class Appointment:
    """Appointment data model"""
    id: str
    client_id: str
    client_name: str
    client_email: str
    client_phone: str
    service_id: str
    service_name: str
    practitioner_id: Optional[str]
    practitioner_name: Optional[str]
    appointment_date: datetime
    duration_minutes: int
    status: AppointmentStatus
    price: float
    notes: str
    created_at: datetime
    updated_at: datetime
    notion_page_id: Optional[str] = None
    reminder_sent: bool = False
    confirmation_sent: bool = False
    intake_form_completed: bool = False
    special_requests: str = ""
    
class AppointmentScheduler:
    """
    Automated appointment scheduling system for The 7 Space wellness center.
    Handles real-time availability, booking management, and client communications.
    """
    
    def __init__(self):
        self.config = the7space_config
        self.notion_client = Client(auth=self.config.notion_api_token)
        self.notion_helper = NotionHelper(self.notion_client)
        self.error_manager = ErrorRecoveryManager()
        
        # Database IDs
        self.appointments_db_id = self.config.get_database_id("appointments")
        self.services_db_id = self.config.get_database_id("services")
        self.contacts_db_id = self.config.get_database_id("contacts")
        
        if not self.appointments_db_id:
            raise ValueError("Appointments database ID not configured")
        
        # Load services and business hours
        self.services = {}
        self.business_hours = self.config.business_hours
        
    async def initialize(self):
        """Initialize the scheduler with services and settings"""
        try:
            await self._load_services()
            logger.info("Appointment scheduler initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize appointment scheduler: {str(e)}")
            raise
    
    async def book_appointment(self, booking_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Book a new appointment with availability validation.
        
        Args:
            booking_data: Dictionary containing booking information
            
        Returns:
            Dict containing booking result and appointment details
        """
        try:
            logger.info(f"Processing appointment booking for {booking_data.get('client_name', 'Unknown')}")
            
            # Validate booking data
            validated_data = await self._validate_booking_data(booking_data)
            
            # Check availability
            is_available, availability_info = await self.check_availability(
                service_id=validated_data["service_id"],
                requested_datetime=validated_data["appointment_datetime"],
                duration_minutes=validated_data.get("duration_minutes")
            )
            
            if not is_available:
                return {
                    "success": False,
                    "error": "Time slot not available",
                    "availability_info": availability_info,
                    "suggested_times": await self._get_suggested_times(
                        validated_data["service_id"],
                        validated_data["appointment_datetime"]
                    )
                }
            
            # Create appointment
            appointment = await self._create_appointment(validated_data)
            
            # Send confirmation
            await self._send_booking_confirmation(appointment)
            
            # Schedule reminders
            await self._schedule_appointment_reminders(appointment)
            
            logger.info(f"Successfully booked appointment {appointment.id}")
            
            return {
                "success": True,
                "appointment_id": appointment.id,
                "appointment_details": asdict(appointment),
                "confirmation_sent": True
            }
            
        except Exception as e:
            logger.error(f"Failed to book appointment: {str(e)}")
            await self.error_manager.handle_error("book_appointment", e, booking_data)
            return {
                "success": False,
                "error": str(e)
            }
    
    async def check_availability(self, service_id: str, requested_datetime: datetime, 
                               duration_minutes: Optional[int] = None) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if a time slot is available for booking.
        
        Args:
            service_id: Service identifier
            requested_datetime: Requested appointment time
            duration_minutes: Optional duration override
            
        Returns:
            Tuple of (is_available, availability_info)
        """
        try:
            # Get service details
            service = self.services.get(service_id)
            if not service:
                return False, {"error": "Service not found"}
            
            duration = duration_minutes or service.duration_minutes
            appointment_end = requested_datetime + timedelta(minutes=duration)
            
            # Check business hours
            if not self._is_within_business_hours(requested_datetime, appointment_end):
                return False, {
                    "error": "Outside business hours",
                    "business_hours": self._get_business_hours_for_date(requested_datetime.date())
                }
            
            # Check for conflicts
            conflicts = await self._check_appointment_conflicts(
                requested_datetime, 
                appointment_end,
                service.practitioner_required
            )
            
            if conflicts:
                return False, {
                    "error": "Time slot conflicts with existing appointment",
                    "conflicts": conflicts
                }
            
            # Check practitioner availability if required
            if service.practitioner_required:
                practitioner_available = await self._check_practitioner_availability(
                    service_id, requested_datetime, duration
                )
                if not practitioner_available:
                    return False, {
                        "error": "No practitioner available",
                        "service_requires_practitioner": True
                    }
            
            return True, {
                "available": True,
                "service_name": service.name,
                "duration_minutes": duration,
                "price": service.price
            }
            
        except Exception as e:
            logger.error(f"Failed to check availability: {str(e)}")
            return False, {"error": str(e)}
    
    async def get_available_slots(self, service_id: str, date: datetime.date, 
                                 days_ahead: int = 7) -> List[Dict[str, Any]]:
        """
        Get all available time slots for a service within a date range.
        
        Args:
            service_id: Service identifier
            date: Starting date
            days_ahead: Number of days to check
            
        Returns:
            List of available time slots
        """
        try:
            service = self.services.get(service_id)
            if not service:
                return []
            
            available_slots = []
            
            for day_offset in range(days_ahead):
                check_date = date + timedelta(days=day_offset)
                day_slots = await self._get_available_slots_for_date(service, check_date)
                available_slots.extend(day_slots)
            
            logger.info(f"Found {len(available_slots)} available slots for service {service_id}")
            return available_slots
            
        except Exception as e:
            logger.error(f"Failed to get available slots: {str(e)}")
            return []
    
    async def reschedule_appointment(self, appointment_id: str, new_datetime: datetime) -> Dict[str, Any]:
        """
        Reschedule an existing appointment.
        
        Args:
            appointment_id: Appointment identifier
            new_datetime: New appointment time
            
        Returns:
            Dict containing reschedule result
        """
        try:
            logger.info(f"Rescheduling appointment {appointment_id}")
            
            # Get existing appointment
            appointment = await self.get_appointment_by_id(appointment_id)
            if not appointment:
                return {"success": False, "error": "Appointment not found"}
            
            # Check if appointment can be rescheduled
            if appointment.status in [AppointmentStatus.COMPLETED, AppointmentStatus.CANCELLED]:
                return {"success": False, "error": "Cannot reschedule completed or cancelled appointment"}
            
            # Check availability for new time
            is_available, availability_info = await self.check_availability(
                appointment.service_id, new_datetime, appointment.duration_minutes
            )
            
            if not is_available:
                return {
                    "success": False,
                    "error": "New time slot not available",
                    "availability_info": availability_info
                }
            
            # Update appointment
            old_datetime = appointment.appointment_date
            appointment.appointment_date = new_datetime
            appointment.status = AppointmentStatus.RESCHEDULED
            appointment.updated_at = datetime.now()
            
            # Update in Notion
            await self._update_appointment_in_notion(appointment)
            
            # Send reschedule notification
            await self._send_reschedule_notification(appointment, old_datetime)
            
            logger.info(f"Successfully rescheduled appointment {appointment_id}")
            
            return {
                "success": True,
                "appointment_id": appointment_id,
                "old_datetime": old_datetime.isoformat(),
                "new_datetime": new_datetime.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to reschedule appointment: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def cancel_appointment(self, appointment_id: str, reason: str = "") -> Dict[str, Any]:
        """
        Cancel an existing appointment.
        
        Args:
            appointment_id: Appointment identifier
            reason: Cancellation reason
            
        Returns:
            Dict containing cancellation result
        """
        try:
            logger.info(f"Cancelling appointment {appointment_id}")
            
            # Get appointment
            appointment = await self.get_appointment_by_id(appointment_id)
            if not appointment:
                return {"success": False, "error": "Appointment not found"}
            
            # Update status
            appointment.status = AppointmentStatus.CANCELLED
            appointment.notes += f"\nCancelled: {reason}" if reason else "\nCancelled"
            appointment.updated_at = datetime.now()
            
            # Update in Notion
            await self._update_appointment_in_notion(appointment)
            
            # Send cancellation notification
            await self._send_cancellation_notification(appointment, reason)
            
            # Handle cancellation policy (refunds, etc.)
            await self._handle_cancellation_policy(appointment)
            
            logger.info(f"Successfully cancelled appointment {appointment_id}")
            
            return {
                "success": True,
                "appointment_id": appointment_id,
                "cancellation_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to cancel appointment: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_appointment_by_id(self, appointment_id: str) -> Optional[Appointment]:
        """
        Retrieve appointment by ID.
        
        Args:
            appointment_id: Appointment identifier
            
        Returns:
            Appointment object if found
        """
        try:
            filter_condition = {
                "property": "Appointment ID",
                "rich_text": {"equals": appointment_id}
            }
            
            results = await self.notion_helper.query_database(
                database_id=self.appointments_db_id,
                filter_condition=filter_condition
            )
            
            if not results:
                return None
            
            return await self._notion_page_to_appointment(results[0])
            
        except Exception as e:
            logger.error(f"Failed to get appointment by ID: {str(e)}")
            return None
    
    async def get_daily_schedule(self, date: datetime.date, 
                               practitioner_id: Optional[str] = None) -> List[Appointment]:
        """
        Get daily appointment schedule.
        
        Args:
            date: Date to get schedule for
            practitioner_id: Optional practitioner filter
            
        Returns:
            List of appointments for the day
        """
        try:
            # Build filter for the date
            start_datetime = datetime.combine(date, time.min)
            end_datetime = datetime.combine(date, time.max)
            
            filter_condition = {
                "and": [
                    {
                        "property": "Appointment Date",
                        "date": {
                            "on_or_after": start_datetime.isoformat()
                        }
                    },
                    {
                        "property": "Appointment Date", 
                        "date": {
                            "on_or_before": end_datetime.isoformat()
                        }
                    }
                ]
            }
            
            # Add practitioner filter if specified
            if practitioner_id:
                filter_condition["and"].append({
                    "property": "Practitioner ID",
                    "rich_text": {"equals": practitioner_id}
                })
            
            results = await self.notion_helper.query_database(
                database_id=self.appointments_db_id,
                filter_condition=filter_condition,
                sorts=[{
                    "property": "Appointment Date",
                    "direction": "ascending"
                }]
            )
            
            appointments = []
            for page in results:
                appointment = await self._notion_page_to_appointment(page)
                if appointment:
                    appointments.append(appointment)
            
            logger.info(f"Retrieved {len(appointments)} appointments for {date}")
            return appointments
            
        except Exception as e:
            logger.error(f"Failed to get daily schedule: {str(e)}")
            return []

    async def _load_services(self):
        """Load wellness services from configuration or database"""
        try:
            # Default services for The 7 Space
            default_services = [
                WellnessService(
                    id="massage_60",
                    name="Therapeutic Massage (60 min)",
                    service_type=ServiceType.MASSAGE,
                    duration_minutes=60,
                    price=120.0,
                    description="Full body therapeutic massage for relaxation and healing"
                ),
                WellnessService(
                    id="yoga_private",
                    name="Private Yoga Session",
                    service_type=ServiceType.YOGA,
                    duration_minutes=90,
                    price=100.0,
                    description="One-on-one yoga instruction tailored to your needs"
                ),
                WellnessService(
                    id="meditation_guided",
                    name="Guided Meditation",
                    service_type=ServiceType.MEDITATION,
                    duration_minutes=45,
                    price=60.0,
                    description="Personalized meditation guidance and instruction"
                ),
                WellnessService(
                    id="reiki_healing",
                    name="Reiki Healing Session",
                    service_type=ServiceType.REIKI,
                    duration_minutes=75,
                    price=90.0,
                    description="Energy healing and chakra balancing"
                ),
                WellnessService(
                    id="wellness_consultation",
                    name="Wellness Consultation",
                    service_type=ServiceType.WELLNESS_CONSULTATION,
                    duration_minutes=60,
                    price=80.0,
                    description="Comprehensive wellness assessment and planning"
                )
            ]

            # Convert to dictionary for easy lookup
            self.services = {service.id: service for service in default_services}

            logger.info(f"Loaded {len(self.services)} wellness services")

        except Exception as e:
            logger.error(f"Failed to load services: {str(e)}")
            self.services = {}

    async def _validate_booking_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate booking data"""
        required_fields = [
            "client_name", "client_email", "service_id", "appointment_datetime"
        ]

        for field in required_fields:
            if field not in data or not data[field]:
                raise ValueError(f"Missing required field: {field}")

        # Validate service exists
        if data["service_id"] not in self.services:
            raise ValueError(f"Invalid service ID: {data['service_id']}")

        # Validate datetime
        if isinstance(data["appointment_datetime"], str):
            data["appointment_datetime"] = datetime.fromisoformat(data["appointment_datetime"])

        # Validate email format
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, data["client_email"]):
            raise ValueError("Invalid email format")

        return data

    async def _create_appointment(self, validated_data: Dict[str, Any]) -> Appointment:
        """Create new appointment object and save to Notion"""
        try:
            service = self.services[validated_data["service_id"]]

            appointment = Appointment(
                id=self._generate_appointment_id(),
                client_id=validated_data.get("client_id", ""),
                client_name=validated_data["client_name"],
                client_email=validated_data["client_email"],
                client_phone=validated_data.get("client_phone", ""),
                service_id=validated_data["service_id"],
                service_name=service.name,
                practitioner_id=validated_data.get("practitioner_id"),
                practitioner_name=validated_data.get("practitioner_name"),
                appointment_date=validated_data["appointment_datetime"],
                duration_minutes=validated_data.get("duration_minutes", service.duration_minutes),
                status=AppointmentStatus.SCHEDULED,
                price=validated_data.get("price", service.price),
                notes=validated_data.get("notes", ""),
                created_at=datetime.now(),
                updated_at=datetime.now(),
                special_requests=validated_data.get("special_requests", "")
            )

            # Save to Notion
            notion_properties = await self._appointment_to_notion_properties(appointment)
            response = await self.notion_helper.create_page(
                database_id=self.appointments_db_id,
                properties=notion_properties
            )

            appointment.notion_page_id = response["id"]

            return appointment

        except Exception as e:
            logger.error(f"Failed to create appointment: {str(e)}")
            raise

    def _generate_appointment_id(self) -> str:
        """Generate unique appointment ID"""
        from uuid import uuid4
        return f"APT-{uuid4().hex[:8].upper()}"

    async def _appointment_to_notion_properties(self, appointment: Appointment) -> Dict[str, Any]:
        """Convert Appointment object to Notion properties"""
        return {
            "Title": {"title": [{"text": {"content": f"{appointment.client_name} - {appointment.service_name}"}}]},
            "Appointment ID": {"rich_text": [{"text": {"content": appointment.id}}]},
            "Client Name": {"rich_text": [{"text": {"content": appointment.client_name}}]},
            "Client Email": {"email": appointment.client_email},
            "Client Phone": {"phone_number": appointment.client_phone},
            "Service": {"rich_text": [{"text": {"content": appointment.service_name}}]},
            "Appointment Date": {"date": {"start": appointment.appointment_date.isoformat()}},
            "Duration": {"number": appointment.duration_minutes},
            "Status": {"select": {"name": appointment.status.value}},
            "Price": {"number": appointment.price},
            "Notes": {"rich_text": [{"text": {"content": appointment.notes}}]},
            "Created": {"date": {"start": appointment.created_at.isoformat()}},
            "Updated": {"date": {"start": appointment.updated_at.isoformat()}}
        }

    async def _notion_page_to_appointment(self, page: Dict[str, Any]) -> Optional[Appointment]:
        """Convert Notion page to Appointment object"""
        try:
            props = page["properties"]

            return Appointment(
                id=self._get_notion_text(props.get("Appointment ID", {})),
                client_id=self._get_notion_text(props.get("Client ID", {})),
                client_name=self._get_notion_text(props.get("Client Name", {})),
                client_email=self._get_notion_email(props.get("Client Email", {})),
                client_phone=self._get_notion_phone(props.get("Client Phone", {})),
                service_id=self._get_notion_text(props.get("Service ID", {})),
                service_name=self._get_notion_text(props.get("Service", {})),
                practitioner_id=self._get_notion_text(props.get("Practitioner ID", {})),
                practitioner_name=self._get_notion_text(props.get("Practitioner", {})),
                appointment_date=self._get_notion_date(props.get("Appointment Date", {})) or datetime.now(),
                duration_minutes=int(self._get_notion_number(props.get("Duration", {})) or 60),
                status=AppointmentStatus(self._get_notion_select(props.get("Status", {})) or "scheduled"),
                price=float(self._get_notion_number(props.get("Price", {})) or 0),
                notes=self._get_notion_text(props.get("Notes", {})),
                created_at=self._get_notion_date(props.get("Created", {})) or datetime.now(),
                updated_at=self._get_notion_date(props.get("Updated", {})) or datetime.now(),
                notion_page_id=page["id"]
            )
        except Exception as e:
            logger.error(f"Failed to convert Notion page to appointment: {str(e)}")
            return None

    def _get_notion_text(self, prop: Dict) -> str:
        """Extract text from Notion property"""
        if prop.get("rich_text"):
            return prop["rich_text"][0]["text"]["content"] if prop["rich_text"] else ""
        return ""

    def _get_notion_email(self, prop: Dict) -> str:
        """Extract email from Notion property"""
        return prop.get("email", "")

    def _get_notion_phone(self, prop: Dict) -> str:
        """Extract phone from Notion property"""
        return prop.get("phone_number", "")

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
