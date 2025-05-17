'use strict';

const crypto = require('crypto');

/**
 * Webhook controller for secure integration with external systems
 * Implements webhook authentication as required by Integration Security Rules
 */

module.exports = {
  /**
   * Handle incoming webhook from external systems
   */
  async handleWebhook(ctx) {
    const { body, headers } = ctx.request;
    
    try {
      // Validate webhook signature
      this.validateWebhookSignature(headers, JSON.stringify(body));
      
      // Process webhook based on source and event type
      const { source, event_type } = body;
      
      let result;
      
      switch (source) {
        case 'notion':
          result = await this.handleNotionWebhook(body);
          break;
        case 'api_gateway':
          result = await this.handleApiGatewayWebhook(body);
          break;
        case 'softr':
          result = await this.handleSoftrWebhook(body);
          break;
        default:
          ctx.throw(400, `Unsupported webhook source: ${source}`);
      }
      
      // Log webhook reception for audit trail
      await strapi.entityService.create('api::webhook-log.webhook-log', {
        data: {
          source,
          eventType: event_type,
          timestamp: new Date(),
          status: 'success',
          requestBody: JSON.stringify(body)
        }
      });
      
      return { success: true, result };
    } catch (error) {
      // Log webhook error for audit trail
      await strapi.entityService.create('api::webhook-log.webhook-log', {
        data: {
          source: body?.source || 'unknown',
          eventType: body?.event_type || 'unknown',
          timestamp: new Date(),
          status: 'error',
          errorMessage: error.message,
          requestBody: JSON.stringify(body)
        }
      });
      
      ctx.throw(error.status || 500, error.message);
    }
  },
  
  /**
   * Validate webhook signature for security
   * @param {Object} headers Request headers
   * @param {string} body Request body as string
   */
  validateWebhookSignature(headers, body) {
    const signature = headers['x-webhook-signature'];
    const webhookSecret = process.env.WEBHOOK_SECRET;
    
    if (!signature || !webhookSecret) {
      throw new Error('Missing webhook signature or secret');
    }
    
    const hmac = crypto.createHmac('sha256', webhookSecret);
    hmac.update(body);
    const calculatedSignature = hmac.digest('hex');
    
    if (signature !== calculatedSignature) {
      throw new Error('Invalid webhook signature');
    }
  },
  
  /**
   * Handle webhooks from Notion
   * @param {Object} data Webhook data
   */
  async handleNotionWebhook(data) {
    const { event_type, payload } = data;
    
    switch (event_type) {
      case 'database.updated':
        return await this.syncNotionDatabaseUpdate(payload);
      case 'page.created':
        return await this.syncNotionPageCreation(payload);
      case 'page.updated':
        return await this.syncNotionPageUpdate(payload);
      default:
        throw new Error(`Unsupported Notion event type: ${event_type}`);
    }
  },
  
  /**
   * Handle webhooks from API Gateway
   * @param {Object} data Webhook data
   */
  async handleApiGatewayWebhook(data) {
    const { event_type, payload } = data;
    
    switch (event_type) {
      case 'workflow_state_change':
        return await this.processWorkflowStateChange(payload);
      case 'agent_communication':
        return await this.processAgentCommunication(payload);
      default:
        throw new Error(`Unsupported API Gateway event type: ${event_type}`);
    }
  },
  
  /**
   * Handle webhooks from Softr interfaces
   * @param {Object} data Webhook data
   */
  async handleSoftrWebhook(data) {
    const { event_type, payload } = data;
    
    switch (event_type) {
      case 'user_event':
        return await this.processSoftrUserEvent(payload);
      case 'form_submission':
        return await this.processSoftrFormSubmission(payload);
      default:
        throw new Error(`Unsupported Softr event type: ${event_type}`);
    }
  },
  
  /**
   * Process Notion database update
   * @param {Object} payload Webhook payload
   */
  async syncNotionDatabaseUpdate(payload) {
    // Implementation would sync Notion database changes to Strapi
    // based on the database type and changes
    return { message: 'Notion database update processed' };
  },
  
  /**
   * Process Notion page creation
   * @param {Object} payload Webhook payload
   */
  async syncNotionPageCreation(payload) {
    // Implementation would create corresponding Strapi entity
    // based on the Notion page type
    return { message: 'Notion page creation processed' };
  },
  
  /**
   * Process Notion page update
   * @param {Object} payload Webhook payload
   */
  async syncNotionPageUpdate(payload) {
    // Implementation would update corresponding Strapi entity
    // based on the Notion page type and changes
    return { message: 'Notion page update processed' };
  },
  
  /**
   * Process workflow state change from API Gateway
   * @param {Object} payload Webhook payload
   */
  async processWorkflowStateChange(payload) {
    // Implementation would update workflow state in Strapi
    // based on the entity type and new state
    return { message: 'Workflow state change processed' };
  },
  
  /**
   * Process agent communication from API Gateway
   * @param {Object} payload Webhook payload
   */
  async processAgentCommunication(payload) {
    // Implementation would handle agent communication
    // based on the agent type and message
    return { message: 'Agent communication processed' };
  },
  
  /**
   * Process Softr user event
   * @param {Object} payload Webhook payload
   */
  async processSoftrUserEvent(payload) {
    // Implementation would handle user events from Softr interfaces
    // based on the event type and user information
    return { message: 'Softr user event processed' };
  },
  
  /**
   * Process Softr form submission
   * @param {Object} payload Webhook payload
   */
  async processSoftrFormSubmission(payload) {
    // Implementation would handle form submissions from Softr interfaces
    // based on the form type and submitted data
    return { message: 'Softr form submission processed' };
  }
};
