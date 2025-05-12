# The HigherSelf Network Server

<div align="center">

![The HigherSelf Network Banner](https://via.placeholder.com/1200x300?text=The+HigherSelf+Network+Banner)

**Intelligent Automation for Art Gallery, Wellness Center & Consultancy Operations**

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/Utak-West/The-HigherSelf-Network-Server)
[![Notion](https://img.shields.io/badge/Notion-Central%20Hub-black.svg)](https://www.notion.so)
[![Python](https://img.shields.io/badge/Python-3.10+-green.svg)](https://www.python.org)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com)
[![License](https://img.shields.io/badge/license-Proprietary-red.svg)](LICENSE)

</div>

## Overview

Welcome to **The HigherSelf Network Server** - an intelligent automation platform designed specifically for art galleries, wellness centers, and consultancy businesses. Our system creates harmony between your business operations through a unique agent-based architecture with Notion as the central hub.

### What Makes Us Special

The HigherSelf Network Server features a team of **named agent personalities**, each with distinct characteristics and responsibilities. These agents work together seamlessly to automate your workflows while maintaining the human touch that makes your business special.

<div align="center">
  <img src="https://via.placeholder.com/800x400?text=Agent+System+Visualization" alt="Agent System Visualization" width="80%">
</div>

### Notion as Your Central Hub

All data, workflows, and communications flow through Notion, creating a unified system that's both powerful and user-friendly. Your team already knows and loves Notion - now it becomes the command center for your entire operation.

## Core Features

<div class="features-grid" style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px;">

<div class="feature-card">

### Notion-Powered Operations

- **Centralized Database Hub**: 16 interconnected Notion databases
- **Real-time Synchronization**: All systems stay in perfect harmony
- **Visual Workflow Tracking**: See exactly where every process stands
- **Customizable Views**: Adapt Notion views to your team's needs

</div>

<div class="feature-card">

### Intelligent Agent System

- **Named Agent Personalities**: Each with unique characteristics
- **Specialized Capabilities**: Experts in their respective domains
- **Autonomous Decision Making**: Agents handle routine tasks independently
- **Graceful Orchestration**: Coordinated by the Grace Fields system

</div>

<div class="feature-card">

### Seamless Integrations

- **Comprehensive API Support**: Connect with all your essential tools
- **Webhook Endpoints**: Receive real-time data from external systems
- **Bidirectional Sync**: Data flows both ways between systems
- **Secure Authentication**: All connections use modern security standards

</div>

<div class="feature-card">

### Robust Architecture

- **Pydantic Data Validation**: Ensures data integrity throughout
- **State Machine Workflows**: Structured processes with clear stages
- **Comprehensive Logging**: Complete audit trail of all activities
- **Extensible Design**: Easily add new capabilities as you grow

</div>

</div>

## Notion Database Structure

<div align="center">
  <img src="https://via.placeholder.com/800x500?text=Notion+Database+Structure" alt="Notion Database Structure" width="80%">
</div>

The HigherSelf Network Server uses a carefully designed system of 16 interconnected Notion databases that work together to create a powerful, flexible automation platform.

<div class="database-container" style="margin-top: 30px;">

<details open>
<summary><h3>Core Operational Databases</h3></summary>

<div class="database-grid" style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-top: 15px;">

<div class="database-card" style="border: 1px solid #e1e4e8; border-radius: 10px; padding: 15px; background-color: #f6f8fa;">
  <h4>Business Entities</h4>
  <p>Registry of all business entities using the system (art gallery, wellness center, consultancy)</p>
  <div style="font-size: 0.8em; color: #666;">
    <p><strong>Key Properties:</strong> Name, Type, Contact Info, Logo</p>
    <p><strong>Relations:</strong> Products, Workflows, Team Members</p>
  </div>
</div>

<div class="database-card" style="border: 1px solid #e1e4e8; border-radius: 10px; padding: 15px; background-color: #f6f8fa;">
  <h4>Contacts & Profiles</h4>
  <p>Unified customer/contact database for all entities and interactions</p>
  <div style="font-size: 0.8em; color: #666;">
    <p><strong>Key Properties:</strong> Name, Email, Phone, Tags</p>
    <p><strong>Relations:</strong> Bookings, Orders, Feedback</p>
  </div>
</div>

<div class="database-card" style="border: 1px solid #e1e4e8; border-radius: 10px; padding: 15px; background-color: #f6f8fa;">
  <h4>Community Hub</h4>
  <p>Community member profiles and engagement tracking</p>
  <div style="font-size: 0.8em; color: #666;">
    <p><strong>Key Properties:</strong> Member Since, Engagement Level</p>
    <p><strong>Relations:</strong> Events, Content, Discussions</p>
  </div>
</div>

<div class="database-card" style="border: 1px solid #e1e4e8; border-radius: 10px; padding: 15px; background-color: #f6f8fa;">
  <h4><img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/package-24.svg" alt="Package" width="16" height="16" /> Products & Services</h4>
  <p>Catalog of all available products and services across businesses</p>
  <div style="font-size: 0.8em; color: #666;">
    <p><strong>Key Properties:</strong> Name, Type, Price, Availability</p>
    <p><strong>Relations:</strong> Business Entity, Orders, Content</p>
  </div>
</div>

<div class="database-card" style="border: 1px solid #e1e4e8; border-radius: 10px; padding: 15px; background-color: #f6f8fa;">
  <h4><img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/gear-24.svg" alt="Gear" width="16" height="16" /> Active Workflows</h4>
  <p>Currently active workflow instances being processed</p>
  <div style="font-size: 0.8em; color: #666;">
    <p><strong>Key Properties:</strong> Status, Stage, Start Date</p>
    <p><strong>Relations:</strong> Tasks, Contacts, Template</p>
  </div>
</div>

<div class="database-card" style="border: 1px solid #e1e4e8; border-radius: 10px; padding: 15px; background-color: #f6f8fa;">
  <h4><img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/megaphone-24.svg" alt="Megaphone" width="16" height="16" /> Marketing Campaigns</h4>
  <p>Marketing initiatives and performance tracking</p>
  <div style="font-size: 0.8em; color: #666;">
    <p><strong>Key Properties:</strong> Name, Channel, Status, Metrics</p>
    <p><strong>Relations:</strong> Audience Segments, Content</p>
  </div>
</div>

<div class="database-card" style="border: 1px solid #e1e4e8; border-radius: 10px; padding: 15px; background-color: #f6f8fa;">
  <h4><img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/pencil-24.svg" alt="Pencil" width="16" height="16" /> Feedback & Surveys</h4>
  <p>Customer feedback and survey responses</p>
  <div style="font-size: 0.8em; color: #666;">
    <p><strong>Key Properties:</strong> Type, Rating, Date, Source</p>
    <p><strong>Relations:</strong> Contact, Product/Service</p>
  </div>
</div>

<div class="database-card" style="border: 1px solid #e1e4e8; border-radius: 10px; padding: 15px; background-color: #f6f8fa;">
  <h4><img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/trophy-24.svg" alt="Trophy" width="16" height="16" /> Rewards & Bounties</h4>
  <p>Incentive programs and achievements</p>
  <div style="font-size: 0.8em; color: #666;">
    <p><strong>Key Properties:</strong> Type, Value, Criteria</p>
    <p><strong>Relations:</strong> Contacts, Campaigns</p>
  </div>
</div>

<div class="database-card" style="border: 1px solid #e1e4e8; border-radius: 10px; padding: 15px; background-color: #f6f8fa;">
  <h4><img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/check-24.svg" alt="Check" width="16" height="16" /> Master Tasks</h4>
  <p>Centralized task management system</p>
  <div style="font-size: 0.8em; color: #666;">
    <p><strong>Key Properties:</strong> Title, Status, Due Date, Priority</p>
    <p><strong>Relations:</strong> Assignee, Workflow, Business Entity</p>
  </div>
</div>

</div>
</details>

<details open>
<summary><h3><img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/device-desktop-24.svg" alt="Desktop" width="18" height="18" /> Agent & System Support Databases</h3></summary>

<div class="database-grid" style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-top: 15px;">

<div class="database-card" style="border: 1px solid #e1e4e8; border-radius: 10px; padding: 15px; background-color: #f6f8fa;">
  <h4><img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/comment-discussion-24.svg" alt="Comment" width="16" height="16" /> Agent Communication</h4>
  <p>Record of all agent interactions and messages</p>
  <div style="font-size: 0.8em; color: #666;">
    <p><strong>Key Properties:</strong> Sender, Recipient, Message Type</p>
    <p><strong>Relations:</strong> Workflows, Tasks</p>
  </div>
</div>

<div class="database-card" style="border: 1px solid #e1e4e8; border-radius: 10px; padding: 15px; background-color: #f6f8fa;">
  <h4><img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/checklist-24.svg" alt="Checklist" width="16" height="16" /> Agent Registry</h4>
  <p>Inventory of all available agents and their capabilities</p>
  <div style="font-size: 0.8em; color: #666;">
    <p><strong>Key Properties:</strong> Name, Type, Status, Version</p>
    <p><strong>Relations:</strong> APIs Used, Business Entities</p>
  </div>
</div>

<div class="database-card" style="border: 1px solid #e1e4e8; border-radius: 10px; padding: 15px; background-color: #f6f8fa;">
  <h4><img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/plug-24.svg" alt="Plug" width="16" height="16" /> API Integrations</h4>
  <p>Catalog of all integrated external services</p>
  <div style="font-size: 0.8em; color: #666;">
    <p><strong>Key Properties:</strong> Service Name, Status, Last Sync</p>
    <p><strong>Relations:</strong> Agents, Workflows</p>
  </div>
</div>

<div class="database-card" style="border: 1px solid #e1e4e8; border-radius: 10px; padding: 15px; background-color: #f6f8fa;">
  <h4><img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/sync-24.svg" alt="Sync" width="16" height="16" /> Data Transformations</h4>
  <p>Data mapping configurations between systems</p>
  <div style="font-size: 0.8em; color: #666;">
    <p><strong>Key Properties:</strong> Source, Target, Mapping Rules</p>
    <p><strong>Relations:</strong> API Integrations</p>
  </div>
</div>

<div class="database-card" style="border: 1px solid #e1e4e8; border-radius: 10px; padding: 15px; background-color: #f6f8fa;">
  <h4><img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/bell-24.svg" alt="Bell" width="16" height="16" /> Notification Templates</h4>
  <p>Templates for system and user notifications</p>
  <div style="font-size: 0.8em; color: #666;">
    <p><strong>Key Properties:</strong> Type, Channel, Subject, Body</p>
    <p><strong>Relations:</strong> Workflows, Triggers</p>
  </div>
</div>

<div class="database-card" style="border: 1px solid #e1e4e8; border-radius: 10px; padding: 15px; background-color: #f6f8fa;">
  <h4><img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/book-24.svg" alt="Book" width="16" height="16" /> Use Cases Library</h4>
  <p>Documented use cases for reference</p>
  <div style="font-size: 0.8em; color: #666;">
    <p><strong>Key Properties:</strong> Title, Category, Steps</p>
    <p><strong>Relations:</strong> Workflows, Business Entities</p>
  </div>
</div>

<div class="database-card" style="border: 1px solid #e1e4e8; border-radius: 10px; padding: 15px; background-color: #f6f8fa;">
  <h4><img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/checklist-24.svg" alt="Checklist" width="16" height="16" /> Workflows Library</h4>
  <p>Template workflows that can be instantiated</p>
  <div style="font-size: 0.8em; color: #666;">
    <p><strong>Key Properties:</strong> Name, Type, Stages, Triggers</p>
    <p><strong>Relations:</strong> Tasks, Agents, Business Entities</p>
  </div>
</div>

</div>
</details>

</div>

## Key Automation Flows

<div align="center">
  <img src="https://via.placeholder.com/800x400?text=Automation+Flows+Diagram" alt="Automation Flows" width="80%">
</div>

The HigherSelf Network Server implements powerful automation flows that streamline operations across your businesses. Each flow is handled by specialized agents working together through Notion.

<div class="flows-container" style="margin-top: 30px;">

<div class="flow-card" style="border: 1px solid #e1e4e8; border-radius: 10px; padding: 20px; margin-bottom: 20px; background-color: #f6f8fa;">
  <div style="display: flex; align-items: center; margin-bottom: 15px;">
    <div style="font-size: 2em; margin-right: 15px;"><img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/star-24.svg" alt="Star" width="24" height="24" /></div>
    <div>
      <h3 style="margin: 0;">Lead Capture & Nurturing</h3>
      <p style="margin: 5px 0 0 0; color: #666; font-style: italic;">Handled by Nyra & Ruvo</p>
    </div>
  </div>

  <p>Consolidates leads from multiple sources (Typeform, website forms, social media) and nurtures them through personalized follow-up sequences.</p>

  <div style="background-color: #e6f7ff; border-radius: 5px; padding: 10px; margin-top: 10px;">
    <p style="margin: 0; font-weight: bold;">Key Features:</p>
    <ul style="margin: 5px 0 0 0; padding-left: 20px;">
      <li>Automatic lead qualification and scoring</li>
      <li>Personalized follow-up task creation</li>
      <li>Interest-based tagging and segmentation</li>
      <li>Conversion tracking across touchpoints</li>
    </ul>
  </div>
</div>

<div class="flow-card" style="border: 1px solid #e1e4e8; border-radius: 10px; padding: 20px; margin-bottom: 20px; background-color: #f6f8fa;">
  <div style="display: flex; align-items: center; margin-bottom: 15px;">
    <div style="font-size: 2em; margin-right: 15px;"><img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/calendar-24.svg" alt="Calendar" width="24" height="24" /></div>
    <div>
      <h3 style="margin: 0;">Booking & Order Management</h3>
      <p style="margin: 5px 0 0 0; color: #666; font-style: italic;">Handled by Solari & Ruvo</p>
    </div>
  </div>

  <p>Manages the complete lifecycle of bookings (retreats, consultations) and orders (art pieces, products) from initial purchase through fulfillment.</p>

  <div style="background-color: #e6f7ff; border-radius: 5px; padding: 10px; margin-top: 10px;">
    <p style="margin: 0; font-weight: bold;">Key Features:</p>
    <ul style="margin: 5px 0 0 0; padding-left: 20px;">
      <li>Automated confirmation and reminder emails</li>
      <li>Preparation task creation for team members</li>
      <li>Payment tracking and receipt generation</li>
      <li>Post-experience follow-up sequences</li>
    </ul>
  </div>
</div>

<div class="flow-card" style="border: 1px solid #e1e4e8; border-radius: 10px; padding: 20px; margin-bottom: 20px; background-color: #f6f8fa;">
  <div style="display: flex; align-items: center; margin-bottom: 15px;">
    <div style="font-size: 2em; margin-right: 15px;"><img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/megaphone-24.svg" alt="Megaphone" width="24" height="24" /></div>
    <div>
      <h3 style="margin: 0;">Marketing Campaign Orchestration</h3>
      <p style="margin: 5px 0 0 0; color: #666; font-style: italic;">Handled by Liora, Elan & Zevi</p>
    </div>
  </div>

  <p>Coordinates multi-channel marketing campaigns across email, social media, and other platforms with targeted messaging for different audience segments.</p>

  <div style="background-color: #e6f7ff; border-radius: 5px; padding: 10px; margin-top: 10px;">
    <p style="margin: 0; font-weight: bold;">Key Features:</p>
    <ul style="margin: 5px 0 0 0; padding-left: 20px;">
      <li>Audience segmentation and targeting</li>
      <li>Content scheduling and distribution</li>
      <li>Performance tracking and analytics</li>
      <li>A/B testing and optimization</li>
    </ul>
  </div>
</div>

<div class="flow-card" style="border: 1px solid #e1e4e8; border-radius: 10px; padding: 20px; margin-bottom: 20px; background-color: #f6f8fa;">
  <div style="display: flex; align-items: center; margin-bottom: 15px;">
    <div style="font-size: 2em; margin-right: 15px;"><img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/person-24.svg" alt="Person" width="24" height="24" /></div>
    <div>
      <h3 style="margin: 0;">Community Engagement</h3>
      <p style="margin: 5px 0 0 0; color: #666; font-style: italic;">Handled by Sage & Elan</p>
    </div>
  </div>

  <p>Nurtures community relationships through Circle.so, facilitating discussions, events, and content sharing to build a vibrant, engaged community.</p>

  <div style="background-color: #e6f7ff; border-radius: 5px; padding: 10px; margin-top: 10px;">
    <p style="margin: 0; font-weight: bold;">Key Features:</p>
    <ul style="margin: 5px 0 0 0; padding-left: 20px;">
      <li>New member welcome sequences</li>
      <li>Engagement tracking and nurturing</li>
      <li>Content curation and sharing</li>
      <li>Event coordination and follow-up</li>
    </ul>
  </div>
</div>

<div class="flow-card" style="border: 1px solid #e1e4e8; border-radius: 10px; padding: 20px; margin-bottom: 20px; background-color: #f6f8fa;">
  <div style="display: flex; align-items: center; margin-bottom: 15px;">
    <div style="font-size: 2em; margin-right: 15px;"><img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/file-24.svg" alt="File" width="24" height="24" /></div>
    <div>
      <h3 style="margin: 0;">Content Lifecycle Management</h3>
      <p style="margin: 5px 0 0 0; color: #666; font-style: italic;">Handled by Elan & Liora</p>
    </div>
  </div>

  <p>Manages the complete content creation process from ideation through creation, review, publication, and performance analysis.</p>

  <div style="background-color: #e6f7ff; border-radius: 5px; padding: 10px; margin-top: 10px;">
    <p style="margin: 0; font-weight: bold;">Key Features:</p>
    <ul style="margin: 5px 0 0 0; padding-left: 20px;">
      <li>Content calendar management</li>
      <li>Review and approval workflows</li>
      <li>Multi-platform distribution</li>
      <li>Performance tracking and insights</li>
    </ul>
  </div>
</div>

</div>

<div align="center" style="margin-top: 30px;">
  <a href="./documentation/AGENT_SYSTEM_GUIDE.md#business-workflows" style="display: inline-block; padding: 10px 20px; background-color: #4CAF50; color: white; text-decoration: none; border-radius: 5px; font-weight: bold;"><img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/book-24.svg" alt="Book" width="16" height="16" /> View All Business Workflows</a>
</div>

## Meet Your Agent Team

<div align="center">
  <img src="https://via.placeholder.com/900x500?text=Agent+Team+Illustration" alt="Agent Team" width="80%">
</div>

The HigherSelf Network Server features a unique team of agent personalities, each with their own character, tone, and specialized skills. These aren't just algorithms - they're digital team members designed to bring intention and care to your automated processes.

<div class="agent-grid" style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-top: 30px;">

<div class="agent-card" style="border: 1px solid #e1e4e8; border-radius: 10px; padding: 20px; background-color: #f6f8fa;">
  <h3>Nyra</h3>
  <p><strong>Lead Capture Specialist</strong></p>
  <p><em>Intuitive & Responsive</em></p>
  <p>Like flowing water (from Sanskrit <em>nira</em>), Nyra channels new connections from multiple sources into your Notion ecosystem with grace and attention to detail.</p>
  <p><strong>Specialty:</strong> Capturing and nurturing new leads</p>
</div>

<div class="agent-card" style="border: 1px solid #e1e4e8; border-radius: 10px; padding: 20px; background-color: #f6f8fa;">
  <h3>Solari</h3>
  <p><strong>Booking & Order Manager</strong></p>
  <p><em>Clear & Luminous</em></p>
  <p>Bringing solar precision to appointment and order processes, Solari manages the structured flow of bookings and purchases with clarity and warmth.</p>
  <p><strong>Specialty:</strong> Managing bookings, appointments, and orders</p>
</div>

<div class="agent-card" style="border: 1px solid #e1e4e8; border-radius: 10px; padding: 20px; background-color: #f6f8fa;">
  <h3>Ruvo</h3>
  <p><strong>Task Orchestrator</strong></p>
  <p><em>Grounded & Task-driven</em></p>
  <p>From the Latin root <em>ruvus</em> (resolve), Ruvo handles the practical execution of workflow-generated tasks with calm efficiency and reliability.</p>
  <p><strong>Specialty:</strong> Creating, assigning, and tracking tasks</p>
</div>

<div class="agent-card" style="border: 1px solid #e1e4e8; border-radius: 10px; padding: 20px; background-color: #f6f8fa;">
  <h3>Liora</h3>
  <p><strong>Marketing Strategist</strong></p>
  <p><em>Elegant & Strategic</em></p>
  <p>Liora (Hebrew for "light") brings illumination and strategic thinking to your marketing campaigns, maintaining clarity amid complex promotional activities.</p>
  <p><strong>Specialty:</strong> Managing marketing campaigns and outreach</p>
</div>

<div class="agent-card" style="border: 1px solid #e1e4e8; border-radius: 10px; padding: 20px; background-color: #f6f8fa;">
  <h3>Sage</h3>
  <p><strong>Community Curator</strong></p>
  <p><em>Warm & Connected</em></p>
  <p>Sage nurtures your community with wisdom and care, holding space for authentic relationships and meaningful engagement in your Circle.so community.</p>
  <p><strong>Specialty:</strong> Facilitating community engagement</p>
</div>

<div class="agent-card" style="border: 1px solid #e1e4e8; border-radius: 10px; padding: 20px; background-color: #f6f8fa;">
  <h3>Elan</h3>
  <p><strong>Content Choreographer</strong></p>
  <p><em>Creative & Adaptive</em></p>
  <p>With both flair and disciplined order, Elan manages the lifecycle of your content from conception to publication across multiple platforms.</p>
  <p><strong>Specialty:</strong> Managing content creation and distribution</p>
</div>

<div class="agent-card" style="border: 1px solid #e1e4e8; border-radius: 10px; padding: 20px; background-color: #f6f8fa;">
  <h3>Zevi</h3>
  <p><strong>Audience Analyst</strong></p>
  <p><em>Analytical & Sharp</em></p>
  <p>Like its wolf namesake, Zevi keenly observes patterns in audience behavior to create meaningful segments for targeted engagement.</p>
  <p><strong>Specialty:</strong> Analyzing and segmenting audiences</p>
</div>

<div class="agent-card" style="border: 1px solid #e1e4e8; border-radius: 10px; padding: 20px; background-color: #f6f8fa;">
  <h3>Grace Fields</h3>
  <p><strong>System Orchestrator</strong></p>
  <p><em>Harmonious & Coordinating</em></p>
  <p>At the center of it all, Grace ensures that each agent is activated at the right time, maintaining the flow of information throughout the system.</p>
  <p><strong>Specialty:</strong> Coordinating all agent activities</p>
</div>

</div>

<div align="center" style="margin-top: 30px;">
  <a href="./documentation/AGENT_SYSTEM_GUIDE.md" style="display: inline-block; padding: 10px 20px; background-color: #4CAF50; color: white; text-decoration: none; border-radius: 5px; font-weight: bold;"><img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/book-24.svg" alt="Book" width="16" height="16" /> Read the Complete Agent System Guide</a>
</div>



## Getting Started

<div class="getting-started-container" style="display: flex; gap: 30px; margin-top: 20px;">

<div class="installation-guide" style="flex: 1;">

### Prerequisites

Before you begin, ensure you have:

- <img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/check-24.svg" alt="Check" width="16" height="16" /> Python 3.10 or higher
- <img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/check-24.svg" alt="Check" width="16" height="16" /> Docker (recommended for production)
- <img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/check-24.svg" alt="Check" width="16" height="16" /> Notion account with admin access
- <img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/check-24.svg" alt="Check" width="16" height="16" /> API keys for your integrated services

### Installation Options

<details>
<summary><b><img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/container-24.svg" alt="Container" width="16" height="16" /> Docker Installation (Recommended)</b></summary>

```bash
# Clone the repository
git clone https://github.com/Utak-West/The-HigherSelf-Network-Server.git
cd The-HigherSelf-Network-Server

# Configure environment
cp .env.example .env
# Edit .env with your API credentials

# Start with Docker Compose
docker-compose up -d
```

This will start the server and all required services in containers.
</details>

<details>
<summary><b><img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/code-24.svg" alt="Code" width="16" height="16" /> Direct Python Installation</b></summary>

```bash
# Clone the repository
git clone https://github.com/Utak-West/The-HigherSelf-Network-Server.git
cd The-HigherSelf-Network-Server

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API credentials

# Start the server
python main.py
```
</details>

<details>
<summary><b><img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/cloud-24.svg" alt="Cloud" width="16" height="16" /> Cloud Deployment</b></summary>

For detailed cloud deployment instructions, see our [Deployment Guide](./documentation/DEPLOYMENT_AND_TRAINING.md).

We support:
- AWS Elastic Container Service
- Google Cloud Run
- Azure Container Instances
- Digital Ocean App Platform
</details>

</div>

<div class="configuration-guide" style="flex: 1;">

### Configuration

The system is configured through environment variables in the `.env` file:

<details>
<summary><b><img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/key-24.svg" alt="Key" width="16" height="16" /> API Credentials</b></summary>

```env
# Notion API (Required)
NOTION_API_TOKEN=your_notion_api_token
NOTION_PARENT_PAGE_ID=your_parent_page_id

# Third-party Services
TYPEFORM_API_KEY=your_typeform_api_key
WOOCOMMERCE_CONSUMER_KEY=your_woocommerce_key
WOOCOMMERCE_CONSUMER_SECRET=your_woocommerce_secret
AMELIA_API_KEY=your_amelia_api_key
CIRCLE_API_TOKEN=your_circle_api_token
BEEHIIV_API_KEY=your_beehiiv_api_key
```
</details>

<details>
<summary><b><img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/briefcase-24.svg" alt="Briefcase" width="16" height="16" /> Notion Database Setup</b></summary>

Run our automated setup tool to create all required Notion databases:

```bash
# Using Docker
docker-compose run --rm windsurf-agent python -m tools.notion_db_setup

# Using Python directly
python -m tools.notion_db_setup
```

This will:
1. Create 16 interconnected databases in your Notion workspace
2. Configure proper relations between databases
3. Update your `.env` file with all database IDs
4. Set up initial templates and views
</details>

<details>
<summary><b><img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/lock-24.svg" alt="Lock" width="16" height="16" /> Security Settings</b></summary>

```env
# Webhook security
WEBHOOK_SECRET=your_secure_random_string

# Server settings
SERVER_PORT=8000
LOG_LEVEL=INFO
```

For production, we recommend:
- Using a strong, randomly generated webhook secret
- Setting up SSL/TLS encryption
- Implementing proper access controls
</details>

</div>

</div>

<div align="center" style="margin-top: 30px;">
  <a href="./documentation/DEPLOYMENT_AND_TRAINING.md" style="display: inline-block; padding: 10px 20px; background-color: #4361EE; color: white; text-decoration: none; border-radius: 5px; font-weight: bold;"><img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/book-24.svg" alt="Book" width="16" height="16" /> Complete Deployment Guide</a>
</div>

## Business Workflows

<div align="center">
  <img src="https://via.placeholder.com/800x400?text=Workflow+Visualization" alt="Workflow Visualization" width="80%">
</div>

The HigherSelf Network Server automates key business workflows for your art gallery, wellness center, and consultancy operations:

<div class="workflow-grid" style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; margin-top: 30px;">

<div class="workflow-card" style="border: 1px solid #e1e4e8; border-radius: 10px; padding: 20px; background-color: #f6f8fa;">
  <h3><img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/paintbrush-24.svg" alt="Paintbrush" width="18" height="18" /> Art Gallery Operations</h3>
  <ul>
    <li><strong>Exhibition Planning & Management</strong>: From concept to opening night</li>
    <li><strong>Artist Relationship Management</strong>: Track communications and agreements</li>
    <li><strong>Artwork Sales Processing</strong>: Handle purchases, shipping, and commissions</li>
    <li><strong>Collector Engagement</strong>: Nurture relationships with art collectors</li>
  </ul>
</div>

<div class="workflow-card" style="border: 1px solid #e1e4e8; border-radius: 10px; padding: 20px; background-color: #f6f8fa;">
  <h3><img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/person-24.svg" alt="Person" width="18" height="18" /> Wellness Center Operations</h3>
  <ul>
    <li><strong>Retreat Booking Management</strong>: Handle registrations and preparations</li>
    <li><strong>Practitioner Scheduling</strong>: Coordinate sessions and resources</li>
    <li><strong>Client Journey Tracking</strong>: Monitor wellness progress and engagement</li>
    <li><strong>Program Development</strong>: Create and refine wellness offerings</li>
  </ul>
</div>

<div class="workflow-card" style="border: 1px solid #e1e4e8; border-radius: 10px; padding: 20px; background-color: #f6f8fa;">
  <h3><img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/briefcase-24.svg" alt="Briefcase" width="18" height="18" /> Consultancy Operations</h3>
  <ul>
    <li><strong>Client Onboarding</strong>: Streamline the intake process</li>
    <li><strong>Project Management</strong>: Track deliverables and milestones</li>
    <li><strong>Knowledge Management</strong>: Organize insights and resources</li>
    <li><strong>Client Reporting</strong>: Generate and deliver professional reports</li>
  </ul>
</div>

<div class="workflow-card" style="border: 1px solid #e1e4e8; border-radius: 10px; padding: 20px; background-color: #f6f8fa;">
  <h3><img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/globe-24.svg" alt="Globe" width="18" height="18" /> Cross-Business Operations</h3>
  <ul>
    <li><strong>Marketing Campaign Management</strong>: Coordinate multi-channel outreach</li>
    <li><strong>Content Creation & Distribution</strong>: Manage your content lifecycle</li>
    <li><strong>Community Engagement</strong>: Nurture your online community</li>
    <li><strong>Lead Capture & Nurturing</strong>: Convert interest into engagement</li>
  </ul>
</div>

</div>

## Integration Ecosystem

The HigherSelf Network Server connects with your essential business tools:

<div class="integration-container" style="display: flex; flex-wrap: wrap; gap: 15px; margin-top: 20px;">

<div class="integration-badge" style="background-color: #f0f0f0; padding: 10px 15px; border-radius: 20px; display: flex; align-items: center; gap: 8px;">
  <span style="font-weight: bold;">Notion</span>
  <span style="color: #666; font-size: 0.9em;">Central Hub</span>
</div>

<div class="integration-badge" style="background-color: #f0f0f0; padding: 10px 15px; border-radius: 20px; display: flex; align-items: center; gap: 8px;">
  <span style="font-weight: bold;">Typeform</span>
  <span style="color: #666; font-size: 0.9em;">Form Capture</span>
</div>

<div class="integration-badge" style="background-color: #f0f0f0; padding: 10px 15px; border-radius: 20px; display: flex; align-items: center; gap: 8px;">
  <span style="font-weight: bold;">WooCommerce</span>
  <span style="color: #666; font-size: 0.9em;">E-commerce</span>
</div>

<div class="integration-badge" style="background-color: #f0f0f0; padding: 10px 15px; border-radius: 20px; display: flex; align-items: center; gap: 8px;">
  <span style="font-weight: bold;">Amelia</span>
  <span style="color: #666; font-size: 0.9em;">Booking</span>
</div>

<div class="integration-badge" style="background-color: #f0f0f0; padding: 10px 15px; border-radius: 20px; display: flex; align-items: center; gap: 8px;">
  <span style="font-weight: bold;">Circle.so</span>
  <span style="color: #666; font-size: 0.9em;">Community</span>
</div>

<div class="integration-badge" style="background-color: #f0f0f0; padding: 10px 15px; border-radius: 20px; display: flex; align-items: center; gap: 8px;">
  <span style="font-weight: bold;">Beehiiv</span>
  <span style="color: #666; font-size: 0.9em;">Newsletters</span>
</div>

<div class="integration-badge" style="background-color: #f0f0f0; padding: 10px 15px; border-radius: 20px; display: flex; align-items: center; gap: 8px;">
  <span style="font-weight: bold;">Plaud</span>
  <span style="color: #666; font-size: 0.9em;">Transcription</span>
</div>

<div class="integration-badge" style="background-color: #f0f0f0; padding: 10px 15px; border-radius: 20px; display: flex; align-items: center; gap: 8px;">
  <span style="font-weight: bold;">TutorLM</span>
  <span style="color: #666; font-size: 0.9em;">Learning</span>
</div>

</div>

<details>
<summary><b><img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/rss-24.svg" alt="RSS" width="16" height="16" /> API Endpoints Reference</b></summary>

### Webhook Endpoints

| Service | Endpoint | Description |
|---------|----------|-------------|
| Typeform | `/webhooks/typeform` | Receives form submissions |
| WooCommerce | `/webhooks/woocommerce` | Processes orders and products |
| Amelia | `/webhooks/amelia` | Handles booking events |
| Circle.so | `/webhooks/circleso/new_member` | Processes new community members |
| Circle.so | `/webhooks/circleso/member_activity` | Tracks community engagement |
| Beehiiv | `/webhooks/beehiiv/newsletter/metrics` | Collects newsletter performance |
| Beehiiv | `/webhooks/beehiiv/subscriber` | Manages newsletter subscribers |

### General API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | System health check |
| `/api/forms/submit` | POST | Direct form submission |
| `/workflows/{instance_id}` | GET | Workflow instance details |
| `/api/status/{service_name}` | GET | Integration status check |
| `/api/notion/sync` | POST | Manual Notion synchronization |

</details>

## Documentation

<div class="docs-container" style="display: flex; gap: 20px; margin-top: 20px;">

<div class="doc-card" style="flex: 1; border: 1px solid #e1e4e8; border-radius: 10px; padding: 20px; background-color: #f6f8fa;">
  <h3><img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/play-24.svg" alt="Play" width="18" height="18" /> Deployment Guide</h3>
  <p>Comprehensive instructions for deploying the system in various environments.</p>
  <a href="./documentation/DEPLOYMENT_AND_TRAINING.md" style="color: #0366d6;">Read the Deployment Guide →</a>
</div>

<div class="doc-card" style="flex: 1; border: 1px solid #e1e4e8; border-radius: 10px; padding: 20px; background-color: #f6f8fa;">
  <h3><img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/person-24.svg" alt="Person" width="18" height="18" /> Agent System Guide</h3>
  <p>Detailed information about agent personalities and how to work with them.</p>
  <a href="./documentation/AGENT_SYSTEM_GUIDE.md" style="color: #0366d6;">Read the Agent Guide →</a>
</div>

<div class="doc-card" style="flex: 1; border: 1px solid #e1e4e8; border-radius: 10px; padding: 20px; background-color: #f6f8fa;">
  <h3><img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/search-24.svg" alt="Search" width="18" height="18" /> Monitoring Guide</h3>
  <p>Instructions for monitoring system health and troubleshooting issues.</p>
  <a href="./documentation/MONITORING_AND_TROUBLESHOOTING.md" style="color: #0366d6;">Read the Monitoring Guide →</a>
</div>

</div>

## For Developers

<details>
<summary><b>System Architecture</b></summary>

The HigherSelf Network Server implements a hub-and-spoke architecture with Notion as the central hub:

<div align="center">
  <img src="https://via.placeholder.com/800x500?text=System+Architecture+Diagram" alt="System Architecture" width="80%">
</div>

### Key Components

1. **Models (`/models`)**: Pydantic models defining data structures
2. **Services (`/services`)**: Service classes for external API interactions
3. **Agents (`/agents`)**: Agent implementations with specific responsibilities
4. **API (`/api`)**: FastAPI server for external communication

### Data Flow

1. External events trigger webhook calls to the API
2. Events are processed by appropriate agents
3. Agents create or update records in Notion via the NotionService
4. Workflow instances track the state of business processes
5. History logs maintain a complete audit trail
</details>

<details>
<summary><b>Adding a New Agent</b></summary>

1. Create a new file in the `agents` directory
2. Extend the `BaseAgent` class
3. Implement the required abstract methods
4. Register the agent in `agents/__init__.py`
5. Add initialization in `main.py`

```python
from agents.base_agent import BaseAgent

class MyNewAgent(BaseAgent):
    """
    My new agent that handles specific tasks.
    """

    def __init__(self, notion_client, **kwargs):
        super().__init__(name="MyNewAgent", notion_client=notion_client, **kwargs)
        self.agent_type = "MyNewAgentType"

    async def process_event(self, event_type: str, event_data: dict) -> dict:
        """Process an event received by this agent."""
        # Implementation here
        return {"status": "processed"}

    async def check_health(self) -> dict:
        """Check the health status of this agent."""
        return {"status": "healthy"}
```
</details>

<details>
<summary><b>Adding a New Integration</b></summary>

To add support for a new integration:

1. Add the API platform to `ApiPlatform` enum in `models/base.py`
2. Create new Pydantic models for the integration's data structures
3. Create a new service class in the `services` directory
4. Implement a new agent or extend an existing one
5. Add webhook endpoints if needed

```python
# 1. Add to ApiPlatform enum
class ApiPlatform(str, Enum):
    # Existing platforms...
    MY_NEW_PLATFORM = "my_new_platform"

# 2. Create service class
class MyNewPlatformService(BaseService):
    """Service for interacting with My New Platform."""

    def __init__(self):
        super().__init__(service_name="my_new_platform")
        # Initialize service

    async def validate_connection(self) -> bool:
        """Validate the connection to the service."""
        # Implementation here
        return True
```
</details>

## Support & Community

<div class="support-container" style="display: flex; gap: 20px; margin-top: 20px;">

<div class="support-card" style="flex: 1; border: 1px solid #e1e4e8; border-radius: 10px; padding: 20px; background-color: #f6f8fa;">
  <h3><img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/mail-24.svg" alt="Mail" width="18" height="18" /> Contact Support</h3>
  <p>For questions or assistance, contact The HigherSelf Network team:</p>
  <p><a href="mailto:support@higherself.network">support@higherself.network</a></p>
</div>

<div class="support-card" style="flex: 1; border: 1px solid #e1e4e8; border-radius: 10px; padding: 20px; background-color: #f6f8fa;">
  <h3><img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/star-24.svg" alt="Star" width="18" height="18" /> Training & Consulting</h3>
  <p>Need help getting started? We offer personalized training and consulting services.</p>
  <p><a href="https://higherself.network/training">Learn More</a></p>
</div>

</div>

<div align="center" style="margin-top: 50px; padding: 20px; background-color: #f6f8fa; border-radius: 10px;">
  <p>&copy; 2023-2025 The HigherSelf Network - All Rights Reserved</p>
  <p><small>Proprietary software for art gallery, wellness center, and consultancy automation</small></p>
</div>
