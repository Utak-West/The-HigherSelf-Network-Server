#!/usr/bin/env python3
"""
Contact Engagement Templates

This module provides comprehensive email templates, notification messages,
and engagement sequences for different contact types and business entities.
All templates support dynamic personalization based on contact data.

Template Categories:
- Welcome sequences for new contacts
- Follow-up sequences based on engagement
- Business entity-specific messaging
- Lead source-specific communications
- Re-engagement campaigns for inactive contacts
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum


class TemplateType(Enum):
    """Types of engagement templates."""
    WELCOME = "welcome"
    FOLLOW_UP = "follow_up"
    NURTURE = "nurture"
    CONVERSION = "conversion"
    RE_ENGAGEMENT = "re_engagement"
    THANK_YOU = "thank_you"
    NOTIFICATION = "notification"


class PersonalizationLevel(Enum):
    """Levels of template personalization."""
    BASIC = "basic"  # Name and email only
    STANDARD = "standard"  # Include contact type and lead source
    ADVANCED = "advanced"  # Full contact profile and behavior data
    PREMIUM = "premium"  # AI-generated personalized content


@dataclass
class EngagementTemplate:
    """Template for contact engagement communications."""
    template_id: str
    name: str
    template_type: TemplateType
    business_entity: str
    contact_types: List[str]
    subject_line: str
    content: str
    personalization_level: PersonalizationLevel
    variables: List[str]
    follow_up_days: Optional[int] = None
    success_metrics: List[str] = None


class ContactEngagementTemplates:
    """
    Comprehensive template library for contact engagement.
    
    Provides personalized templates for different contact types,
    business entities, and engagement scenarios.
    """

    def __init__(self):
        """Initialize the template library."""
        self.templates = self._initialize_templates()
        self.personalization_rules = self._initialize_personalization_rules()

    def _initialize_templates(self) -> Dict[str, EngagementTemplate]:
        """Initialize all engagement templates."""
        return {
            # The 7 Space Templates
            "the7space_artist_welcome": EngagementTemplate(
                template_id="the7space_artist_welcome",
                name="The 7 Space Artist Welcome",
                template_type=TemplateType.WELCOME,
                business_entity="The 7 Space",
                contact_types=["Artist", "Gallery Contact"],
                subject_line="Welcome to The 7 Space Artist Community, {first_name}!",
                content="""
Dear {first_name},

Welcome to The 7 Space, where creativity meets community and wellness intersects with artistic expression.

We're thrilled to have you join our vibrant community of artists, creators, and visionaries. The 7 Space is more than just a gallery – we're a sanctuary for artistic growth, collaboration, and holistic well-being.

**What awaits you:**
• Exhibition opportunities in our curated gallery space
• Wellness programs designed specifically for creative professionals
• Networking events with fellow artists and art enthusiasts
• Workshops and masterclasses to enhance your craft
• A supportive community that celebrates your unique artistic journey

**Next Steps:**
1. Complete your artist profile: [Profile Link]
2. Browse our upcoming exhibitions: [Exhibitions Link]
3. Explore our wellness programs: [Wellness Link]
4. Join our artist community forum: [Community Link]

We'd love to learn more about your artistic practice and how The 7 Space can support your creative journey. Feel free to reply to this email with your portfolio or any questions you might have.

Looking forward to seeing your art grace our walls and your presence enrich our community.

With creative energy,
The 7 Space Team

P.S. Follow us on Instagram @the7space for daily inspiration and behind-the-scenes glimpses of our artist community.
                """,
                personalization_level=PersonalizationLevel.STANDARD,
                variables=["first_name", "last_name", "email", "contact_type"],
                follow_up_days=7,
                success_metrics=["email_open", "link_clicks", "profile_completion", "event_registration"]
            ),

            "the7space_gallery_inquiry": EngagementTemplate(
                template_id="the7space_gallery_inquiry",
                name="The 7 Space Gallery Inquiry Response",
                template_type=TemplateType.FOLLOW_UP,
                business_entity="The 7 Space",
                contact_types=["Gallery Contact", "Business Contact"],
                subject_line="Your Gallery Inquiry - Let's Create Something Beautiful Together",
                content="""
Hello {first_name},

Thank you for your interest in The 7 Space gallery. We're excited about the possibility of collaborating with you.

The 7 Space is a unique venue that combines contemporary art exhibition with wellness programming, creating an immersive experience that nourishes both the mind and soul.

**Our Gallery Offerings:**
• 2,500 sq ft of flexible exhibition space
• Professional lighting and display systems
• Integrated wellness programming options
• Marketing and promotional support
• Opening reception coordination
• Artist talk and workshop facilitation

**Collaboration Opportunities:**
• Solo and group exhibitions
• Pop-up installations
• Wellness-art integration programs
• Community engagement events
• Corporate art partnerships

I'd love to schedule a time to discuss your vision and explore how The 7 Space can bring it to life. Are you available for a brief call this week?

You can also visit our gallery Tuesday-Sunday, 10am-6pm, to experience the space firsthand.

Looking forward to creating something beautiful together.

Best regards,
{curator_name}
Gallery Curator, The 7 Space
                """,
                personalization_level=PersonalizationLevel.ADVANCED,
                variables=["first_name", "curator_name", "inquiry_type", "contact_source"],
                follow_up_days=3,
                success_metrics=["response_rate", "meeting_scheduled", "gallery_visit", "collaboration_initiated"]
            ),

            # AM Consulting Templates
            "am_consulting_business_welcome": EngagementTemplate(
                template_id="am_consulting_business_welcome",
                name="AM Consulting Business Welcome",
                template_type=TemplateType.WELCOME,
                business_entity="AM Consulting",
                contact_types=["Business Contact", "Potential Client"],
                subject_line="Strategic Growth Awaits - Welcome to AM Consulting",
                content="""
Dear {first_name},

Welcome to AM Consulting, where strategic vision meets actionable results.

I'm {consultant_name}, and I'm excited to connect with you about your business growth objectives. At AM Consulting, we specialize in transforming ambitious visions into measurable outcomes through strategic planning, operational excellence, and innovative solutions.

**Our Expertise:**
• Strategic Business Planning & Execution
• Operational Optimization & Process Improvement
• Market Expansion & Growth Strategies
• Digital Transformation & Technology Integration
• Leadership Development & Team Building
• Financial Planning & Performance Management

**Why Businesses Choose AM Consulting:**
✓ 15+ years of proven results across diverse industries
✓ Customized strategies tailored to your unique challenges
✓ Hands-on implementation support, not just recommendations
✓ Measurable ROI and performance improvements
✓ Long-term partnership approach to sustainable growth

**Your Complimentary Strategy Session:**
I'd like to offer you a complimentary 30-minute strategy session where we can:
• Assess your current business challenges and opportunities
• Identify key growth levers specific to your industry
• Outline a preliminary roadmap for achieving your objectives
• Determine how AM Consulting can best support your success

This session is completely free with no obligations – consider it our investment in your potential success.

Are you available for a brief call this week? You can schedule directly using this link: [Scheduling Link]

Looking forward to discussing your business vision and how we can help you achieve it.

Best regards,
{consultant_name}
Principal Consultant, AM Consulting
                """,
                personalization_level=PersonalizationLevel.ADVANCED,
                variables=["first_name", "consultant_name", "company_name", "industry", "lead_source"],
                follow_up_days=2,
                success_metrics=["email_open", "scheduling_link_click", "consultation_booked", "response_rate"]
            ),

            "am_consulting_consultation_follow_up": EngagementTemplate(
                template_id="am_consulting_consultation_follow_up",
                name="AM Consulting Post-Consultation Follow-up",
                template_type=TemplateType.FOLLOW_UP,
                business_entity="AM Consulting",
                contact_types=["Potential Client", "Business Contact"],
                subject_line="Your Strategic Roadmap - Next Steps for {company_name}",
                content="""
Dear {first_name},

Thank you for the engaging conversation during our strategy session yesterday. I was impressed by {company_name}'s vision and the opportunities we discussed for accelerating your growth.

**Key Takeaways from Our Discussion:**
• {key_challenge_1}
• {key_opportunity_1}
• {strategic_priority_1}
• {growth_potential_area}

**Recommended Next Steps:**
Based on our conversation, I've outlined a preliminary strategic approach that could help {company_name} achieve {specific_goal} within {timeframe}.

**Phase 1: Foundation (Months 1-2)**
- {recommendation_1}
- {recommendation_2}

**Phase 2: Implementation (Months 3-4)**
- {recommendation_3}
- {recommendation_4}

**Phase 3: Optimization (Months 5-6)**
- {recommendation_5}
- {recommendation_6}

**Your Customized Proposal:**
I'm preparing a detailed proposal that outlines:
• Comprehensive situation analysis
• Strategic recommendations with implementation timelines
• Expected outcomes and ROI projections
• Investment options and engagement models

I'll have this ready for you by {proposal_date}. In the meantime, I've attached a case study of how we helped a similar company in {industry} achieve {case_study_result}.

**Questions or Immediate Needs:**
If you have any immediate questions or would like to discuss any aspect of our conversation in more detail, please don't hesitate to reach out.

I'm excited about the possibility of partnering with {company_name} on this strategic journey.

Best regards,
{consultant_name}
Principal Consultant, AM Consulting
                """,
                personalization_level=PersonalizationLevel.PREMIUM,
                variables=["first_name", "company_name", "consultant_name", "key_challenge_1", "specific_goal", "timeframe"],
                follow_up_days=1,
                success_metrics=["email_open", "attachment_download", "response_rate", "proposal_request"]
            ),

            # HigherSelf Core Templates
            "higherself_community_welcome": EngagementTemplate(
                template_id="higherself_community_welcome",
                name="HigherSelf Community Welcome",
                template_type=TemplateType.WELCOME,
                business_entity="HigherSelf Core",
                contact_types=["General Contact", "Academic Contact", "Media Contact"],
                subject_line="Welcome to The HigherSelf Network - Your Growth Journey Begins",
                content="""
Welcome to The HigherSelf Network, {first_name}!

You've just joined a community of growth-minded individuals committed to personal and professional transformation. We're thrilled to have you on this journey with us.

**What is The HigherSelf Network?**
We're more than just a platform – we're a movement dedicated to helping individuals unlock their highest potential through:

• **Personal Development Resources:** Curated content, tools, and frameworks for continuous growth
• **Professional Advancement:** Career development strategies, networking opportunities, and skill-building programs
• **Community Connection:** Engage with like-minded individuals who share your commitment to excellence
• **Expert Guidance:** Access to thought leaders, coaches, and mentors across various disciplines
• **Holistic Wellness:** Integration of mental, physical, and spiritual well-being practices

**Your Next Steps:**
1. **Complete Your Profile:** Help us personalize your experience [Profile Link]
2. **Explore Our Resources:** Browse our library of growth-focused content [Resources Link]
3. **Join Community Discussions:** Connect with fellow members [Community Link]
4. **Attend Our Welcome Session:** Join our next virtual orientation [Event Link]

**This Week's Highlights:**
• New Article: "The Science of Sustainable Growth" [Read Now]
• Community Challenge: 7-Day Mindfulness Practice [Join Challenge]
• Upcoming Webinar: "Building Your Personal Brand" [Register]

**Stay Connected:**
Follow us on social media for daily inspiration and community updates:
• LinkedIn: @HigherSelfNetwork
• Instagram: @thehigherselfnetwork
• Twitter: @HigherSelfNet

Remember, every expert was once a beginner. Your journey to your HigherSelf starts with a single step, and you've already taken it by joining our community.

Welcome aboard!

The HigherSelf Network Team

P.S. Reply to this email and tell us what you're most excited to achieve this year. We love hearing from our community members!
                """,
                personalization_level=PersonalizationLevel.STANDARD,
                variables=["first_name", "interests", "goals", "join_source"],
                follow_up_days=7,
                success_metrics=["profile_completion", "resource_engagement", "community_participation", "event_attendance"]
            ),

            # Lead Source-Specific Templates
            "event_follow_up_warm": EngagementTemplate(
                template_id="event_follow_up_warm",
                name="Event Follow-up (Warm Lead)",
                template_type=TemplateType.FOLLOW_UP,
                business_entity="All",
                contact_types=["All"],
                subject_line="Great meeting you at {event_name}!",
                content="""
Hi {first_name},

It was wonderful meeting you at {event_name} {event_date}! I really enjoyed our conversation about {conversation_topic}.

As promised, I'm following up with the information we discussed:

{promised_information}

**What's Next?**
{next_steps_based_on_conversation}

I'd love to continue our conversation and explore how we can support your {specific_interest}. Are you available for a brief call next week?

You can schedule a time that works for you here: [Scheduling Link]

Looking forward to staying connected!

Best regards,
{team_member_name}
{business_entity}

P.S. I've also included some additional resources that might interest you based on our discussion: {additional_resources}
                """,
                personalization_level=PersonalizationLevel.PREMIUM,
                variables=["first_name", "event_name", "event_date", "conversation_topic", "team_member_name"],
                follow_up_days=1,
                success_metrics=["response_rate", "meeting_scheduled", "resource_engagement", "conversion"]
            ),

            "referral_vip_welcome": EngagementTemplate(
                template_id="referral_vip_welcome",
                name="VIP Referral Welcome",
                template_type=TemplateType.WELCOME,
                business_entity="All",
                contact_types=["All"],
                subject_line="Welcome! {referrer_name} thought you'd love what we're doing",
                content="""
Dear {first_name},

{referrer_name} thought you'd be interested in what we're doing at {business_entity}, and we're honored by their recommendation.

{referrer_name} mentioned that you're {referrer_context}, which aligns perfectly with our mission and community.

**A Special Welcome for You:**
As a valued referral from {referrer_name}, we'd like to offer you:
• {vip_benefit_1}
• {vip_benefit_2}
• {vip_benefit_3}

**Why {referrer_name} Recommended Us:**
{referrer_testimonial_or_reason}

**Let's Connect:**
I'd personally love to learn more about your {relevant_interest} and share how we might be able to support your goals.

Would you be available for a brief conversation this week? I promise to keep it focused and valuable for you.

You can schedule a time directly here: [VIP Scheduling Link]

Thank you for trusting {referrer_name}'s recommendation, and we look forward to potentially welcoming you to our community.

Warm regards,
{executive_name}
{executive_title}, {business_entity}

P.S. Please give our best to {referrer_name} – we're grateful for friends like them who help us connect with amazing people like you.
                """,
                personalization_level=PersonalizationLevel.PREMIUM,
                variables=["first_name", "referrer_name", "business_entity", "executive_name", "referrer_context"],
                follow_up_days=1,
                success_metrics=["response_rate", "vip_meeting_scheduled", "referrer_thank_you", "conversion"]
            )
        }

    def _initialize_personalization_rules(self) -> Dict[str, Any]:
        """Initialize rules for template personalization."""
        return {
            "contact_type_messaging": {
                "Artist": {
                    "tone": "creative and inspiring",
                    "focus": "artistic growth and community",
                    "call_to_action": "portfolio sharing and exhibition opportunities"
                },
                "Business Contact": {
                    "tone": "professional and results-oriented",
                    "focus": "business growth and strategic outcomes",
                    "call_to_action": "consultation booking and ROI discussion"
                },
                "General Contact": {
                    "tone": "welcoming and supportive",
                    "focus": "personal development and community connection",
                    "call_to_action": "platform exploration and community engagement"
                }
            },
            "lead_source_timing": {
                "Event": {"immediate_follow_up": 24, "sequence_spacing": [1, 3, 7]},
                "Referral": {"immediate_follow_up": 4, "sequence_spacing": [1, 2, 5]},
                "Website": {"immediate_follow_up": 12, "sequence_spacing": [1, 7, 14]}
            },
            "business_entity_branding": {
                "The 7 Space": {
                    "color_scheme": "warm and artistic",
                    "imagery": "gallery and wellness focused",
                    "signature": "creative energy"
                },
                "AM Consulting": {
                    "color_scheme": "professional and trustworthy",
                    "imagery": "business growth focused",
                    "signature": "strategic excellence"
                },
                "HigherSelf Core": {
                    "color_scheme": "inspiring and growth-oriented",
                    "imagery": "community and development focused",
                    "signature": "transformational journey"
                }
            }
        }

    def get_template(self, template_id: str) -> Optional[EngagementTemplate]:
        """Get a specific template by ID."""
        return self.templates.get(template_id)

    def get_templates_by_entity(self, business_entity: str) -> List[EngagementTemplate]:
        """Get all templates for a specific business entity."""
        return [
            template for template in self.templates.values()
            if template.business_entity == business_entity or template.business_entity == "All"
        ]

    def get_templates_by_type(self, template_type: TemplateType) -> List[EngagementTemplate]:
        """Get all templates of a specific type."""
        return [
            template for template in self.templates.values()
            if template.template_type == template_type
        ]

    def personalize_template(self, template_id: str, contact_data: Dict[str, Any]) -> Dict[str, str]:
        """Personalize a template with contact data."""
        template = self.get_template(template_id)
        if not template:
            return {}

        personalized_content = template.content
        personalized_subject = template.subject_line

        # Replace variables with actual data
        for variable in template.variables:
            value = contact_data.get(variable, f"{{{variable}}}")
            personalized_content = personalized_content.replace(f"{{{variable}}}", str(value))
            personalized_subject = personalized_subject.replace(f"{{{variable}}}", str(value))

        return {
            "subject": personalized_subject,
            "content": personalized_content,
            "template_id": template_id,
            "personalization_level": template.personalization_level.value
        }
