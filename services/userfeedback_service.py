"""
UserFeedback integration service for The HigherSelf Network Server.
This service handles user feedback collection via the UserFeedback API.
"""

import os
import requests
from typing import Dict, Any, List, Optional
from loguru import logger
from pydantic import BaseModel


class UserFeedbackConfig(BaseModel):
    """Configuration for UserFeedback API integration."""
    api_key: str
    project_id: str
    
    class Config:
        env_prefix = "USERFEEDBACK_"


class FeedbackItem(BaseModel):
    """Model representing a user feedback item."""
    id: Optional[str] = None
    user_id: Optional[str] = None
    email: Optional[str] = None
    name: Optional[str] = None
    feedback_text: str
    rating: Optional[int] = None
    source: Optional[str] = None
    page_url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None


class UserFeedbackService:
    """
    Service for interacting with the UserFeedback API.
    Feedback data is processed and stored in Notion as the central hub.
    """
    
    def __init__(self, api_key: str = None, project_id: str = None):
        """
        Initialize the UserFeedback service.
        
        Args:
            api_key: UserFeedback API key
            project_id: UserFeedback project ID
        """
        self.api_key = api_key or os.environ.get("USERFEEDBACK_API_KEY")
        self.project_id = project_id or os.environ.get("USERFEEDBACK_PROJECT_ID")
        self.base_url = "https://api.userfeedback.io/v1"
        
        if not self.api_key or not self.project_id:
            logger.warning("UserFeedback credentials not fully configured.")
    
    async def submit_feedback(self, feedback: FeedbackItem) -> Optional[str]:
        """
        Submit a new feedback entry.
        
        Args:
            feedback: FeedbackItem model with feedback data
            
        Returns:
            Feedback ID if successful, None otherwise
        """
        if not self.api_key or not self.project_id:
            logger.error("UserFeedback credentials not configured")
            return None
        
        url = f"{self.base_url}/projects/{self.project_id}/feedback"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "feedback_text": feedback.feedback_text,
        }
        
        # Add optional fields if provided
        if feedback.email:
            payload["email"] = feedback.email
        if feedback.name:
            payload["name"] = feedback.name
        if feedback.rating is not None:
            payload["rating"] = feedback.rating
        if feedback.source:
            payload["source"] = feedback.source
        if feedback.page_url:
            payload["page_url"] = feedback.page_url
        if feedback.metadata:
            payload["metadata"] = feedback.metadata
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            feedback_id = data.get("id")
            logger.info(f"Submitted feedback: {feedback_id}")
            return feedback_id
        except Exception as e:
            logger.error(f"Error submitting feedback: {e}")
            return None
    
    async def get_feedback(self, feedback_id: str) -> Optional[FeedbackItem]:
        """
        Get a specific feedback entry.
        
        Args:
            feedback_id: ID of the feedback to retrieve
            
        Returns:
            FeedbackItem if found, None otherwise
        """
        if not self.api_key or not self.project_id:
            logger.error("UserFeedback credentials not configured")
            return None
        
        url = f"{self.base_url}/projects/{self.project_id}/feedback/{feedback_id}"
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            feedback = FeedbackItem(
                id=data.get("id"),
                user_id=data.get("user_id"),
                email=data.get("email"),
                name=data.get("name"),
                feedback_text=data.get("feedback_text", ""),
                rating=data.get("rating"),
                source=data.get("source"),
                page_url=data.get("page_url"),
                metadata=data.get("metadata"),
                created_at=data.get("created_at")
            )
            
            return feedback
        except Exception as e:
            logger.error(f"Error getting feedback: {e}")
            return None
    
    async def list_feedback(self, limit: int = 50, offset: int = 0) -> List[FeedbackItem]:
        """
        List feedback entries for the project.
        
        Args:
            limit: Maximum number of entries to retrieve
            offset: Number of entries to skip
            
        Returns:
            List of FeedbackItem objects
        """
        if not self.api_key or not self.project_id:
            logger.error("UserFeedback credentials not configured")
            return []
        
        url = f"{self.base_url}/projects/{self.project_id}/feedback"
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        params = {
            "limit": limit,
            "offset": offset
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            feedback_items = []
            for item in data.get("data", []):
                feedback = FeedbackItem(
                    id=item.get("id"),
                    user_id=item.get("user_id"),
                    email=item.get("email"),
                    name=item.get("name"),
                    feedback_text=item.get("feedback_text", ""),
                    rating=item.get("rating"),
                    source=item.get("source"),
                    page_url=item.get("page_url"),
                    metadata=item.get("metadata"),
                    created_at=item.get("created_at")
                )
                feedback_items.append(feedback)
            
            logger.info(f"Retrieved {len(feedback_items)} feedback items")
            return feedback_items
        except Exception as e:
            logger.error(f"Error listing feedback: {e}")
            return []
    
    async def process_feedback_webhook(self, payload: Dict[str, Any]) -> Optional[FeedbackItem]:
        """
        Process a webhook notification from UserFeedback.
        
        Args:
            payload: Webhook payload
            
        Returns:
            FeedbackItem if valid, None otherwise
        """
        try:
            feedback_data = payload.get("feedback", {})
            if not feedback_data:
                logger.error("Invalid webhook payload: missing feedback data")
                return None
            
            feedback = FeedbackItem(
                id=feedback_data.get("id"),
                user_id=feedback_data.get("user_id"),
                email=feedback_data.get("email"),
                name=feedback_data.get("name"),
                feedback_text=feedback_data.get("feedback_text", ""),
                rating=feedback_data.get("rating"),
                source=feedback_data.get("source"),
                page_url=feedback_data.get("page_url"),
                metadata=feedback_data.get("metadata"),
                created_at=feedback_data.get("created_at")
            )
            
            logger.info(f"Processed feedback webhook for {feedback.id}")
            return feedback
        except Exception as e:
            logger.error(f"Error processing feedback webhook: {e}")
            return None
