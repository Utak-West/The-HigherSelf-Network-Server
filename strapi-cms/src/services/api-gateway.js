'use strict';

/**
 * API Gateway integration service for Higher Self Network
 * Ensures secure communication between Strapi and API Gateway
 * following the Integration Security Rules
 */

const axios = require('axios');

module.exports = ({ strapi }) => ({
  /**
   * Send event notification to API Gateway
   *
   * @param {string} eventType Type of event (state_change, data_update, etc.)
   * @param {Object} payload Event data
   * @returns {Object} API Gateway response
   */
  async notifyGateway(eventType, payload) {
    try {
      const apiGatewayUrl = process.env.API_GATEWAY_URL;
      const apiGatewayKey = process.env.API_GATEWAY_KEY;

      if (!apiGatewayUrl || !apiGatewayKey) {
        throw new Error('API Gateway configuration missing in environment variables');
      }

      // Prepare the event notification
      const eventData = {
        event_type: eventType,
        source: 'strapi_cms',
        timestamp: new Date().toISOString(),
        payload
      };

      // Implement rate limiting for API Gateway calls
      await this.checkRateLimit('api_gateway_notification');

      // Send to API Gateway with proper authentication
      const response = await axios.post(
        `${apiGatewayUrl}/events`,
        eventData,
        {
          headers: {
            'Authorization': `Bearer ${apiGatewayKey}`,
            'Content-Type': 'application/json'
          }
        }
      );

      // Log the API call for audit purposes
      await this.logApiCall(eventType, response.status);

      return {
        success: true,
        status: response.status,
        data: response.data
      };
    } catch (error) {
      strapi.log.error('API Gateway notification error:', error);

      // Implement graceful degradation
      await this.storeFailedNotification(eventType, payload, error.message);

      return {
        success: false,
        error: error.message
      };
    }
  },

  /**
   * Check rate limit before making API calls
   * @param {string} operationType Type of operation
   */
  async checkRateLimit(operationType) {
    const windowMs = parseInt(process.env.RATE_LIMIT_WINDOW_MS || '60000', 10);
    const maxRequests = parseInt(process.env.RATE_LIMIT_MAX || '100', 10);

    // Here you would implement actual rate limiting logic
    // In a real implementation, this would use Redis or another store
    // to track request counts within the time window

    // For now, we'll just simulate it
    return true;
  },

  /**
   * Log API call for audit purposes
   * @param {string} eventType Event type
   * @param {number} statusCode Response status code
   */
  async logApiCall(eventType, statusCode) {
    try {
      await strapi.entityService.create('api::api-log.api-log', {
        data: {
          eventType,
          statusCode,
          timestamp: new Date(),
          source: 'strapi_cms'
        }
      });
    } catch (error) {
      strapi.log.error('Error logging API call:', error);
    }
  },

  /**
   * Store failed notification for retry
   * @param {string} eventType Event type
   * @param {Object} payload Event payload
   * @param {string} errorMessage Error message
   */
  async storeFailedNotification(eventType, payload, errorMessage) {
    try {
      await strapi.entityService.create('api::failed-notification.failed-notification', {
        data: {
          eventType,
          payload: JSON.stringify(payload),
          errorMessage,
          timestamp: new Date(),
          retryCount: 0,
          status: 'pending'
        }
      });
    } catch (error) {
      strapi.log.error('Error storing failed notification:', error);
    }
  }
});
