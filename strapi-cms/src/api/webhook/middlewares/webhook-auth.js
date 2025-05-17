'use strict';

const crypto = require('crypto');

/**
 * Webhook authentication middleware
 * Implements webhook authentication as required by Integration Security Rules
 */

module.exports = (config, { strapi }) => {
  return async (ctx, next) => {
    const { headers, body, method, url } = ctx.request;
    
    if (method !== 'POST') {
      return next();
    }
    
    try {
      // Extract source from URL for source-specific validation
      const urlParts = url.split('/');
      const source = urlParts[urlParts.length - 1];
      
      // Apply rate limiting for webhook endpoints
      await applyRateLimit(ctx, source);
      
      // Get the appropriate secret based on the source
      const secret = getWebhookSecret(source);
      
      // Validate the webhook signature
      validateSignature(headers, JSON.stringify(body), secret);
      
      // Add source information to the request for controller use
      ctx.request.body.source = source;
      
      // Log webhook attempt for audit trail
      await logWebhookAttempt(source, 'authentication_success', null);
      
      return next();
    } catch (error) {
      // Log failed authentication attempt
      await logWebhookAttempt(
        url.split('/').pop(),
        'authentication_failure',
        error.message
      );
      
      return ctx.unauthorized(`Webhook authentication failed: ${error.message}`);
    }
  };
};

/**
 * Apply rate limiting for webhook endpoints
 * @param {Object} ctx Request context
 * @param {string} source Webhook source
 */
async function applyRateLimit(ctx, source) {
  const windowMs = parseInt(process.env.RATE_LIMIT_WINDOW_MS || '60000', 10);
  const maxRequests = parseInt(process.env.RATE_LIMIT_MAX || '100', 10);
  
  // In a real implementation, this would use Redis or another store
  // to track and limit webhook requests by source
  
  // For demonstration, we'll implement a simple check
  const ip = ctx.request.ip;
  const key = `rate-limit:webhook:${source}:${ip}`;
  
  // This is a placeholder - in production you would implement
  // proper rate limiting with Redis or a similar solution
  
  // For now we'll allow all requests to proceed
  return true;
}

/**
 * Get the webhook secret based on source
 * @param {string} source Webhook source
 * @returns {string} Webhook secret
 */
function getWebhookSecret(source) {
  // In production, you would have different secrets for different sources
  // Use environment variables for security as per Integration Security Rules
  
  const secretMappings = {
    notion: process.env.NOTION_WEBHOOK_SECRET,
    'api-gateway': process.env.API_GATEWAY_WEBHOOK_SECRET,
    softr: process.env.SOFTR_WEBHOOK_SECRET
  };
  
  // Default to generic webhook secret if source-specific one isn't available
  return secretMappings[source] || process.env.WEBHOOK_SECRET;
}

/**
 * Validate the webhook signature
 * @param {Object} headers Request headers
 * @param {string} body Request body as string
 * @param {string} secret Webhook secret
 */
function validateSignature(headers, body, secret) {
  const signature = headers['x-webhook-signature'];
  
  if (!signature) {
    throw new Error('Missing webhook signature');
  }
  
  if (!secret) {
    throw new Error('Webhook secret not configured');
  }
  
  const hmac = crypto.createHmac('sha256', secret);
  hmac.update(body);
  const calculatedSignature = hmac.digest('hex');
  
  if (signature !== calculatedSignature) {
    throw new Error('Invalid webhook signature');
  }
}

/**
 * Log webhook authentication attempt for audit trail
 * @param {string} source Webhook source
 * @param {string} status Authentication status
 * @param {string|null} errorMessage Error message if any
 */
async function logWebhookAttempt(source, status, errorMessage) {
  try {
    const strapi = require('@strapi/strapi').factories.createStrapi();
    
    await strapi.entityService.create('api::webhook-auth-log.webhook-auth-log', {
      data: {
        source,
        status,
        errorMessage,
        timestamp: new Date(),
        ipAddress: strapi.requestContext.get().request.ip
      }
    });
  } catch (error) {
    console.error('Error logging webhook authentication:', error);
  }
}
