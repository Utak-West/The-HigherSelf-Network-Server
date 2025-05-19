# BetterMode vs Circle.so Comparison

This document outlines the key differences between BetterMode and Circle.so platforms to guide the migration process for The HigherSelf Network Server.

## Platform Overview

| Feature | BetterMode | Circle.so |
|---------|------------|-----------|
| **Primary Focus** | Customer communities for brands and businesses | Creator communities with monetization |
| **Target Users** | Businesses and organizations | Creators and course builders |
| **Pricing** | Starting at $599/month | Starting at $49/month |
| **Customization** | Extensive with block-based builder | Limited customization options |

## Key Differences

### 1. Architecture and Design

- **BetterMode**: Offers a block-based builder with extensive customization options, premade templates, and a flexible design studio
- **Circle.so**: Simpler interface with limited customization options

### 2. Integration Capabilities

- **BetterMode**: Robust App Store with direct integrations to business tools (Zapier, Intercom, Zendesk, Salesforce, etc.)
- **Circle.so**: Limited direct integrations, primarily focused on creator monetization tools

### 3. API and Developer Tools

- **BetterMode**: Comprehensive API, webhooks, and Developer Portal for custom workflows
- **Circle.so**: Basic API with limited customization options

### 4. Embedding Options

- **BetterMode**: Advanced embed tools and React SDK for deep integration into websites and apps
- **Circle.so**: Basic embedding via iFrame

### 5. Authentication and SSO

- **BetterMode**: Multiple SSO options (OAuth, Okta, JWT, custom SSO) that can be combined
- **Circle.so**: Limited SSO options (Auth0)

### 6. Gamification

- **BetterMode**: Comprehensive gamification tools (badges, reputation scores, leaderboards)
- **Circle.so**: Limited gamification features

### 7. Moderation Tools

- **BetterMode**: Advanced moderation tools (keyword blocklist, profanity filter, moderation rules, moderation panel)
- **Circle.so**: Basic moderation capabilities

### 8. Multilingual Support

- **BetterMode**: Supports multiple languages including English, Spanish, French, German
- **Circle.so**: Limited language support

## API Differences

### BetterMode API

- GraphQL-based API
- Comprehensive authentication options
- Webhook support for real-time events
- Developer Portal for custom app development

### Circle.so API

- REST-based API
- Limited webhook functionality
- Fewer integration options

## Migration Considerations

When migrating from Circle.so to BetterMode, consider the following:

1. **Data Migration**: Plan for migrating community members, content, and activity data
2. **API Integration**: Update all API calls to use BetterMode's GraphQL API
3. **Authentication**: Implement BetterMode's authentication methods
4. **Webhooks**: Update webhook handlers to process BetterMode's webhook format
5. **Custom Features**: Leverage BetterMode's App Store and Developer Portal for custom functionality
6. **User Experience**: Take advantage of BetterMode's customization options to enhance user experience

## Feature Mapping

| Circle.so Feature | BetterMode Equivalent |
|-------------------|------------------------|
| Community Spaces | Spaces with Templates |
| Member Profiles | Custom Member Profiles |
| Direct Messages | Private Messaging |
| Group Chat | Discussion Spaces |
| Events | Event Spaces |
| Content Posts | Discussion, Article, and Q&A Spaces |
| Member Directory | Member Directory with Custom Fields |
| Notifications | Notification System with Email Digests |

This comparison will guide the implementation of BetterMode as a replacement for Circle.so in The HigherSelf Network Server.
