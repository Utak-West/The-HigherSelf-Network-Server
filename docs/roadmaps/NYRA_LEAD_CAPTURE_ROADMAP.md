# Nyra Lead Capture Roadmap

## Introduction

Nyra serves as the Lead Capture Specialist within The HigherSelf Network server ecosystem. As the initial point of contact for most new business opportunities, Nyra plays a critical role in processing incoming leads, qualifying their potential, and initiating appropriate follow-up actions. This document outlines Nyra's roles, responsibilities, and workflows, providing a comprehensive blueprint for implementation and operation of this vital component in the agent ecosystem.

Nyra's primary purpose is to ensure that every lead entering the system receives prompt, appropriate processing and evaluation, with seamless handoffs to other specialized agents for follow-up actions. By centralizing lead capture and qualification logic, Nyra ensures consistent lead handling, proper data enrichment, and intelligent routing based on lead characteristics and business rules.

## Core Responsibilities and Capabilities

Nyra functions as the lead management center of The HigherSelf Network, with the following core responsibilities:

- **Lead Reception**: Capturing lead information from various sources including web forms, social media platforms, email inquiries, and partner referrals
- **Data Validation**: Ensuring incoming lead data meets quality standards and contains all required information
- **Lead Enrichment**: Augmenting basic lead information with additional data from external sources and internal databases
- **Lead Qualification**: Evaluating leads against predefined criteria to determine their quality, potential value, and appropriate next steps
- **Prospect Segmentation**: Categorizing leads based on characteristics such as industry, company size, needs, and engagement readiness
- **Follow-up Task Generation**: Creating appropriate follow-up tasks and assigning them to the right agents or human team members
- **Lead Nurturing Initiation**: Triggering automated nurture sequences for leads that require further development
- **Duplicate Detection**: Identifying and properly handling duplicate lead submissions
- **Lead Prioritization**: Assigning priority levels to incoming leads based on business rules and lead characteristics
- **Analytics Tracking**: Recording lead sources, qualification results, and conversion metrics for performance analysis

Nyra's capabilities extend beyond basic lead collection to include sophisticated evaluation and routing logic that considers both explicit lead attributes and implicit signals to determine the optimal processing path for each lead.

## Lead Processing Workflow

Nyra's lead processing workflow follows these key steps:

1. **Lead Reception**: Leads enter the system through one of several channels:
   - Website contact and lead capture forms
   - Social media inquiries and direct messages
   - Email submissions and responses
   - Partner referrals and integrations
   - Manual entries from team members

2. **Initial Validation**: Upon receipt, Nyra performs preliminary validation:
   - Verifying the presence of all required fields
   - Checking email and phone format validity
   - Detecting potential spam or bot submissions
   - Standardizing data formats for consistent processing

3. **Lead Enrichment**: Nyra augments the basic lead information:
   - Company details from business databases
   - Social media profile information
   - Previous interactions with the business
   - Website visitor behavior data when available
   - Technographic and firmographic data

4. **Duplicate Detection**: Nyra checks for existing records:
   - Email and phone matching against existing contacts
   - Company name similarity detection
   - Fuzzy matching algorithms for potential duplicates
   - Determination of merge, update, or new record creation

5. **Lead Qualification**: Nyra evaluates the lead against qualification criteria:
   - Fit with ideal customer profile
   - Budget signals and potential project scope
   - Timeline indicators for decision-making
   - Authority level of the contact person
   - Needs alignment with available services
   - Engagement signals and response behavior

6. **Lead Categorization**: Based on qualification, Nyra categorizes the lead:
   - Sales-ready leads for immediate follow-up
   - Marketing-qualified leads requiring nurturing
   - Information-seeking leads needing educational content
   - Partner or collaboration opportunities
   - Unqualified leads that don't fit current offerings

7. **Follow-up Action Determination**: Nyra decides appropriate next steps:
   - Direct assignment to sales team for high-value, ready leads
   - Enrollment in nurture sequences for qualified but not ready leads
   - Educational content delivery for information-seeking leads
   - Specific workflows for special case leads
   - Courtesy response for unqualified leads

8. **Task Creation**: Nyra generates appropriate follow-up tasks:
   - Creating task records with all relevant context
   - Setting deadlines based on lead priority
   - Assigning to appropriate team members or agents
   - Including qualification notes and suggested actions

9. **Nurture Sequence Initiation**: For leads requiring nurturing:
   - Selecting appropriate nurture campaign type
   - Personalizing sequence based on lead characteristics
   - Setting up tracking for engagement monitoring
   - Scheduling initial nurture communications

10. **System Record Creation**: Nyra ensures proper record creation:

## Decision Points for Lead Qualification and Routing

Nyra employs a sophisticated decision-making framework to qualify leads and determine optimal routing. Key decision points in this process include:

### Lead Qualification Framework

Nyra evaluates leads using a multi-factor qualification system:

```mermaid
flowchart TD
    %% Styling
    classDef entryPoint fill:#e1f5fe,stroke:#01579b,color:#01579b,stroke-width:2px
    classDef eventProcess fill:#e8f5e9,stroke:#2e7d32,color:#2e7d32,stroke-width:2px
    classDef agentNode fill:#f3e5f5,stroke:#6a1b9a,color:#6a1b9a,stroke-width:2px
    classDef decisionNode fill:#fff3e0,stroke:#e65100,color:#e65100,stroke-width:2px
    classDef dataNode fill:#e0f2f1,stroke:#00695c,color:#00695c,stroke-width:2px

    %% Lead Qualification Flow
    IncomingLead[Incoming Lead] :::entryPoint
    IncomingLead --> BasicValidation[Basic Data Validation] :::eventProcess
    BasicValidation --> ValidationCheck{Valid Lead Data?} :::decisionNode

    ValidationCheck -->|No| InvalidLead[Handle Invalid Lead] :::eventProcess
    ValidationCheck -->|Yes| EnrichmentProcess[Enrich Lead Data] :::eventProcess

    EnrichmentProcess --> DuplicateCheck{Duplicate Check} :::decisionNode
    DuplicateCheck -->|Is Duplicate| DuplicateProcess[Handle Duplicate Lead] :::eventProcess
    DuplicateCheck -->|Is New| FitAnalysis[Analyze ICP Fit] :::eventProcess

    FitAnalysis --> FitScore{ICP Fit Score} :::decisionNode
    FitScore -->|Poor Fit| UnqualifiedProcess[Process as Unqualified] :::eventProcess
    FitScore -->|Good Fit| BudgetAnalysis[Analyze Budget Signals] :::eventProcess

    BudgetAnalysis --> BudgetScore{Budget Score} :::decisionNode
    BudgetScore -->|Below Threshold| NurtureCandidate[Mark as Nurture Candidate] :::eventProcess
    BudgetScore -->|Above Threshold| TimelineAnalysis[Analyze Timeline Signals] :::eventProcess

    TimelineAnalysis --> UrgencyScore{Urgency Score} :::decisionNode
    UrgencyScore -->|Low Urgency| NurtureCandidate
    UrgencyScore -->|High Urgency| AuthorityAnalysis[Analyze Authority Level] :::eventProcess

    AuthorityAnalysis --> AuthorityScore{Authority Score} :::decisionNode
    AuthorityScore -->|Low Authority| InfluencerProcess[Process as Influencer] :::eventProcess
    AuthorityScore -->|High Authority| NeedsAnalysis[Analyze Needs Alignment] :::eventProcess

    NeedsAnalysis --> NeedsScore{Needs Alignment} :::decisionNode
    NeedsScore -->|Low Alignment| SpecialCaseProcess[Process as Special Case] :::eventProcess
    NeedsScore -->|High Alignment| EngagementAnalysis[Analyze Engagement Signals] :::eventProcess

    EngagementAnalysis --> EngagementScore{Engagement Score} :::decisionNode
    EngagementScore -->|Low Engagement| MQLProcess[Process as MQL] :::eventProcess
    EngagementScore -->|High Engagement| SQLProcess[Process as SQL] :::eventProcess

    InvalidLead --> SendCourtesyResponse[Send Courtesy Response] :::eventProcess
    DuplicateProcess --> UpdateExistingRecord[Update Existing Record] :::eventProcess
    UnqualifiedProcess --> RecordUnqualifiedLead[Record Unqualified Lead] :::eventProcess
    NurtureCandidate --> NurtureQualification[Qualify for Nurture Type] :::eventProcess
    InfluencerProcess --> InfluencerNurture[Setup Influencer Nurture] :::eventProcess
    SpecialCaseProcess --> SpecialCaseRouting[Route to Specialist] :::eventProcess
    MQLProcess --> MarketingHandoff[Handoff to Marketing] :::eventProcess
    SQLProcess --> SalesHandoff[Handoff to Sales] :::eventProcess
```

### Lead Routing Logic

Once a lead is qualified, Nyra determines the appropriate routing path:

```mermaid
flowchart TD
    %% Styling
    classDef entryPoint fill:#e1f5fe,stroke:#01579b,color:#01579b,stroke-width:2px
    classDef eventProcess fill:#e8f5e9,stroke:#2e7d32,color:#2e7d32,stroke-width:2px
    classDef agentNode fill:#f3e5f5,stroke:#6a1b9a,color:#6a1b9a,stroke-width:2px
    classDef decisionNode fill:#fff3e0,stroke:#e65100,color:#e65100,stroke-width:2px
    classDef dataNode fill:#e0f2f1,stroke:#00695c,color:#00695c,stroke-width:2px

    %% Lead Routing Flow
    QualifiedLead[Qualified Lead] :::entryPoint
    QualifiedLead --> LeadType{Lead Category} :::decisionNode

    LeadType -->|SQL| SalesReadyProcess[Process Sales Ready Lead] :::eventProcess
    LeadType -->|MQL| MarketingQualifiedProcess[Process Marketing Qualified Lead] :::eventProcess
    LeadType -->|Information Request| InfoRequestProcess[Process Information Request] :::eventProcess
    LeadType -->|Partner Opportunity| PartnerProcess[Process Partner Lead] :::eventProcess
    LeadType -->|Special Case| SpecialCaseProcess[Process Special Case] :::eventProcess

    SalesReadyProcess --> UrgencyCheck{Urgency Level} :::decisionNode
    UrgencyCheck -->|High| ImmediateContact[Create Immediate Contact Task] :::eventProcess
    UrgencyCheck -->|Medium| StandardFollow[Create Standard Follow-up Task] :::eventProcess
    UrgencyCheck -->|Low| DelayedFollow[Create Delayed Follow-up Task] :::eventProcess

    MarketingQualifiedProcess --> InterestAnalysis{Primary Interest} :::decisionNode
    InterestAnalysis -->|Product A| ProductASequence[Initiate Product A Nurture] :::eventProcess
    InterestAnalysis -->|Service B| ServiceBSequence[Initiate Service B Nurture] :::eventProcess
    InterestAnalysis -->|General| GeneralSequence[Initiate General Nurture] :::eventProcess

    InfoRequestProcess --> ContentTypeMatch{Content Type} :::decisionNode
    ContentTypeMatch -->|Case Studies| CaseStudyDelivery[Deliver Case Studies] :::eventProcess
    ContentTypeMatch -->|Pricing| PricingDelivery[Deliver Pricing Info] :::eventProcess
    ContentTypeMatch -->|Technical| TechnicalDelivery[Deliver Technical Info] :::eventProcess

    PartnerProcess --> PartnerTypeAnalysis{Partner Type} :::decisionNode
    PartnerTypeAnalysis -->|Referral| ReferralProcess[Process Referral Partner] :::eventProcess
    PartnerTypeAnalysis -->|Integration| IntegrationProcess[Process Integration Partner] :::eventProcess
    PartnerTypeAnalysis -->|Channel| ChannelProcess[Process Channel Partner] :::eventProcess

    ImmediateContact --> CreateSalesTask[Create Ruvo Sales Task] :::eventProcess
    StandardFollow --> CreateSalesTask
    DelayedFollow --> CreateSalesTask

    ProductASequence --> InitiateNurture[Initiate Liora Nurture Sequence] :::eventProcess
    ServiceBSequence --> InitiateNurture
    GeneralSequence --> InitiateNurture

    CaseStudyDelivery --> CreateContentTask[Create Elan Content Task] :::eventProcess
    PricingDelivery --> CreateSalesTask
    TechnicalDelivery --> CreateContentTask
## Integration with Ruvo (Task Orchestrator)

Nyra integrates closely with Ruvo, the Task Orchestrator, to ensure proper follow-up on qualified leads. This integration includes:

### Task Creation for Lead Follow-up

- **Structured Task Generation**: Nyra creates detailed, structured task requests based on lead qualification results
- **Context Preservation**: All relevant lead information and qualification notes are included in task creation
- **Priority Assignment**: Tasks are assigned appropriate priority levels based on lead characteristics
- **Deadline Setting**: Suitable deadlines are established based on lead urgency and business SLAs
- **Assignee Determination**: Nyra identifies the most appropriate assignee based on lead properties
- **Task Template Application**: Industry-specific task templates are applied to ensure consistency
- **Task Sequence Management**: Related tasks are linked into sequences when appropriate
- **Follow-up Verification**: Nyra monitors task completion status through Ruvo's update system

### Task Creation Workflow

```mermaid
flowchart TD
    %% Styling
    classDef entryPoint fill:#e1f5fe,stroke:#01579b,color:#01579b,stroke-width:2px
    classDef eventProcess fill:#e8f5e9,stroke:#2e7d32,color:#2e7d32,stroke-width:2px
    classDef agentNode fill:#f3e5f5,stroke:#6a1b9a,color:#6a1b9a,stroke-width:2px
    classDef decisionNode fill:#fff3e0,stroke:#e65100,color:#e65100,stroke-width:2px
    classDef dataNode fill:#e0f2f1,stroke:#00695c,color:#00695c,stroke-width:2px

    %% Task Creation Flow
    QualifiedLead[Qualified Lead] :::entryPoint
    QualifiedLead --> DetermineActions[Determine Required Actions] :::eventProcess
    DetermineActions --> SingleActionCheck{Multiple Actions?} :::decisionNode

    SingleActionCheck -->|No| TaskTypeSelection[Select Task Type] :::eventProcess
    SingleActionCheck -->|Yes| TaskSequenceCreation[Create Task Sequence] :::eventProcess

    TaskTypeSelection --> FindTemplate[Find Matching Task Template] :::eventProcess
    TaskSequenceCreation --> SequenceTemplate[Find Sequence Template] :::eventProcess

    FindTemplate --> TemplateAvailable{Template Found?} :::decisionNode
    TemplateAvailable -->|Yes| ApplyTemplate[Apply Task Template] :::eventProcess
    TemplateAvailable -->|No| CreateCustomTask[Create Custom Task] :::eventProcess

    SequenceTemplate --> ApplyTaskSequence[Apply Task Sequence Template] :::eventProcess

    ApplyTemplate --> AssigneeSelection[Select Appropriate Assignee] :::eventProcess
    CreateCustomTask --> AssigneeSelection
    ApplyTaskSequence --> MultipleAssignees[Determine Task Assignees] :::eventProcess

    AssigneeSelection --> SetPriority[Set Task Priority] :::eventProcess
    MultipleAssignees --> BatchPriorities[Set Task Priorities] :::eventProcess

    SetPriority --> SetDeadline[Set Task Deadline] :::eventProcess
    BatchPriorities --> BatchDeadlines[Set Task Deadlines] :::eventProcess

    SetDeadline --> EnrichTaskContext[Enrich with Lead Context] :::eventProcess
    BatchDeadlines --> EnrichBatchContext[Enrich Tasks with Context] :::eventProcess

    EnrichTaskContext --> SendToRuvo[Send Task Request to Ruvo] :::eventProcess
    EnrichBatchContext --> SendBatchToRuvo[Send Task Batch to Ruvo] :::eventProcess

    SendToRuvo --> Ruvo{Ruvo Task Orchestrator} :::agentNode
    SendBatchToRuvo --> Ruvo
```

### Task Completion Monitoring

- **Status Updates**: Nyra receives task status updates from Ruvo as follow-up tasks progress
- **Follow-up Escalation**: When tasks exceed their expected completion timeframes, Nyra can trigger escalation
- **Conversion Tracking**: Lead status changes resulting from task completion are recorded for analytics
- **Sequence Advancement**: For multi-step lead processes, Nyra works with Ruvo to manage task sequence progression

This integration ensures that qualified leads are consistently followed up with appropriate actions, proper tracking, and clear accountability.

## Integration with Liora (Marketing Agent)

Nyra works closely with Liora, the Marketing Strategist, to ensure leads requiring nurturing receive appropriate marketing attention. This integration includes:

### Lead Nurture Sequence Initiation

- **Nurture Campaign Selection**: Nyra determines the most appropriate nurture campaign type based on lead characteristics
- **Personalization Data**: Lead information is structured and enhanced to enable personalized nurture content
- **Segment Assignment**: Leads are assigned to appropriate marketing segments based on qualification data
- **Engagement Tracking Setup**: Proper tracking parameters are established for nurture sequence engagement monitoring
- **Content Customization Signals**: Lead preference and interest data are passed to enable content customization
- **Sequence Timing Parameters**: Urgency and timeline data inform the pacing of nurture communications
- **Multi-channel Coordination**: Contact preference data guides channel selection for nurture touches
- **Feedback Loop Establishment**: Engagement monitoring mechanisms are established for continuous optimization

### Nurture Initiation Workflow

```mermaid
flowchart TD
    %% Styling
    classDef entryPoint fill:#e1f5fe,stroke:#01579b,color:#01579b,stroke-width:2px
    classDef eventProcess fill:#e8f5e9,stroke:#2e7d32,color:#2e7d32,stroke-width:2px
    classDef agentNode fill:#f3e5f5,stroke:#6a1b9a,color:#6a1b9a,stroke-width:2px
    classDef decisionNode fill:#fff3e0,stroke:#e65100,color:#e65100,stroke-width:2px
    classDef dataNode fill:#e0f2f1,stroke:#00695c,color:#00695c,stroke-width:2px

    %% Nurture Initiation Flow
    NurtureCandidate[Nurture Candidate Lead] :::entryPoint
    NurtureCandidate --> AnalyzeInterests[Analyze Lead Interests] :::eventProcess
    AnalyzeInterests --> InterestType{Primary Interest Area} :::decisionNode

    InterestType -->|Product Focused| ProductNurture[Select Product Nurture] :::eventProcess
    InterestType -->|Service Focused| ServiceNurture[Select Service Nurture] :::eventProcess
    InterestType -->|Content Focused| ContentNurture[Select Content Nurture] :::eventProcess
    InterestType -->|Educational| EducationalNurture[Select Educational Nurture] :::eventProcess

    ProductNurture --> AnalyzeTimeline[Analyze Lead Timeline] :::eventProcess
    ServiceNurture --> AnalyzeTimeline
    ContentNurture --> AnalyzeTimeline
    EducationalNurture --> AnalyzeTimeline

    AnalyzeTimeline --> TimelineType{Buying Timeline} :::decisionNode
    TimelineType -->|Short Term| UrgentPacing[Set Urgent Pacing] :::eventProcess
    TimelineType -->|Medium Term| StandardPacing[Set Standard Pacing] :::eventProcess
    TimelineType -->|Long Term| GradualPacing[Set Gradual Pacing] :::eventProcess
    TimelineType -->|Unknown| DefaultPacing[Set Default Pacing] :::eventProcess

    UrgentPacing --> ChannelPreference[Determine Channel Preferences] :::eventProcess
    StandardPacing --> ChannelPreference
    GradualPacing --> ChannelPreference
    DefaultPacing --> ChannelPreference

    ChannelPreference --> ChannelMix{Preferred Channels} :::decisionNode
    ChannelMix -->|Email Primary| EmailFocused[Configure Email-focused Nurture] :::eventProcess
    ChannelMix -->|Social Primary| SocialFocused[Configure Social-focused Nurture] :::eventProcess
    ChannelMix -->|Multi-channel| MultiChannel[Configure Multi-channel Nurture] :::eventProcess

    EmailFocused --> CompilePersonalization[Compile Personalization Data] :::eventProcess
    SocialFocused --> CompilePersonalization
    MultiChannel --> CompilePersonalization

    CompilePersonalization --> CreateNurtureRequest[Create Nurture Sequence Request] :::eventProcess
    CreateNurtureRequest --> SendToLiora[Send Request to Liora] :::eventProcess

    SendToLiora --> Liora{Liora Marketing Strategist} :::agentNode
```

### Engagement Monitoring

- **Engagement Signal Reception**: Nyra receives updates from Liora on lead engagement with nurture content
- **Lead Status Updates**: Based on engagement patterns, lead qualification status may be upgraded
- **Handoff Triggering**: When engagement reaches threshold levels, Nyra can trigger sales handoff
- **Nurture Optimization**: Engagement data informs refinement of nurture sequence selection logic
- **Re-qualification**: Significant engagement changes can trigger lead re-qualification

This integration ensures that leads requiring development receive appropriate nurturing attention, with clear tracking of progress and mechanisms to accelerate promising leads through the funnel.

```
## Integration with External Systems

Nyra integrates with various external systems to ensure comprehensive lead processing capabilities. Key integration points include:

### CRM Systems

- **Lead Record Creation**: Automatic creation of lead records in CRM platforms
- **Contact Deduplication**: Matching against existing CRM records to prevent duplicates
- **Field Mapping**: Standardized mapping of lead data to CRM field structures
- **Activity Logging**: Recording lead capture and qualification activities in CRM timelines
- **Status Synchronization**: Maintaining consistent lead status between systems

### Form and Landing Page Platforms

- **Form Submission Processing**: Direct integration with form platforms like Typeform and JotForm
- **Landing Page Tracking**: Capturing referring landing pages and campaign data
- **Progressive Profiling Support**: Managing incremental data collection across multiple interactions
- **Contextual Data Capture**: Preserving UTM parameters and referral information
- **Conversion Tracking**: Recording form-to-lead conversion metrics

### Email Systems

- **Inbound Email Processing**: Extracting lead information from email inquiries
- **Confirmation Emails**: Triggering acknowledgment emails for form submissions
- **Deliverability Verification**: Validating email addresses for deliverability
- **Unsubscribe Handling**: Respecting marketing preferences and consent

### Social Media Platforms

- **Social Lead Capture**: Processing leads generated through social media platforms
- **Profile Enrichment**: Enhancing lead data with social profile information
- **Social Engagement History**: Incorporating previous social interactions into lead context
- **Direct Message Handling**: Processing inquiries received through social direct messages

### Data Enrichment Services

- **Company Data Enrichment**: Connecting with services like Clearbit and ZoomInfo for company information
- **Contact Verification**: Validating contact information accuracy
- **Technographic Enrichment**: Adding technology stack information when relevant
- **Industry Classification**: Standardizing industry categorization

### Analytics and Tracking

- **Attribution Tracking**: Maintaining source and campaign attribution data
- **Conversion Analysis**: Tracking lead-to-customer conversion rates by source
- **Performance Metrics**: Generating lead processing performance metrics
- **A/B Test Processing**: Handling leads from different variant groups appropriately

These integrations position Nyra as a central hub for lead processing that connects seamlessly with both internal agents and external systems to create a comprehensive lead management ecosystem.

These decision frameworks enable Nyra to make intelligent qualification and routing decisions based on lead characteristics, business rules, and current system state.
## Nyra's Workflow Visualization

The following diagram provides a visual representation of Nyra's complete lead processing workflow:

```mermaid
flowchart TB
    %% Styling
    classDef entryPoint fill:#e1f5fe,stroke:#01579b,color:#01579b,stroke-width:2px
    classDef eventProcess fill:#e8f5e9,stroke:#2e7d32,color:#2e7d32,stroke-width:2px
    classDef agentNode fill:#f3e5f5,stroke:#6a1b9a,color:#6a1b9a,stroke-width:2px
    classDef decisionNode fill:#fff3e0,stroke:#e65100,color:#e65100,stroke-width:2px
    classDef storageNode fill:#e0f2f1,stroke:#00695c,color:#00695c,stroke-width:2px
    classDef integrationNode fill:#ede7f6,stroke:#4527a0,color:#4527a0,stroke-width:2px
    classDef errorNode fill:#ffebee,stroke:#b71c1c,color:#b71c1c,stroke-width:2px

    %% Entry Points
    WebForm[Website Forms] :::entryPoint
    SocialMedia[Social Media] :::entryPoint
    Email[Email Inquiries] :::entryPoint
    PartnerReferral[Partner Referrals] :::entryPoint
    ManualEntry[Manual Entry] :::entryPoint

    %% Nyra Processing Steps
    WebForm --> LeadReceived[Lead Received] :::eventProcess
    SocialMedia --> LeadReceived
    Email --> LeadReceived
    PartnerReferral --> LeadReceived
    ManualEntry --> LeadReceived

    LeadReceived --> BasicValidation[Basic Validation] :::eventProcess
    BasicValidation --> ValidationCheck{Valid Lead?} :::decisionNode

    ValidationCheck -->|No| InvalidHandling[Handle Invalid Lead] :::errorNode
    ValidationCheck -->|Yes| DuplicateCheck[Check for Duplicates] :::eventProcess

    DuplicateCheck --> DuplicateResult{Duplicate?} :::decisionNode
    DuplicateResult -->|Yes| MergeOrUpdate[Merge or Update Record] :::eventProcess
    DuplicateResult -->|No| EnrichLead[Enrich Lead Data] :::eventProcess

    EnrichLead --> ExternalEnrichment[External Data Services] :::integrationNode
    ExternalEnrichment --> EnrichedLead[Enriched Lead] :::eventProcess

    MergeOrUpdate --> LeadQualification[Lead Qualification] :::eventProcess
    EnrichedLead --> LeadQualification

    LeadQualification --> QualificationResult{Qualification Result} :::decisionNode

    QualificationResult -->|Unqualified| UnqualifiedProcess[Process Unqualified Lead] :::eventProcess
    QualificationResult -->|Information Request| InfoRequestProcess[Process Information Request] :::eventProcess
    QualificationResult -->|MQL| MQLProcess[Process Marketing Qualified Lead] :::eventProcess
    QualificationResult -->|SQL| SQLProcess[Process Sales Qualified Lead] :::eventProcess
    QualificationResult -->|Partner| PartnerProcess[Process Partner Lead] :::eventProcess

    UnqualifiedProcess --> CourtesyResponse[Send Courtesy Response] :::eventProcess
    InfoRequestProcess --> ContentSelection[Select Appropriate Content] :::eventProcess
    ContentSelection --> ContentDelivery[Content Delivery Task] :::eventProcess

    MQLProcess --> NurtureTypeSelection[Select Nurture Type] :::eventProcess
    NurtureTypeSelection --> CreateNurtureRequest[Create Nurture Request] :::eventProcess
    CreateNurtureRequest --> Liora[Liora - Marketing Strategist] :::agentNode

    SQLProcess --> SalesTaskCreation[Create Sales Task] :::eventProcess
    SalesTaskCreation --> Ruvo[Ruvo - Task Orchestrator] :::agentNode

    PartnerProcess --> PartnerTaskCreation[Create Partner Follow-up Task] :::eventProcess
    PartnerTaskCreation --> Ruvo

    CourtesyResponse --> LeadRecordCreation[Create Lead Records] :::eventProcess
    ContentDelivery --> LeadRecordCreation
    Liora --> LeadRecordCreation
    Ruvo --> LeadRecordCreation

    LeadRecordCreation --> CRM[(CRM System)] :::storageNode
    LeadRecordCreation --> NotionDB[(Notion Database)] :::storageNode
    LeadRecordCreation --> MarketingPlatform[(Marketing Platform)] :::storageNode

    CRM --> Analytics[Update Analytics] :::eventProcess
    NotionDB --> Analytics
    MarketingPlatform --> Analytics

    Analytics --> LeadMetrics[Lead Processing Metrics] :::storageNode
    Analytics --> ConversionTracking[Conversion Tracking] :::storageNode
```

This diagram illustrates the comprehensive flow of leads through Nyra's processing system, from initial reception through validation, enrichment, qualification, and appropriate routing to other specialized agents or external systems.

## JSON Message Examples

The following examples demonstrate the JSON message formats used by Nyra for different lead processing scenarios.

### 1. Lead Data Receipt from Form Submission

When a lead is submitted through a form, Nyra receives it in the following format:

```json
{
  "event_type": "lead_submission",
  "source": {
    "system_id": "WEBSITE_FORM",
    "form_id": "contact-us-primary",
    "source_name": "Main Contact Form"
  },
  "timestamp": "2025-05-17T09:45:22Z",
  "event_id": "evt-8d62c3a4b7f1",
  "lead_data": {
    "personal_info": {
      "first_name": "Jordan",
      "last_name": "Taylor",
      "email": "jordan.taylor@example.com",
      "phone": "+1-555-987-6543",
      "job_title": "Operations Director"
    },
    "company_info": {
      "company_name": "Frontier Innovations",
      "industry": "Healthcare Technology",
      "company_size": "50-200",
      "website": "frontierinnovations.example.com"
    },
    "interest_info": {
      "service_interest": "Community Building Services",
      "project_timeline": "1-3 months",
      "budget_range": "$10,000 - $25,000",
      "message": "We're looking to build an engaged community around our new health monitoring platform. Would like to discuss your community growth strategies and how they might apply to healthcare tech."
    }
  },
  "marketing_data": {
    "utm_source": "google",
    "utm_medium": "cpc",
    "utm_campaign": "community-services-q2-2025",
    "utm_content": "healthcare-specific",
    "landing_page": "/services/community-building",
    "referrer": "google.com"
  },
  "metadata": {
    "submission_ip": "192.168.1.105",
    "device_type": "desktop",
    "browser": "Chrome",
    "session_duration": 245,
    "pages_viewed": 3,
    "submission_timestamp_local": "2025-05-17T05:45:22-04:00"
  }
}
```

This example shows a detailed lead submission from a website contact form, containing structured personal and company information, interest data, marketing attribution, and session metadata.

### 2. Task Creation Request Sent to Ruvo

When Nyra determines a lead needs sales follow-up, it sends a task creation request to Ruvo in this format:

```json
{
  "message_type": "task_creation_request",
  "sender": {
    "agent_id": "LEAD_CAPTURE_AGENT",
    "agent_name": "Nyra"
  },
  "recipient": {
    "agent_id": "TASK_MANAGEMENT_AGENT",
    "agent_name": "Ruvo"
  },
  "timestamp": "2025-05-17T09:48:35Z",
  "message_id": "msg-3f82b9d7e6c5",
  "correlation_id": "lead-8d62c3a4b7f1",
  "payload": {
    "task_type": "sales_follow_up",
    "task_name": "Follow up with Jordan Taylor (Frontier Innovations)",
    "priority": "high",
    "due_date": "2025-05-18T17:00:00Z",
    "description": "New sales-qualified lead from our website contact form. They're interested in Community Building Services for their healthcare technology platform. Budget range is $10,000 - $25,000 with a timeline of 1-3 months.",
    "assignee_type": "sales_team",
    "preferred_assignee": "healthcare_specialist",
    "lead_data": {
      "lead_id": "lead-8d62c3a4b7f1",
      "lead_source": "website_form",
      "contact_name": "Jordan Taylor",
      "contact_email": "jordan.taylor@example.com",
      "contact_phone": "+1-555-987-6543",
      "company": "Frontier Innovations",
      "lead_qualification_score": 85,
      "qualification_notes": "Great fit for our healthcare community services. Has budget and timeline aligned with our offerings."
    },
    "task_template_id": "TPL-SALES-HEALTHCARE-001",
    "checklist_items": [
      "Review company website and social profiles",
      "Research healthcare tech industry trends",
      "Prepare community building case studies for healthcare",
      "Make initial contact within 24 hours",
      "Schedule discovery call",
      "Document call notes and next steps"
    ],
    "attachments": [
      {
        "name": "Lead Submission Details",
        "type": "lead_data",
        "reference_id": "lead-8d62c3a4b7f1"
      },
      {
        "name": "Healthcare Community Case Study",
        "type": "document",
        "reference_id": "doc-healthcare-case-001"
      }
    ]
  },
  "expected_response": {
    "type": "task_creation_confirmation",
    "timeout_seconds": 60
  }
}
```

This message demonstrates how Nyra creates a structured, detailed task request for Ruvo, providing comprehensive information about the lead, suggested actions, and relevant context to enable effective follow-up.

### 3. Lead Nurture Sequence Initiation Sent to Liora

For leads requiring nurturing, Nyra sends a nurture sequence initiation request to Liora:

```json
{
  "message_type": "nurture_sequence_request",
  "sender": {
    "agent_id": "LEAD_CAPTURE_AGENT",
    "agent_name": "Nyra"
  },
  "recipient": {
    "agent_id": "MARKETING_AGENT",
    "agent_name": "Liora"
  },
  "timestamp": "2025-05-17T10:12:18Z",
  "message_id": "msg-5d93c8b6a7e4",
  "correlation_id": "lead-9f73d2b8c1a5",
  "payload": {
    "sequence_type": "mql_nurture",
    "sequence_name": "Healthcare Tech Nurture - Community Focus",
    "lead_data": {
      "lead_id": "lead-9f73d2b8c1a5",
      "contact_name": "Morgan Chen",
      "contact_email": "morgan.chen@example.com",
      "contact_phone": "+1-555-234-5678",
      "job_title": "Product Marketing Manager",
      "company": "MedTech Solutions",
      "industry": "Healthcare Technology",
      "lead_source": "webinar_registration",
      "lead_qualification_score": 68
    },
    "personalization_data": {
      "specific_interests": ["community engagement", "user retention", "healthcare compliance"],
      "buying_stage": "research",
      "content_preferences": ["case studies", "webinars", "how-to guides"],
      "company_size": "10-50",
      "pain_points": ["low user engagement", "regulatory compliance", "scaling community moderation"]
    },
    "nurture_parameters": {
      "urgency_level": "medium",
      "sequence_duration_days": 45,
      "touchpoint_frequency": "weekly",
      "primary_channel": "email",
      "secondary_channels": ["linkedin", "remarketing"],
      "conversion_goal": "schedule_demo",
      "fallback_conversion_goal": "content_download"
    },
    "engagement_monitoring": {
      "email_opens_threshold": 2,
      "click_threshold": 1,
      "website_visit_threshold": 2,
      "form_submission_escalation": true,
      "upgrade_to_sql_signals": ["pricing page visit", "demo request", "multiple content downloads"]
    },
    "related_content_ids": [
      "content-healthcare-community-guide",
      "content-compliance-webinar",
      "content-engagement-metrics-whitepaper",
      "content-case-study-healthcare-community"
    ]
  },
  "expected_response": {
    "type": "nurture_sequence_confirmation",
    "timeout_seconds": 120
  }
}
```

This message showcases how Nyra provides Liora with comprehensive lead nurturing instructions, including detailed personalization data, engagement parameters, monitoring thresholds, and content recommendations for an effective nurture campaign.

## Conclusion

This roadmap outlines Nyra's role as the Lead Capture Specialist within The HigherSelf Network, detailing her responsibilities, workflows, decision frameworks, and integration points. By implementing Nyra according to this blueprint, the system will gain powerful capabilities for consistent lead processing, intelligent qualification, and appropriate routing of business opportunities.

Nyra serves as an essential component in the agent ecosystem, sitting at the critical junction between external lead sources and internal follow-up processes. Her ability to properly evaluate, enrich, and route leads ensures that no opportunity is lost and that each lead receives the most appropriate handling based on its characteristics and potential value.

As The HigherSelf Network evolves, Nyra's capabilities can be extended with additional qualification criteria, more sophisticated routing logic, and integration with new lead sources and destination systems. The modular design outlined in this roadmap facilitates such expansion while maintaining the consistency and reliability of the core lead processing workflow.
    - CRM contact and lead records
    - Notion database entries
    - Marketing automation platform records
    - Analytics tracking setup

This workflow ensures that every lead entering the system receives appropriate evaluation and processing, with optimal routing to the next steps in the customer journey.
