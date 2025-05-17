'use strict';

/**
 * Strapi CMS integration service for Higher Self Network API Gateway
 * This service handles communication with the Strapi headless CMS
 * following the server rules for Integration Security.
 */

const axios = require('axios');
const crypto = require('crypto');
const logger = require('../../utils/logger');

class StrapiService {
  constructor(config) {
    this.config = config;
    this.baseUrl = config.strapiUrl || process.env.STRAPI_API_URL || 'http://localhost:1337/api';
    this.apiKey = config.strapiApiKey || process.env.STRAPI_API_KEY;
    this.webhookSecret = config.strapiWebhookSecret || process.env.STRAPI_WEBHOOK_SECRET;
  }

  /**
   * Initialize the service and verify connectivity
   */
  async initialize() {
    try {
      const response = await this.get('/healthcheck');
      logger.info('Strapi CMS connection established', { status: response.status });
      return true;
    } catch (error) {
      logger.error('Failed to connect to Strapi CMS', { error: error.message });
      return false;
    }
  }

  /**
   * Perform GET request to Strapi API
   * @param {string} endpoint API endpoint
   * @param {Object} params Query parameters
   * @returns {Promise<Object>} API response
   */
  async get(endpoint, params = {}) {
    try {
      const url = `${this.baseUrl}${endpoint}`;
      const response = await axios.get(url, {
        params,
        headers: this.getAuthHeaders()
      });
      return response.data;
    } catch (error) {
      this.handleApiError(error, 'GET', endpoint);
      throw error;
    }
  }

  /**
   * Perform POST request to Strapi API
   * @param {string} endpoint API endpoint
   * @param {Object} data Request payload
   * @returns {Promise<Object>} API response
   */
  async post(endpoint, data = {}) {
    try {
      const url = `${this.baseUrl}${endpoint}`;
      const response = await axios.post(url, data, {
        headers: this.getAuthHeaders()
      });
      return response.data;
    } catch (error) {
      this.handleApiError(error, 'POST', endpoint);
      throw error;
    }
  }

  /**
   * Perform PUT request to Strapi API
   * @param {string} endpoint API endpoint
   * @param {Object} data Request payload
   * @returns {Promise<Object>} API response
   */
  async put(endpoint, data = {}) {
    try {
      const url = `${this.baseUrl}${endpoint}`;
      const response = await axios.put(url, data, {
        headers: this.getAuthHeaders()
      });
      return response.data;
    } catch (error) {
      this.handleApiError(error, 'PUT', endpoint);
      throw error;
    }
  }

  /**
   * Perform DELETE request to Strapi API
   * @param {string} endpoint API endpoint
   * @returns {Promise<Object>} API response
   */
  async delete(endpoint) {
    try {
      const url = `${this.baseUrl}${endpoint}`;
      const response = await axios.delete(url, {
        headers: this.getAuthHeaders()
      });
      return response.data;
    } catch (error) {
      this.handleApiError(error, 'DELETE', endpoint);
      throw error;
    }
  }

  /**
   * Send webhook event to Strapi
   * @param {string} source Event source
   * @param {string} eventType Event type
   * @param {Object} payload Event payload
   * @returns {Promise<Object>} Webhook response
   */
  async sendWebhook(source, eventType, payload) {
    try {
      const webhookData = {
        source,
        event_type: eventType,
        timestamp: new Date().toISOString(),
        payload
      };

      const webhookUrl = `${this.baseUrl.replace('/api', '')}/webhooks/${source.replace('_', '-')}`;
      const webhookBody = JSON.stringify(webhookData);
      const signature = this.generateWebhookSignature(webhookBody);

      const response = await axios.post(webhookUrl, webhookData, {
        headers: {
          'Content-Type': 'application/json',
          'X-Webhook-Signature': signature
        }
      });

      logger.info('Webhook sent to Strapi CMS', {
        source,
        eventType,
        status: response.status
      });

      return response.data;
    } catch (error) {
      logger.error('Failed to send webhook to Strapi CMS', {
        source,
        eventType,
        error: error.message
      });
      throw error;
    }
  }

  /**
   * Generate authentication headers for API requests
   * @returns {Object} Headers with authentication
   */
  getAuthHeaders() {
    return {
      'Authorization': `Bearer ${this.apiKey}`,
      'Content-Type': 'application/json'
    };
  }

  /**
   * Generate webhook signature for secure communication
   * @param {string} body Webhook body as string
   * @returns {string} HMAC signature
   */
  generateWebhookSignature(body) {
    const hmac = crypto.createHmac('sha256', this.webhookSecret);
    hmac.update(body);
    return hmac.digest('hex');
  }

  /**
   * Handle API errors with proper logging
   * @param {Error} error API error
   * @param {string} method HTTP method
   * @param {string} endpoint API endpoint
   */
  handleApiError(error, method, endpoint) {
    const status = error.response?.status || 0;
    const message = error.response?.data?.error?.message || error.message;

    logger.error('Strapi API error', {
      method,
      endpoint,
      status,
      message
    });
  }

  /**
   * Get exhibits from Strapi CMS
   * @param {Object} params Query parameters
   * @returns {Promise<Array>} List of exhibits
   */
  async getExhibits(params = {}) {
    return this.get('/exhibits', params);
  }

  /**
   * Get a specific exhibit by ID
   * @param {string} id Exhibit ID
   * @returns {Promise<Object>} Exhibit data
   */
  async getExhibit(id) {
    return this.get(`/exhibits/${id}`);
  }

  /**
   * Create a new exhibit
   * @param {Object} exhibitData Exhibit data
   * @returns {Promise<Object>} Created exhibit
   */
  async createExhibit(exhibitData) {
    return this.post('/exhibits', { data: exhibitData });
  }

  /**
   * Update an exhibit
   * @param {string} id Exhibit ID
   * @param {Object} exhibitData Updated exhibit data
   * @returns {Promise<Object>} Updated exhibit
   */
  async updateExhibit(id, exhibitData) {
    return this.put(`/exhibits/${id}`, { data: exhibitData });
  }

  /**
   * Get wellness services from Strapi CMS
   * @param {Object} params Query parameters
   * @returns {Promise<Array>} List of wellness services
   */
  async getWellnessServices(params = {}) {
    return this.get('/wellness-services', params);
  }

  /**
   * Get available bookings for a wellness service
   * @param {string} serviceId Service ID
   * @param {Object} params Query parameters (date range, etc.)
   * @returns {Promise<Array>} Available booking slots
   */
  async getAvailableBookings(serviceId, params = {}) {
    return this.get(`/wellness-services/${serviceId}/available-slots`, params);
  }

  /**
   * Create a new booking
   * @param {Object} bookingData Booking data
   * @returns {Promise<Object>} Created booking
   */
  async createBooking(bookingData) {
    return this.post('/bookings', { data: bookingData });
  }

  /**
   * Update workflow state for an entity
   * @param {string} entityType Entity type (exhibit, booking, etc.)
   * @param {string} entityId Entity ID
   * @param {string} newState New workflow state
   * @param {string} triggerEvent Event triggering the state change
   * @returns {Promise<Object>} Updated entity
   */
  async updateWorkflowState(entityType, entityId, newState, triggerEvent) {
    const endpoint = `/${entityType.replace('_', '-')}s/${entityId}/state`;
    return this.put(endpoint, {
      data: {
        newState,
        triggerEvent,
        updatedBy: 'api_gateway'
      }
    });
  }

  /**
   * Get active workflow states for an entity type
   * @param {string} workflowType Workflow type (Gallery_Exhibit, Wellness_Booking, etc.)
   * @returns {Promise<Array>} List of workflow states
   */
  async getWorkflowStates(workflowType) {
    return this.get('/workflow-states', {
      filters: {
        workflowType: {
          $eq: workflowType
        }
      }
    });
  }

  /**
   * Get valid transitions from a state
   * @param {string} workflowType Workflow type
   * @param {string} currentState Current state key
   * @returns {Promise<Array>} List of valid transitions
   */
  async getValidTransitions(workflowType, currentState) {
    return this.get('/workflow-transitions', {
      filters: {
        fromState: {
          stateKey: {
            $eq: currentState
          },
          workflowType: {
            $eq: workflowType
          }
        }
      },
      populate: ['toState']
    });
  }
}

module.exports = StrapiService;
