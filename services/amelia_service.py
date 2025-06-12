"""
Amelia integration service for The HigherSelf Network Server.
This service handles integration with Amelia Booking while maintaining Notion as the central hub.
"""

import json
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import requests
from loguru import logger
from pydantic import BaseModel, Field


class AmeliaConfig(BaseModel):
    """Configuration for Amelia Booking API integration."""

    api_url: str
    api_key: str
    site_id: int = 1

    class Config:
        env_prefix = "AMELIA_"


class AmeliaAppointment(BaseModel):
    """Model representing an Amelia booking appointment."""

    id: Optional[int] = None
    booking_start: datetime
    booking_end: datetime
    status: str  # pending, approved, canceled, rejected
    service_id: int
    provider_id: int
    customer_id: int
    customer_first_name: str
    customer_last_name: str
    customer_email: str
    customer_phone: Optional[str] = None
    payment_amount: Optional[float] = None
    payment_status: Optional[str] = None
    internal_notes: Optional[str] = None
    custom_fields: Dict[str, Any] = Field(default_factory=dict)
    location_id: Optional[int] = None
    created_date: Optional[datetime] = None
    updated_date: Optional[datetime] = None
    notion_page_id: Optional[str] = None


class AmeliaService(BaseModel):
    """Model representing an Amelia service."""

    id: int
    name: str
    description: Optional[str] = None
    color: Optional[str] = None
    price: float
    duration: int  # in seconds
    category_id: Optional[int] = None
    min_capacity: int = 1
    max_capacity: int = 1
    status: str = "visible"  # visible, hidden, disabled


class AmeliaCustomer(BaseModel):
    """Model representing an Amelia customer."""

    id: Optional[int] = None
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    gender: Optional[str] = None
    birthday: Optional[str] = None
    note: Optional[str] = None
    notion_page_id: Optional[str] = None
    status: str = "visible"


class AmeliaServiceClient:
    """
    Client for interacting with Amelia Booking plugin's API.
    Ensures all booking data is synchronized with Notion as the central hub.
    """

    def __init__(self, api_url: str = None, api_key: str = None, site_id: int = None):
        """
        Initialize the Amelia Booking service client.

        Args:
            api_url: Amelia API URL (typically the WordPress site URL with /wp-json/amelia/v1/)
            api_key: Amelia API Key
            site_id: Amelia site ID (defaults to 1 for single-site installations)
        """
        self.api_url = api_url or os.environ.get("AMELIA_API_URL")
        self.api_key = api_key or os.environ.get("AMELIA_API_KEY")
        self.site_id = site_id or int(os.environ.get("AMELIA_SITE_ID", "1"))

        if not self.api_url or not self.api_key:
            logger.warning("Amelia Booking credentials not fully configured")

    def _get_headers(self) -> Dict[str, str]:
        """
        Get the headers required for Amelia API requests.

        Returns:
            Dictionary of headers
        """
        return {"Content-Type": "application/json", "X-API-KEY": self.api_key}

    async def validate_credentials(self) -> bool:
        """
        Validate the Amelia API credentials.

        Returns:
            True if credentials are valid, False otherwise
        """
        if not self.api_url or not self.api_key:
            logger.error("Amelia Booking credentials not configured")
            return False

        try:
            # Test the API by fetching services
            url = f"{self.api_url}/services"
            headers = self._get_headers()

            response = requests.get(url, headers=headers)
            response.raise_for_status()

            logger.info("Amelia Booking credentials validated successfully")
            return True
        except Exception as e:
            logger.error(f"Invalid Amelia Booking credentials: {e}")
            return False

    async def get_services(self) -> List[AmeliaService]:
        """
        Get all services configured in Amelia.

        Returns:
            List of AmeliaService objects
        """
        if not self.api_url or not self.api_key:
            logger.error("Amelia Booking credentials not configured")
            return []

        try:
            url = f"{self.api_url}/services"
            headers = self._get_headers()

            response = requests.get(url, headers=headers)
            response.raise_for_status()

            services_data = response.json()
            services = []

            for data in services_data:
                service = AmeliaService(
                    id=data.get("id"),
                    name=data.get("name"),
                    description=data.get("description"),
                    color=data.get("color"),
                    price=float(data.get("price", 0)),
                    duration=int(data.get("duration", 3600)),
                    category_id=data.get("categoryId"),
                    min_capacity=int(data.get("minCapacity", 1)),
                    max_capacity=int(data.get("maxCapacity", 1)),
                    status=data.get("status", "visible"),
                )
                services.append(service)

            logger.info(f"Retrieved {len(services)} services from Amelia")
            return services
        except Exception as e:
            logger.error(f"Error getting services: {e}")
            return []

    async def get_appointments(
        self, start_date: datetime = None, end_date: datetime = None, status: str = None
    ) -> List[AmeliaAppointment]:
        """
        Get appointments within a date range.

        Args:
            start_date: Optional start date for the range
            end_date: Optional end date for the range
            status: Optional status filter (pending, approved, canceled, rejected)

        Returns:
            List of AmeliaAppointment objects
        """
        if not self.api_url or not self.api_key:
            logger.error("Amelia Booking credentials not configured")
            return []

        try:
            url = f"{self.api_url}/appointments"
            headers = self._get_headers()
            params = {}

            if start_date:
                params["dateFrom"] = start_date.strftime("%Y-%m-%d")

            if end_date:
                params["dateTo"] = end_date.strftime("%Y-%m-%d")

            if status:
                params["status"] = status

            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()

            appointments_data = response.json()
            appointments = []

            for data in appointments_data:
                try:
                    # Parse custom fields to find Notion page ID if it exists
                    notion_page_id = None
                    custom_fields = {}

                    if "customFields" in data:
                        for field in data["customFields"]:
                            custom_fields[field.get("name", "unknown")] = field.get(
                                "value"
                            )
                            if (
                                field.get("name") == "notion_page_id"
                                or field.get("label") == "Notion Page ID"
                            ):
                                notion_page_id = field.get("value")

                    # Parse the appointment data
                    appointment = AmeliaAppointment(
                        id=data.get("id"),
                        booking_start=datetime.fromisoformat(
                            data.get("bookingStart").replace("Z", "+00:00")
                        ),
                        booking_end=datetime.fromisoformat(
                            data.get("bookingEnd").replace("Z", "+00:00")
                        ),
                        status=data.get("status"),
                        service_id=data.get("serviceId"),
                        provider_id=data.get("providerId"),
                        customer_id=data.get("customerId"),
                        customer_first_name=data.get("customerFirstName", ""),
                        customer_last_name=data.get("customerLastName", ""),
                        customer_email=data.get("customerEmail", ""),
                        customer_phone=data.get("customerPhone"),
                        payment_amount=float(data.get("payment", {}).get("amount", 0))
                        if "payment" in data
                        else None,
                        payment_status=data.get("payment", {}).get("status")
                        if "payment" in data
                        else None,
                        internal_notes=data.get("internalNotes"),
                        custom_fields=custom_fields,
                        location_id=data.get("locationId"),
                        notion_page_id=notion_page_id,
                    )

                    if "created" in data:
                        appointment.created_date = datetime.fromisoformat(
                            data.get("created").replace("Z", "+00:00")
                        )

                    if "updated" in data:
                        appointment.updated_date = datetime.fromisoformat(
                            data.get("updated").replace("Z", "+00:00")
                        )

                    appointments.append(appointment)
                except Exception as e:
                    logger.error(f"Error parsing appointment data: {e}")

            logger.info(f"Retrieved {len(appointments)} appointments from Amelia")
            return appointments
        except Exception as e:
            logger.error(f"Error getting appointments: {e}")
            return []

    async def get_appointment(self, appointment_id: int) -> Optional[AmeliaAppointment]:
        """
        Get a specific appointment by ID.

        Args:
            appointment_id: Amelia appointment ID

        Returns:
            AmeliaAppointment if found, None otherwise
        """
        if not self.api_url or not self.api_key:
            logger.error("Amelia Booking credentials not configured")
            return None

        try:
            url = f"{self.api_url}/appointments/{appointment_id}"
            headers = self._get_headers()

            response = requests.get(url, headers=headers)
            response.raise_for_status()

            data = response.json()

            # Parse custom fields to find Notion page ID if it exists
            notion_page_id = None
            custom_fields = {}

            if "customFields" in data:
                for field in data["customFields"]:
                    custom_fields[field.get("name", "unknown")] = field.get("value")
                    if (
                        field.get("name") == "notion_page_id"
                        or field.get("label") == "Notion Page ID"
                    ):
                        notion_page_id = field.get("value")

            # Parse the appointment data
            appointment = AmeliaAppointment(
                id=data.get("id"),
                booking_start=datetime.fromisoformat(
                    data.get("bookingStart").replace("Z", "+00:00")
                ),
                booking_end=datetime.fromisoformat(
                    data.get("bookingEnd").replace("Z", "+00:00")
                ),
                status=data.get("status"),
                service_id=data.get("serviceId"),
                provider_id=data.get("providerId"),
                customer_id=data.get("customerId"),
                customer_first_name=data.get("customerFirstName", ""),
                customer_last_name=data.get("customerLastName", ""),
                customer_email=data.get("customerEmail", ""),
                customer_phone=data.get("customerPhone"),
                payment_amount=float(data.get("payment", {}).get("amount", 0))
                if "payment" in data
                else None,
                payment_status=data.get("payment", {}).get("status")
                if "payment" in data
                else None,
                internal_notes=data.get("internalNotes"),
                custom_fields=custom_fields,
                location_id=data.get("locationId"),
                notion_page_id=notion_page_id,
            )

            if "created" in data:
                appointment.created_date = datetime.fromisoformat(
                    data.get("created").replace("Z", "+00:00")
                )

            if "updated" in data:
                appointment.updated_date = datetime.fromisoformat(
                    data.get("updated").replace("Z", "+00:00")
                )

            logger.info(f"Retrieved Amelia appointment: {appointment_id}")
            return appointment
        except Exception as e:
            logger.error(f"Error getting appointment {appointment_id}: {e}")
            return None

    async def create_appointment(self, appointment: AmeliaAppointment) -> Optional[int]:
        """
        Create a new appointment in Amelia.

        Args:
            appointment: AmeliaAppointment model with appointment details

        Returns:
            Appointment ID if successful, None otherwise
        """
        if not self.api_url or not self.api_key:
            logger.error("Amelia Booking credentials not configured")
            return None

        try:
            url = f"{self.api_url}/appointments"
            headers = self._get_headers()

            # Prepare custom fields including Notion page ID if available
            custom_fields = []
            for field_name, field_value in appointment.custom_fields.items():
                custom_fields.append({"name": field_name, "value": field_value})

            if appointment.notion_page_id and not any(
                f.get("name") == "notion_page_id" for f in custom_fields
            ):
                custom_fields.append(
                    {"name": "notion_page_id", "value": appointment.notion_page_id}
                )

            # Prepare appointment data
            payload = {
                "bookingStart": appointment.booking_start.isoformat(),
                "bookingEnd": appointment.booking_end.isoformat(),
                "status": appointment.status,
                "serviceId": appointment.service_id,
                "providerId": appointment.provider_id,
                "customer": {
                    "id": appointment.customer_id if appointment.customer_id else None,
                    "firstName": appointment.customer_first_name,
                    "lastName": appointment.customer_last_name,
                    "email": appointment.customer_email,
                    "phone": appointment.customer_phone,
                },
                "customFields": custom_fields,
            }

            if appointment.location_id:
                payload["locationId"] = appointment.location_id

            if appointment.internal_notes:
                payload["internalNotes"] = appointment.internal_notes

            # Add payment details if provided
            if appointment.payment_amount is not None and appointment.payment_status:
                payload["payment"] = {
                    "amount": appointment.payment_amount,
                    "status": appointment.payment_status,
                }

            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()

            data = response.json()
            appointment_id = data.get("id")
            logger.info(f"Created Amelia appointment: {appointment_id}")
            return appointment_id
        except Exception as e:
            logger.error(f"Error creating appointment: {e}")
            return None

    async def update_appointment(
        self, appointment_id: int, update_data: Dict[str, Any]
    ) -> bool:
        """
        Update an existing appointment in Amelia.

        Args:
            appointment_id: Amelia appointment ID
            update_data: Dictionary of fields to update

        Returns:
            True if update successful, False otherwise
        """
        if not self.api_url or not self.api_key:
            logger.error("Amelia Booking credentials not configured")
            return False

        try:
            url = f"{self.api_url}/appointments/{appointment_id}"
            headers = self._get_headers()

            response = requests.patch(url, headers=headers, json=update_data)
            response.raise_for_status()

            logger.info(f"Updated Amelia appointment: {appointment_id}")
            return True
        except Exception as e:
            logger.error(f"Error updating appointment {appointment_id}: {e}")
            return False

    async def cancel_appointment(self, appointment_id: int) -> bool:
        """
        Cancel an appointment in Amelia.

        Args:
            appointment_id: Amelia appointment ID

        Returns:
            True if cancellation successful, False otherwise
        """
        return await self.update_appointment(appointment_id, {"status": "canceled"})

    async def get_customer(self, customer_id: int) -> Optional[AmeliaCustomer]:
        """
        Get a customer from Amelia by ID.

        Args:
            customer_id: Amelia customer ID

        Returns:
            AmeliaCustomer if found, None otherwise
        """
        if not self.api_url or not self.api_key:
            logger.error("Amelia Booking credentials not configured")
            return None

        try:
            url = f"{self.api_url}/customers/{customer_id}"
            headers = self._get_headers()

            response = requests.get(url, headers=headers)
            response.raise_for_status()

            data = response.json()

            # Parse custom fields to find Notion page ID if it exists
            notion_page_id = None
            if "fields" in data:
                for field in data["fields"]:
                    if (
                        field.get("name") == "notion_page_id"
                        or field.get("label") == "Notion Page ID"
                    ):
                        notion_page_id = field.get("value")

            customer = AmeliaCustomer(
                id=data.get("id"),
                first_name=data.get("firstName", ""),
                last_name=data.get("lastName", ""),
                email=data.get("email", ""),
                phone=data.get("phone"),
                gender=data.get("gender"),
                birthday=data.get("birthday"),
                note=data.get("note"),
                status=data.get("status", "visible"),
                notion_page_id=notion_page_id,
            )

            logger.info(f"Retrieved Amelia customer: {customer_id}")
            return customer
        except Exception as e:
            logger.error(f"Error getting customer {customer_id}: {e}")
            return None

    async def create_customer(self, customer: AmeliaCustomer) -> Optional[int]:
        """
        Create a new customer in Amelia.

        Args:
            customer: AmeliaCustomer model with customer details

        Returns:
            Customer ID if successful, None otherwise
        """
        if not self.api_url or not self.api_key:
            logger.error("Amelia Booking credentials not configured")
            return None

        try:
            url = f"{self.api_url}/customers"
            headers = self._get_headers()

            # Prepare customer data
            payload = {
                "firstName": customer.first_name,
                "lastName": customer.last_name,
                "email": customer.email,
                "status": customer.status,
            }

            if customer.phone:
                payload["phone"] = customer.phone

            if customer.gender:
                payload["gender"] = customer.gender

            if customer.birthday:
                payload["birthday"] = customer.birthday

            if customer.note:
                payload["note"] = customer.note

            # Add custom fields for Notion integration if provided
            if customer.notion_page_id:
                payload["fields"] = [
                    {"name": "notion_page_id", "value": customer.notion_page_id}
                ]

            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()

            data = response.json()
            customer_id = data.get("id")
            logger.info(f"Created Amelia customer: {customer_id}")
            return customer_id
        except Exception as e:
            logger.error(f"Error creating customer: {e}")
            return None

    async def update_customer(
        self, customer_id: int, update_data: Dict[str, Any]
    ) -> bool:
        """
        Update an existing customer in Amelia.

        Args:
            customer_id: Amelia customer ID
            update_data: Dictionary of fields to update

        Returns:
            True if update successful, False otherwise
        """
        if not self.api_url or not self.api_key:
            logger.error("Amelia Booking credentials not configured")
            return False

        try:
            url = f"{self.api_url}/customers/{customer_id}"
            headers = self._get_headers()

            response = requests.patch(url, headers=headers, json=update_data)
            response.raise_for_status()

            logger.info(f"Updated Amelia customer: {customer_id}")
            return True
        except Exception as e:
            logger.error(f"Error updating customer {customer_id}: {e}")
            return False

    async def sync_appointment_to_notion(
        self, appointment_id: int, notion_page_id: str
    ) -> bool:
        """
        Update an Amelia appointment with its associated Notion page ID.
        This is done through custom fields in Amelia.

        Args:
            appointment_id: Amelia appointment ID
            notion_page_id: Notion page ID

        Returns:
            True if sync successful, False otherwise
        """
        try:
            # First, get the current appointment to check if it has custom fields
            appointment = await self.get_appointment(appointment_id)
            if not appointment:
                logger.error(
                    f"Could not find appointment {appointment_id} to sync with Notion"
                )
                return False

            # Check if there are existing custom fields
            current_custom_fields = []
            for field_name, field_value in appointment.custom_fields.items():
                # Skip existing notion_page_id field if present
                if field_name != "notion_page_id":
                    current_custom_fields.append(
                        {"name": field_name, "value": field_value}
                    )

            # Add the Notion page ID field
            current_custom_fields.append(
                {"name": "notion_page_id", "value": notion_page_id}
            )

            # Update the appointment with the custom fields
            update_data = {"customFields": current_custom_fields}

            # Also update internal notes if needed
            notes = appointment.internal_notes or ""
            if "Notion Page:" not in notes:
                notion_link = (
                    f"Notion Page: https://notion.so/{notion_page_id.replace('-', '')}"
                )
                if notes:
                    notes += f"\n\n{notion_link}"
                else:
                    notes = notion_link

                update_data["internalNotes"] = notes

            # Update the appointment
            return await self.update_appointment(appointment_id, update_data)
        except Exception as e:
            logger.error(f"Error syncing appointment {appointment_id} to Notion: {e}")
            return False

    async def sync_customer_to_notion(
        self, customer_id: int, notion_page_id: str
    ) -> bool:
        """
        Update an Amelia customer with their associated Notion page ID.

        Args:
            customer_id: Amelia customer ID
            notion_page_id: Notion page ID

        Returns:
            True if sync successful, False otherwise
        """
        try:
            customer = await self.get_customer(customer_id)
            if not customer:
                logger.error(
                    f"Could not find customer {customer_id} to sync with Notion"
                )
                return False

            # Update custom fields to store Notion page ID
            update_data = {
                "fields": [{"name": "notion_page_id", "value": notion_page_id}]
            }

            # Also update the note field if it doesn't already have the Notion link
            note = customer.note or ""
            if "Notion Page:" not in note:
                notion_link = (
                    f"Notion Page: https://notion.so/{notion_page_id.replace('-', '')}"
                )
                if note:
                    note += f"\n\n{notion_link}"
                else:
                    note = notion_link

                update_data["note"] = note

            # Update the customer
            return await self.update_customer(customer_id, update_data)
        except Exception as e:
            logger.error(f"Error syncing customer {customer_id} to Notion: {e}")
            return False

    async def process_webhook(
        self, webhook_data: Dict[str, Any]
    ) -> Optional[AmeliaAppointment]:
        """
        Process a webhook notification from Amelia Booking.

        Args:
            webhook_data: Webhook payload data

        Returns:
            AmeliaAppointment if valid, None otherwise
        """
        try:
            # Extract the relevant data from the webhook payload
            if "type" not in webhook_data or "appointment" not in webhook_data:
                logger.error("Invalid Amelia webhook data: missing required fields")
                return None

            event_type = webhook_data.get("type")
            appointment_data = webhook_data.get("appointment")
            appointment_id = appointment_data.get("id")

            # Get the full appointment details from the API
            appointment = await self.get_appointment(appointment_id)

            if not appointment:
                logger.error(
                    f"Could not retrieve appointment {appointment_id} from webhook"
                )
                return None

            logger.info(
                f"Processed Amelia webhook: {event_type} for appointment {appointment_id}"
            )
            return appointment
        except Exception as e:
            logger.error(f"Error processing Amelia webhook: {e}")
            return None
