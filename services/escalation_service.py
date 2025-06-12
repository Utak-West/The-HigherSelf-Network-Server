#!/usr/bin/env python3
"""
Escalation Service for Grace Fields Enhanced Customer Service

This service handles human escalation notifications and ticket management
for The HigherSelf Network Server customer service system.
"""

import asyncio
import json
import smtplib
import uuid
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, List, Optional

from loguru import logger
from pydantic import BaseModel, Field

from services.notion_service import NotionService


class EscalationTicket(BaseModel):
    """Model for escalation tickets."""

    ticket_id: str = Field(default_factory=lambda: f"ESC-{str(uuid.uuid4())[:8]}")
    request_id: str
    customer_email: str
    customer_name: Optional[str] = None
    business_entity: str
    issue_category: str
    description: str
    priority: str
    escalation_reason: str
    attempted_resolutions: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    assigned_human: Optional[str] = None
    status: str = "open"  # open, in_progress, resolved, closed
    resolution_notes: Optional[str] = None
    resolved_at: Optional[datetime] = None


class EscalationService:
    """
    Service for managing human escalations in the customer service system.

    Handles:
    - Creating escalation tickets
    - Sending notifications to human specialists
    - Tracking escalation status and resolution
    - Integration with Notion for ticket management
    """

    def __init__(
        self,
        notion_service: Optional[NotionService] = None,
        smtp_server: Optional[str] = None,
        smtp_port: int = 587,
        smtp_username: Optional[str] = None,
        smtp_password: Optional[str] = None,
        notification_email: Optional[str] = None,
    ):
        """Initialize the escalation service."""
        self.notion_service = notion_service
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.smtp_username = smtp_username
        self.smtp_password = smtp_password
        self.notification_email = notification_email

        # In-memory storage for tickets (in production, use database)
        self.tickets: Dict[str, EscalationTicket] = {}

        logger.info("Escalation service initialized")

    async def create_escalation_ticket(self, escalation_data: Dict[str, Any]) -> str:
        """
        Create a new escalation ticket and send notifications.

        Args:
            escalation_data: Dictionary containing escalation information

        Returns:
            The ticket ID for the created escalation
        """
        try:
            # Create escalation ticket
            ticket = EscalationTicket(
                request_id=escalation_data.get("request_id", ""),
                customer_email=escalation_data.get("customer_email", ""),
                customer_name=escalation_data.get("customer_name"),
                business_entity=escalation_data.get("business_entity", ""),
                issue_category=escalation_data.get("issue_category", ""),
                description=escalation_data.get("description", ""),
                priority=escalation_data.get("priority", "medium"),
                escalation_reason=escalation_data.get("escalation_reason", ""),
                attempted_resolutions=escalation_data.get("attempted_resolutions", []),
            )

            # Store ticket
            self.tickets[ticket.ticket_id] = ticket

            # Create Notion record if service available
            if self.notion_service:
                await self._create_notion_escalation_record(ticket)

            # Send notification email
            await self._send_escalation_notification(ticket)

            logger.info(
                f"Created escalation ticket {ticket.ticket_id} for {ticket.customer_email}"
            )

            return ticket.ticket_id

        except Exception as e:
            logger.error(f"Error creating escalation ticket: {e}")
            # Generate fallback ticket ID
            fallback_id = f"ESC-{escalation_data.get('request_id', 'UNKNOWN')[:8]}"
            return fallback_id

    async def _create_notion_escalation_record(
        self, ticket: EscalationTicket
    ) -> Optional[str]:
        """Create a record in Notion for the escalation ticket."""
        try:
            if not self.notion_service:
                return None

            # This would create a record in a Notion database for escalation tracking
            # For now, we'll log the action
            logger.info(f"Would create Notion record for escalation {ticket.ticket_id}")

            # In a real implementation:
            # escalation_page = await self.notion_service.create_page(
            #     database_id="escalation_database_id",
            #     properties={
            #         "Ticket ID": {"title": [{"text": {"content": ticket.ticket_id}}]},
            #         "Customer Email": {"email": ticket.customer_email},
            #         "Priority": {"select": {"name": ticket.priority.title()}},
            #         "Status": {"select": {"name": ticket.status.title()}},
            #         "Business Entity": {"select": {"name": ticket.business_entity.title()}},
            #         "Issue Category": {"select": {"name": ticket.issue_category.title()}},
            #         "Created": {"date": {"start": ticket.created_at.isoformat()}}
            #     }
            # )
            # return escalation_page.get("id")

            return None

        except Exception as e:
            logger.error(f"Error creating Notion escalation record: {e}")
            return None

    async def _send_escalation_notification(self, ticket: EscalationTicket) -> bool:
        """Send email notification for escalation."""
        try:
            if not all(
                [
                    self.smtp_server,
                    self.smtp_username,
                    self.smtp_password,
                    self.notification_email,
                ]
            ):
                logger.warning(
                    "Email configuration incomplete - escalation notification not sent"
                )
                return False

            # Create email message
            msg = MIMEMultipart()
            msg["From"] = self.smtp_username
            msg["To"] = self.notification_email
            msg[
                "Subject"
            ] = f"[URGENT - Grace Fields] Human intervention required - Ticket #{ticket.ticket_id}"

            # Create email body
            email_body = self._create_escalation_email_body(ticket)
            msg.attach(MIMEText(email_body, "plain"))

            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)

            logger.info(f"Escalation notification sent for ticket {ticket.ticket_id}")
            return True

        except Exception as e:
            logger.error(f"Error sending escalation notification: {e}")
            return False

    def _create_escalation_email_body(self, ticket: EscalationTicket) -> str:
        """Create the email body for escalation notifications."""
        attempted_resolutions_text = ""
        if ticket.attempted_resolutions:
            attempted_resolutions_text = "\n".join(
                [
                    f"- {res.get('agent', 'Unknown')}: {res.get('action', 'No action specified')} - {res.get('result', 'No result specified')}"
                    for res in ticket.attempted_resolutions
                ]
            )
        else:
            attempted_resolutions_text = "- No previous resolution attempts recorded"

        # Determine customer emotional state and business impact
        customer_emotional_state = "Unknown"
        business_impact_risk = "Medium"
        timeline_sensitivity = "Standard"

        if ticket.priority == "urgent":
            customer_emotional_state = "Highly concerned"
            business_impact_risk = "High"
            timeline_sensitivity = "Immediate"
        elif ticket.priority == "high":
            customer_emotional_state = "Concerned"
            business_impact_risk = "Medium-High"
            timeline_sensitivity = "Same Day"

        email_body = f"""
Severity Level: Level 4 - Human Required
Customer: {ticket.customer_name or 'Not provided'} ({ticket.customer_email})
Business Entity: {ticket.business_entity.replace('_', ' ').title()}
Issue Classification: {ticket.issue_category.replace('_', ' ').title()}

ESCALATION REASON: {ticket.escalation_reason}

CUSTOMER REQUEST:
{ticket.description}

Attempted Agent Resolutions:
{attempted_resolutions_text}

Recommended Human Action: Review case details and provide direct customer contact within priority timeframe
Customer Emotional State: {customer_emotional_state}
Business Impact Risk: {business_impact_risk}
Timeline Sensitivity: {timeline_sensitivity}

TICKET DETAILS:
- Ticket ID: {ticket.ticket_id}
- Request ID: {ticket.request_id}
- Created: {ticket.created_at.strftime('%Y-%m-%d %H:%M:%S')}
- Priority: {ticket.priority.upper()}

Please log into the Grace Fields system to view complete interaction history and take appropriate action.

This is an automated notification from The HigherSelf Network Server.
        """.strip()

        return email_body

    async def update_ticket_status(
        self,
        ticket_id: str,
        status: str,
        assigned_human: Optional[str] = None,
        resolution_notes: Optional[str] = None,
    ) -> bool:
        """Update the status of an escalation ticket."""
        try:
            if ticket_id not in self.tickets:
                logger.error(f"Ticket {ticket_id} not found")
                return False

            ticket = self.tickets[ticket_id]
            ticket.status = status

            if assigned_human:
                ticket.assigned_human = assigned_human

            if resolution_notes:
                ticket.resolution_notes = resolution_notes

            if status in ["resolved", "closed"]:
                ticket.resolved_at = datetime.now()

            logger.info(f"Updated ticket {ticket_id} status to {status}")

            # Update Notion record if available
            if self.notion_service:
                await self._update_notion_escalation_record(ticket)

            return True

        except Exception as e:
            logger.error(f"Error updating ticket {ticket_id}: {e}")
            return False

    async def _update_notion_escalation_record(self, ticket: EscalationTicket) -> bool:
        """Update the Notion record for an escalation ticket."""
        try:
            # In a real implementation, this would update the Notion page
            logger.info(f"Would update Notion record for ticket {ticket.ticket_id}")
            return True

        except Exception as e:
            logger.error(f"Error updating Notion escalation record: {e}")
            return False

    async def get_ticket(self, ticket_id: str) -> Optional[EscalationTicket]:
        """Retrieve an escalation ticket by ID."""
        return self.tickets.get(ticket_id)

    async def list_open_tickets(self) -> List[EscalationTicket]:
        """Get all open escalation tickets."""
        return [
            ticket
            for ticket in self.tickets.values()
            if ticket.status in ["open", "in_progress"]
        ]

    async def get_escalation_metrics(self) -> Dict[str, Any]:
        """Get metrics about escalation performance."""
        try:
            total_tickets = len(self.tickets)
            open_tickets = len([t for t in self.tickets.values() if t.status == "open"])
            resolved_tickets = len(
                [t for t in self.tickets.values() if t.status == "resolved"]
            )

            # Calculate average resolution time for resolved tickets
            resolved_with_times = [
                t
                for t in self.tickets.values()
                if t.status == "resolved" and t.resolved_at
            ]

            avg_resolution_hours = 0.0
            if resolved_with_times:
                total_resolution_time = sum(
                    [
                        (t.resolved_at - t.created_at).total_seconds() / 3600
                        for t in resolved_with_times
                    ]
                )
                avg_resolution_hours = total_resolution_time / len(resolved_with_times)

            return {
                "total_escalations": total_tickets,
                "open_escalations": open_tickets,
                "resolved_escalations": resolved_tickets,
                "resolution_rate": (
                    round((resolved_tickets / total_tickets * 100), 2)
                    if total_tickets > 0
                    else 0
                ),
                "average_resolution_hours": round(avg_resolution_hours, 2),
                "escalations_by_priority": self._get_escalations_by_priority(),
                "escalations_by_category": self._get_escalations_by_category(),
            }

        except Exception as e:
            logger.error(f"Error calculating escalation metrics: {e}")
            return {"error": str(e)}

    def _get_escalations_by_priority(self) -> Dict[str, int]:
        """Get count of escalations by priority level."""
        priority_counts = {"urgent": 0, "high": 0, "medium": 0, "low": 0}
        for ticket in self.tickets.values():
            if ticket.priority in priority_counts:
                priority_counts[ticket.priority] += 1
        return priority_counts

    def _get_escalations_by_category(self) -> Dict[str, int]:
        """Get count of escalations by issue category."""
        category_counts = {}
        for ticket in self.tickets.values():
            category = ticket.issue_category
            category_counts[category] = category_counts.get(category, 0) + 1
        return category_counts
