"""
The 7 Space Wellness Center Automation

This module provides automated wellness center management functionality including:
- Appointment scheduling and management
- Class capacity and waitlist management
- Client intake and onboarding automation
- Wellness program enrollment and tracking
- Wellness center analytics and reporting
"""

from .appointment_scheduler import AppointmentScheduler
from .class_capacity import ClassCapacityManager
from .client_intake import ClientIntakeAutomation
from .program_enrollment import ProgramEnrollmentManager
from .wellness_analytics import WellnessAnalytics

__all__ = [
    'AppointmentScheduler',
    'ClassCapacityManager',
    'ClientIntakeAutomation',
    'ProgramEnrollmentManager',
    'WellnessAnalytics'
]
