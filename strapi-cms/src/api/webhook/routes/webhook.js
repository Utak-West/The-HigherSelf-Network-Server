'use strict';

/**
 * Webhook routes configuration
 * Defines secured endpoints for receiving webhooks from external systems
 */

module.exports = {
  routes: [
    {
      // Route for receiving Notion webhooks
      method: 'POST',
      path: '/webhooks/notion',
      handler: 'webhook.handleWebhook',
      config: {
        middlewares: ['api::webhook.webhook-auth'],
        auth: false,
        // Tag this route for Swagger documentation
        tags: ['Webhook'],
        description: 'Handle incoming webhooks from Notion'
      }
    },
    {
      // Route for receiving API Gateway webhooks
      method: 'POST',
      path: '/webhooks/api-gateway',
      handler: 'webhook.handleWebhook',
      config: {
        middlewares: ['api::webhook.webhook-auth'],
        auth: false,
        tags: ['Webhook'],
        description: 'Handle incoming webhooks from API Gateway'
      }
    },
    {
      // Route for receiving Softr webhooks
      method: 'POST',
      path: '/webhooks/softr',
      handler: 'webhook.handleWebhook',
      config: {
        middlewares: ['api::webhook.webhook-auth'],
        auth: false,
        tags: ['Webhook'],
        description: 'Handle incoming webhooks from Softr interfaces'
      }
    }
  ]
};
