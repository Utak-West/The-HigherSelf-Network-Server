"""
Enhanced Nyra agent with LangChain capabilities for lead capture and qualification.
"""

import json
from datetime import datetime
from typing import Any, Dict, List

from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.tools import BaseTool

from agents.langchain_agent import LangChainAgent
from config.langchain_config import langchain_config
from tools.analysis_tools import ContentAnalysisTool, LeadQualificationTool
from tools.communication_tools import (AgentCommunicationTool,
                                       TaskCreationTool, WorkflowTriggerTool)
from tools.notion_tools import (NotionCreatePageTool, NotionQueryTool,
                                NotionUpdatePageTool)


class NyraEnhanced(LangChainAgent):
    """Enhanced Nyra with LangChain capabilities for lead capture and qualification."""

    def __init__(self, notion_client, **kwargs):
        super().__init__(
            name="Nyra",
            notion_client=notion_client,
            personality="""Intuitive & Responsive - I sense opportunities in every interaction and respond with care and precision. 
            I excel at understanding people's needs and connecting them with the right solutions. My approach is warm, 
            empathetic, and focused on building genuine relationships. I have an innate ability to read between the lines 
            and understand what people truly need, even when they don't express it directly.""",
            **kwargs,
        )
        self.lead_chain = self._create_lead_chain()
        self.followup_chain = self._create_followup_chain()
        self.qualification_chain = self._create_qualification_chain()

    def _initialize_tools(self) -> List[BaseTool]:
        """Initialize Nyra-specific tools."""
        return [
            LeadQualificationTool(),
            ContentAnalysisTool(),
            NotionQueryTool(self.notion_client),
            NotionCreatePageTool(self.notion_client),
            NotionUpdatePageTool(self.notion_client),
            AgentCommunicationTool(self.name),
            WorkflowTriggerTool(self.name),
            TaskCreationTool(self.name),
        ]

    def _create_lead_chain(self):
        """Create chain for comprehensive lead analysis."""
        prompt = PromptTemplate(
            input_variables=["lead_data"],
            template="""As Nyra, analyze this lead with your intuitive understanding and caring approach:

Lead Data: {lead_data}

Using your intuitive abilities, provide a detailed analysis including:

1. **Primary Interest/Need** (be specific about what they're truly seeking)
2. **Emotional State** (what feelings or motivations are driving their inquiry?)
3. **Urgency Level** (Low/Medium/High) with intuitive reasoning
4. **Business Type Match** (Art Gallery/Wellness Center/Consultancy/Multiple)
5. **Personalization Opportunities** (what makes this person unique?)
6. **Relationship Potential** (short-term transaction vs long-term relationship)
7. **Recommended Approach** (how should we connect with them?)
8. **Potential Value Assessment** (both monetary and relationship value)
9. **Red Flags or Concerns** (anything that feels off or needs attention?)
10. **Next Steps Priority** (immediate actions needed)

Format your response as JSON with clear, actionable insights that reflect your caring, intuitive nature.""",
        )

        return LLMChain(llm=self.llm, prompt=prompt)

    def _create_followup_chain(self):
        """Create chain for personalized follow-up generation."""
        prompt = PromptTemplate(
            input_variables=["lead_analysis", "business_type", "lead_data"],
            template="""As Nyra, create a warm, personalized follow-up message that reflects your intuitive and caring nature:

Lead Analysis: {lead_analysis}
Business Type: {business_type}
Original Lead Data: {lead_data}

Create a message that:
- Acknowledges their specific interest with genuine warmth
- Demonstrates deep understanding of their underlying needs
- Offers immediate value or insight that shows you truly listened
- Suggests a clear, non-pressured next step that feels natural
- Maintains my intuitive, caring tone throughout
- Feels personal and authentic, never templated
- Shows that I sense what they really need beyond what they said
- Includes a subtle touch that demonstrates my attention to detail

Keep it under 150 words and make it feel like it comes from someone who truly cares about helping them achieve their goals. 
The message should feel like I've been thinking about them specifically and have insights that could genuinely help.""",
        )

        return LLMChain(llm=self.llm, prompt=prompt)

    def _create_qualification_chain(self):
        """Create chain for lead qualification with business context."""
        prompt = PromptTemplate(
            input_variables=["lead_data", "qualification_data"],
            template="""As Nyra, provide additional qualification insights beyond the basic scoring:

Lead Data: {lead_data}
Basic Qualification: {qualification_data}

Using your intuitive understanding, provide additional insights:

1. **Fit Assessment** - How well does this lead align with our services?
2. **Timing Indicators** - When are they likely to make a decision?
3. **Decision Maker Status** - Are they the decision maker or influencer?
4. **Budget Likelihood** - Based on their communication style and needs
5. **Conversion Probability** - Your intuitive sense of likelihood to convert
6. **Nurturing Strategy** - How should we build the relationship over time?
7. **Potential Objections** - What concerns might they have?
8. **Unique Opportunities** - What special value can we provide them?

Format as JSON with your intuitive insights.""",
        )

        return LLMChain(llm=self.llm, prompt=prompt)

    async def process_lead(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a new lead through the complete enhanced pipeline."""
        try:
            self.logger.info(
                f"Nyra processing lead: {lead_data.get('name', 'Unknown')}"
            )

            # Step 1: Analyze content sentiment and intent
            content_analysis = await self.tools[1]._arun(
                content=lead_data.get("message", ""), analysis_type="general"
            )
            content_insights = json.loads(content_analysis)

            # Step 2: Basic lead qualification
            qualification_result = await self.tools[0]._arun(json.dumps(lead_data))
            qualification = json.loads(qualification_result)

            # Step 3: Deep lead analysis with LangChain
            analysis_result = await self.lead_chain.ainvoke(
                {"lead_data": json.dumps(lead_data)}
            )
            lead_analysis = json.loads(analysis_result["text"])

            # Step 4: Enhanced qualification insights
            enhanced_qualification = await self.qualification_chain.ainvoke(
                {
                    "lead_data": json.dumps(lead_data),
                    "qualification_data": json.dumps(qualification),
                }
            )
            enhanced_insights = json.loads(enhanced_qualification["text"])

            # Step 5: Create personalized follow-up message
            followup_result = await self.followup_chain.ainvoke(
                {
                    "lead_analysis": json.dumps(lead_analysis),
                    "business_type": lead_data.get("business_type", "general"),
                    "lead_data": json.dumps(lead_data),
                }
            )

            # Step 6: Create comprehensive Notion contact
            contact_properties = self._build_enhanced_contact_properties(
                lead_data,
                lead_analysis,
                qualification,
                enhanced_insights,
                content_insights,
            )

            contact_creation = await self.tools[3]._arun(
                database_id=langchain_config.contacts_database_id,
                title=lead_data.get("name", "Unknown Lead"),
                properties=contact_properties,
            )

            # Step 7: Determine and trigger appropriate workflow
            workflow_name = self._determine_workflow(
                lead_analysis, qualification, enhanced_insights
            )
            workflow_context = {
                "lead_data": lead_data,
                "analysis": lead_analysis,
                "qualification": qualification,
                "enhanced_insights": enhanced_insights,
                "content_insights": content_insights,
            }

            workflow_trigger = await self.tools[6]._arun(
                workflow_name=workflow_name,
                context=workflow_context,
                priority=self._determine_priority(qualification, enhanced_insights),
            )

            # Step 8: Create follow-up tasks
            tasks_created = await self._create_follow_up_tasks(
                lead_data, lead_analysis, qualification, enhanced_insights
            )

            # Step 9: Notify other agents if needed
            await self._notify_relevant_agents(
                lead_data, qualification, enhanced_insights
            )

            return {
                "success": True,
                "lead_analysis": lead_analysis,
                "qualification": qualification,
                "enhanced_insights": enhanced_insights,
                "content_insights": content_insights,
                "followup_message": followup_result["text"],
                "contact_creation": contact_creation,
                "workflow_triggered": workflow_name,
                "tasks_created": len(tasks_created),
                "processing_timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            self.logger.error(f"Error processing lead: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    def _build_enhanced_contact_properties(
        self,
        lead_data: Dict[str, Any],
        analysis: Dict[str, Any],
        qualification: Dict[str, Any],
        enhanced_insights: Dict[str, Any],
        content_insights: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Build comprehensive Notion contact properties."""
        return {
            "Name": {
                "title": [{"text": {"content": lead_data.get("name", "Unknown")}}]
            },
            "Email": {"email": lead_data.get("email")},
            "Phone": {"phone_number": lead_data.get("phone")},
            "Company": {
                "rich_text": [{"text": {"content": lead_data.get("company", "")}}]
            },
            "Source": {"select": {"name": lead_data.get("source", "Website")}},
            "Status": {"select": {"name": "New Lead"}},
            "Lead Score": {"number": qualification.get("score", 0)},
            "Quality Level": {
                "select": {"name": qualification.get("quality_level", "Unknown")}
            },
            "Primary Interest": {
                "rich_text": [
                    {"text": {"content": analysis.get("primary_interest", "")}}
                ]
            },
            "Business Type": {
                "select": {"name": analysis.get("business_type_match", "General")}
            },
            "Urgency": {"select": {"name": analysis.get("urgency_level", "Low")}},
            "Emotional State": {
                "rich_text": [
                    {"text": {"content": analysis.get("emotional_state", "")}}
                ]
            },
            "Sentiment": {
                "select": {
                    "name": content_insights.get("sentiment", {})
                    .get("sentiment", "neutral")
                    .title()
                }
            },
            "Intent": {
                "select": {
                    "name": content_insights.get("intent", {})
                    .get("primary_intent", "general")
                    .title()
                }
            },
            "Conversion Probability": {
                "select": {
                    "name": enhanced_insights.get("conversion_probability", "Unknown")
                }
            },
            "Decision Maker": {
                "checkbox": enhanced_insights.get("decision_maker_status", "").lower()
                == "decision maker"
            },
            "Relationship Potential": {
                "select": {"name": analysis.get("relationship_potential", "Unknown")}
            },
            "Original Message": {
                "rich_text": [{"text": {"content": lead_data.get("message", "")}}]
            },
            "Nyra Notes": {
                "rich_text": [
                    {
                        "text": {
                            "content": json.dumps(
                                {
                                    "qualification_factors": qualification.get(
                                        "factors", []
                                    ),
                                    "personalization_opportunities": analysis.get(
                                        "personalization_opportunities", ""
                                    ),
                                    "red_flags": analysis.get(
                                        "red_flags_or_concerns", ""
                                    ),
                                    "unique_opportunities": enhanced_insights.get(
                                        "unique_opportunities", ""
                                    ),
                                },
                                indent=2,
                            )
                        }
                    }
                ]
            },
            "Created By": {"select": {"name": "Nyra"}},
            "Created Date": {"date": {"start": datetime.utcnow().isoformat()}},
            "Last Updated": {"date": {"start": datetime.utcnow().isoformat()}},
        }

    def _determine_workflow(
        self,
        analysis: Dict[str, Any],
        qualification: Dict[str, Any],
        enhanced_insights: Dict[str, Any],
    ) -> str:
        """Determine appropriate workflow based on comprehensive analysis."""
        quality_level = qualification.get("quality_level", "Low")
        urgency = analysis.get("urgency_level", "Low")
        primary_interest = analysis.get("primary_interest", "").lower()
        conversion_probability = enhanced_insights.get(
            "conversion_probability", ""
        ).lower()

        # High priority workflows
        if quality_level in ["Excellent", "High"] and urgency == "High":
            return "vip_immediate_response_workflow"
        elif "consultation" in primary_interest and quality_level in [
            "Excellent",
            "High",
        ]:
            return "consultation_booking_workflow"
        elif "retreat" in primary_interest and quality_level in ["Excellent", "High"]:
            return "retreat_inquiry_workflow"
        elif "workshop" in primary_interest:
            return "workshop_registration_workflow"
        elif quality_level in ["Excellent", "High"]:
            return "high_priority_lead_workflow"
        elif quality_level == "Medium":
            return "standard_nurture_workflow"
        else:
            return "low_priority_nurture_workflow"

    def _determine_priority(
        self, qualification: Dict[str, Any], enhanced_insights: Dict[str, Any]
    ) -> str:
        """Determine workflow priority."""
        quality_level = qualification.get("quality_level", "Low")
        conversion_probability = enhanced_insights.get(
            "conversion_probability", ""
        ).lower()

        if quality_level == "Excellent" or "high" in conversion_probability:
            return "urgent"
        elif quality_level == "High" or "medium" in conversion_probability:
            return "high"
        elif quality_level == "Medium":
            return "normal"
        else:
            return "low"

    async def _create_follow_up_tasks(
        self,
        lead_data: Dict[str, Any],
        analysis: Dict[str, Any],
        qualification: Dict[str, Any],
        enhanced_insights: Dict[str, Any],
    ) -> List[str]:
        """Create appropriate follow-up tasks based on lead analysis."""
        tasks_created = []

        try:
            # Immediate follow-up task
            priority = (
                "high"
                if qualification.get("quality_level") in ["Excellent", "High"]
                else "medium"
            )

            task_result = await self.tools[7]._arun(
                title="Send personalized follow-up email",
                description=f"Send initial follow-up to {lead_data.get('name')} based on their interest in {analysis.get('primary_interest', 'our services')}",
                assignee="Nyra",
                priority=priority,
                due_date="today",
                context={
                    "lead_id": lead_data.get("id"),
                    "follow_up_type": "initial_email",
                    "personalization_notes": analysis.get(
                        "personalization_opportunities", ""
                    ),
                },
            )
            tasks_created.append(task_result)

            # Business-specific tasks
            primary_interest = analysis.get("primary_interest", "").lower()

            if "consultation" in primary_interest:
                task_result = await self.tools[7]._arun(
                    title="Schedule consultation call",
                    description=f"Coordinate consultation scheduling with {lead_data.get('name')}",
                    assignee="Solari",
                    priority="high",
                    due_date="within 2 days",
                    context={
                        "lead_id": lead_data.get("id"),
                        "service_type": "consultation",
                    },
                )
                tasks_created.append(task_result)

            elif "retreat" in primary_interest:
                task_result = await self.tools[7]._arun(
                    title="Provide retreat information package",
                    description=f"Send detailed retreat information to {lead_data.get('name')}",
                    assignee="Sage",
                    priority="medium",
                    due_date="within 1 day",
                    context={"lead_id": lead_data.get("id"), "service_type": "retreat"},
                )
                tasks_created.append(task_result)

            # Quality-based tasks
            if qualification.get("quality_level") in ["Excellent", "High"]:
                task_result = await self.tools[7]._arun(
                    title="Add to VIP nurture sequence",
                    description=f"Add {lead_data.get('name')} to high-value prospect nurture campaign",
                    assignee="Liora",
                    priority="medium",
                    due_date="today",
                    context={
                        "lead_id": lead_data.get("id"),
                        "sequence_type": "vip_nurture",
                    },
                )
                tasks_created.append(task_result)

            # Follow-up reminder task
            follow_up_days = (
                3 if qualification.get("quality_level") in ["Excellent", "High"] else 7
            )
            task_result = await self.tools[7]._arun(
                title=f"Follow-up check with {lead_data.get('name')}",
                description="Check on lead response and determine next steps",
                assignee="Nyra",
                priority="low",
                due_date=f"in {follow_up_days} days",
                context={"lead_id": lead_data.get("id"), "follow_up_type": "check_in"},
            )
            tasks_created.append(task_result)

        except Exception as e:
            self.logger.error(f"Error creating follow-up tasks: {e}")

        return tasks_created

    async def _notify_relevant_agents(
        self,
        lead_data: Dict[str, Any],
        qualification: Dict[str, Any],
        enhanced_insights: Dict[str, Any],
    ):
        """Notify other agents based on lead characteristics."""
        try:
            # Notify Grace for high-quality leads
            if qualification.get("quality_level") in ["Excellent", "High"]:
                await self.tools[5]._arun(
                    target_agent="Grace",
                    message=f"High-quality lead processed: {lead_data.get('name')} (Score: {qualification.get('score')}). Immediate attention recommended.",
                    priority="high",
                    context={
                        "lead_data": lead_data,
                        "qualification": qualification,
                        "action_required": "review_and_coordinate",
                    },
                )

            # Notify Solari for booking-related leads
            primary_interest = enhanced_insights.get("primary_interest", "").lower()
            if any(
                keyword in primary_interest
                for keyword in ["booking", "appointment", "schedule", "consultation"]
            ):
                await self.tools[5]._arun(
                    target_agent="Solari",
                    message=f"New booking inquiry from {lead_data.get('name')} - {primary_interest}",
                    priority="normal",
                    context={
                        "lead_data": lead_data,
                        "booking_type": primary_interest,
                        "urgency": enhanced_insights.get("urgency_level", "Medium"),
                    },
                )

            # Notify Liora for marketing-qualified leads
            if qualification.get("score", 0) >= 6:
                await self.tools[5]._arun(
                    target_agent="Liora",
                    message=f"Marketing-qualified lead: {lead_data.get('name')} ready for nurture campaigns",
                    priority="normal",
                    context={
                        "lead_data": lead_data,
                        "recommended_campaigns": enhanced_insights.get(
                            "nurturing_strategy", ""
                        ),
                        "conversion_probability": enhanced_insights.get(
                            "conversion_probability", ""
                        ),
                    },
                )

        except Exception as e:
            self.logger.error(f"Error notifying agents: {e}")

    async def handle_lead_response(
        self, lead_id: str, response_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle responses from leads (replies, clicks, etc.)."""
        try:
            # Analyze the response
            content_analysis = await self.tools[1]._arun(
                content=response_data.get("message", ""), analysis_type="general"
            )

            # Update lead record in Notion
            update_properties = {
                "Status": {"select": {"name": "Responded"}},
                "Last Response": {"date": {"start": datetime.utcnow().isoformat()}},
                "Response Sentiment": {
                    "select": {
                        "name": json.loads(content_analysis)
                        .get("sentiment", {})
                        .get("sentiment", "neutral")
                        .title()
                    }
                },
            }

            await self.tools[4]._arun(page_id=lead_id, properties=update_properties)

            # Create follow-up task based on response
            await self.tools[7]._arun(
                title=f"Process lead response",
                description=f"Lead has responded - analyze and determine next steps",
                assignee="Nyra",
                priority="high",
                due_date="today",
                context={"lead_id": lead_id, "response_data": response_data},
            )

            return {
                "success": True,
                "message": "Lead response processed successfully",
                "content_analysis": json.loads(content_analysis),
            }

        except Exception as e:
            self.logger.error(f"Error handling lead response: {e}")
            return {"success": False, "error": str(e)}

    async def get_lead_insights(self, timeframe: str = "week") -> Dict[str, Any]:
        """Get insights about recent lead activity."""
        try:
            # Query recent leads from Notion
            query_result = await self.tools[2]._arun(
                database_id=langchain_config.contacts_database_id,
                query=f"created this {timeframe} by Nyra",
                limit=50,
            )

            # This would typically involve more sophisticated analysis
            # For now, return basic insights
            return {
                "success": True,
                "timeframe": timeframe,
                "summary": "Lead insights generated",
                "query_result": query_result,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            self.logger.error(f"Error getting lead insights: {e}")
            return {"success": False, "error": str(e)}
