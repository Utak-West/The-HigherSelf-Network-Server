"""
Analysis and qualification tools for LangChain agents.
"""

from langchain.tools import BaseTool
from typing import Type, Dict, Any, List
from pydantic import BaseModel, Field
import json
import re
from datetime import datetime

from loguru import logger

class LeadQualificationInput(BaseModel):
    lead_data: str = Field(description="Lead data as JSON string")

class LeadQualificationTool(BaseTool):
    name = "qualify_lead"
    description = "Analyze and qualify a lead based on provided data. Returns qualification score and recommendations."
    args_schema: Type[BaseModel] = LeadQualificationInput
    
    def _run(self, lead_data: str) -> str:
        """Qualify lead using business rules."""
        try:
            data = json.loads(lead_data) if isinstance(lead_data, str) else lead_data
            
            score = 0
            factors = []
            recommendations = []
            
            # Email quality (2 points)
            email = data.get("email", "")
            if email and "@" in email and "." in email:
                score += 2
                factors.append("Valid email provided")
            elif email:
                score += 1
                factors.append("Email provided but may need validation")
            
            # Message quality and intent (3 points)
            message = data.get("message", "").lower()
            high_intent_words = ["consultation", "retreat", "workshop", "booking", "appointment", "schedule", "hire", "purchase"]
            medium_intent_words = ["interested", "learn more", "information", "details", "pricing"]
            
            if any(word in message for word in high_intent_words):
                score += 3
                factors.append("High-intent keywords detected")
                recommendations.append("Immediate follow-up recommended")
            elif any(word in message for word in medium_intent_words):
                score += 2
                factors.append("Medium-intent keywords detected")
                recommendations.append("Follow-up within 24 hours")
            elif message:
                score += 1
                factors.append("Message provided")
            
            # Contact information completeness (2 points)
            if data.get("phone"):
                score += 2
                factors.append("Phone number provided")
                recommendations.append("Phone follow-up possible")
            
            # Urgency indicators (2 points)
            urgency_words = ["urgent", "soon", "asap", "immediately", "today", "this week", "quickly"]
            if any(word in message for word in urgency_words):
                score += 2
                factors.append("Urgency indicated")
                recommendations.append("Prioritize immediate response")
            
            # Budget/investment awareness (1 point)
            budget_words = ["budget", "investment", "cost", "price", "fee", "rate", "affordable", "expensive"]
            if any(word in message for word in budget_words):
                score += 1
                factors.append("Budget awareness shown")
            
            # Business type relevance (1 point)
            business_indicators = {
                "art": ["art", "gallery", "exhibition", "artist", "painting", "sculpture"],
                "wellness": ["wellness", "health", "meditation", "yoga", "healing", "therapy", "retreat"],
                "consultancy": ["consulting", "business", "strategy", "advice", "guidance", "coaching"]
            }
            
            for business_type, keywords in business_indicators.items():
                if any(keyword in message for keyword in keywords):
                    score += 1
                    factors.append(f"Relevant to {business_type} business")
                    break
            
            # Company/organization indicators (1 point)
            if data.get("company") or any(word in message for word in ["company", "organization", "team", "group"]):
                score += 1
                factors.append("Business/organization inquiry")
            
            # Determine quality level
            if score >= 8:
                quality_level = "Excellent"
            elif score >= 6:
                quality_level = "High"
            elif score >= 4:
                quality_level = "Medium"
            elif score >= 2:
                quality_level = "Low"
            else:
                quality_level = "Very Low"
            
            # Generate recommendations based on score
            if not recommendations:
                if score >= 6:
                    recommendations.append("High priority - immediate follow-up recommended")
                elif score >= 4:
                    recommendations.append("Medium priority - follow-up within 24 hours")
                else:
                    recommendations.append("Low priority - add to nurture sequence")
            
            result = {
                "score": score,
                "quality_level": quality_level,
                "factors": factors,
                "recommendations": recommendations,
                "analysis_timestamp": datetime.utcnow().isoformat()
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Error qualifying lead: {e}")
            return json.dumps({
                "error": f"Error qualifying lead: {str(e)}",
                "score": 0,
                "quality_level": "Unknown"
            })
    
    async def _arun(self, lead_data: str) -> str:
        """Async version."""
        return self._run(lead_data)

class ContentAnalysisInput(BaseModel):
    content: str = Field(description="Content to analyze")
    analysis_type: str = Field(default="general", description="Type of analysis: sentiment, intent, topic, quality")

class ContentAnalysisTool(BaseTool):
    name = "analyze_content"
    description = "Analyze content for sentiment, intent, topics, or quality. Useful for understanding customer communications."
    args_schema: Type[BaseModel] = ContentAnalysisInput
    
    def _run(self, content: str, analysis_type: str = "general") -> str:
        """Analyze content based on specified type."""
        try:
            results = {}
            
            if analysis_type in ["general", "sentiment"]:
                results["sentiment"] = self._analyze_sentiment(content)
            
            if analysis_type in ["general", "intent"]:
                results["intent"] = self._analyze_intent(content)
            
            if analysis_type in ["general", "topic"]:
                results["topics"] = self._extract_topics(content)
            
            if analysis_type in ["general", "quality"]:
                results["quality"] = self._assess_quality(content)
            
            results["analysis_timestamp"] = datetime.utcnow().isoformat()
            
            return json.dumps(results, indent=2)
            
        except Exception as e:
            logger.error(f"Error analyzing content: {e}")
            return json.dumps({"error": f"Error analyzing content: {str(e)}"})
    
    async def _arun(self, content: str, analysis_type: str = "general") -> str:
        """Async version."""
        return self._run(content, analysis_type)
    
    def _analyze_sentiment(self, content: str) -> Dict[str, Any]:
        """Simple sentiment analysis."""
        content_lower = content.lower()
        
        positive_words = ["great", "excellent", "amazing", "wonderful", "fantastic", "love", "perfect", "awesome", "brilliant", "outstanding"]
        negative_words = ["terrible", "awful", "horrible", "hate", "worst", "bad", "disappointing", "frustrated", "angry", "upset"]
        neutral_words = ["okay", "fine", "average", "normal", "standard"]
        
        positive_count = sum(1 for word in positive_words if word in content_lower)
        negative_count = sum(1 for word in negative_words if word in content_lower)
        neutral_count = sum(1 for word in neutral_words if word in content_lower)
        
        if positive_count > negative_count and positive_count > neutral_count:
            sentiment = "positive"
            confidence = min(0.9, 0.5 + (positive_count * 0.1))
        elif negative_count > positive_count and negative_count > neutral_count:
            sentiment = "negative"
            confidence = min(0.9, 0.5 + (negative_count * 0.1))
        else:
            sentiment = "neutral"
            confidence = 0.6
        
        return {
            "sentiment": sentiment,
            "confidence": round(confidence, 2),
            "positive_indicators": positive_count,
            "negative_indicators": negative_count
        }
    
    def _analyze_intent(self, content: str) -> Dict[str, Any]:
        """Analyze user intent."""
        content_lower = content.lower()
        
        intent_patterns = {
            "purchase": ["buy", "purchase", "order", "get", "want to", "need to", "looking for"],
            "inquiry": ["question", "ask", "wondering", "curious", "information", "details", "tell me"],
            "booking": ["book", "schedule", "appointment", "reserve", "availability", "when can"],
            "complaint": ["problem", "issue", "wrong", "error", "not working", "disappointed", "frustrated"],
            "support": ["help", "support", "assistance", "guide", "how to", "can you"],
            "compliment": ["thank", "great", "excellent", "amazing", "love", "appreciate"]
        }
        
        detected_intents = []
        for intent, patterns in intent_patterns.items():
            if any(pattern in content_lower for pattern in patterns):
                detected_intents.append(intent)
        
        primary_intent = detected_intents[0] if detected_intents else "general"
        
        return {
            "primary_intent": primary_intent,
            "all_intents": detected_intents,
            "confidence": 0.8 if detected_intents else 0.4
        }
    
    def _extract_topics(self, content: str) -> List[str]:
        """Extract main topics from content."""
        content_lower = content.lower()
        
        topic_keywords = {
            "art": ["art", "painting", "sculpture", "gallery", "exhibition", "artist"],
            "wellness": ["wellness", "health", "meditation", "yoga", "healing", "therapy"],
            "business": ["business", "strategy", "consulting", "advice", "growth", "marketing"],
            "booking": ["appointment", "schedule", "booking", "reservation", "availability"],
            "pricing": ["price", "cost", "fee", "rate", "budget", "investment"],
            "location": ["where", "location", "address", "directions", "visit"],
            "timing": ["when", "time", "schedule", "hours", "availability", "date"]
        }
        
        detected_topics = []
        for topic, keywords in topic_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                detected_topics.append(topic)
        
        return detected_topics
    
    def _assess_quality(self, content: str) -> Dict[str, Any]:
        """Assess content quality."""
        word_count = len(content.split())
        char_count = len(content)
        sentence_count = len([s for s in content.split('.') if s.strip()])
        
        # Quality indicators
        has_proper_grammar = not bool(re.search(r'[a-z][A-Z]', content))  # Simple check
        has_punctuation = bool(re.search(r'[.!?]', content))
        avg_word_length = sum(len(word) for word in content.split()) / max(word_count, 1)
        
        quality_score = 0
        if word_count >= 10:
            quality_score += 2
        elif word_count >= 5:
            quality_score += 1
        
        if has_proper_grammar:
            quality_score += 1
        
        if has_punctuation:
            quality_score += 1
        
        if avg_word_length > 4:
            quality_score += 1
        
        quality_level = "High" if quality_score >= 4 else "Medium" if quality_score >= 2 else "Low"
        
        return {
            "quality_level": quality_level,
            "quality_score": quality_score,
            "word_count": word_count,
            "character_count": char_count,
            "sentence_count": sentence_count,
            "average_word_length": round(avg_word_length, 1)
        }
