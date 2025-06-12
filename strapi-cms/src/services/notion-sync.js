'use strict';

/**
 * Notion synchronization service for Higher Self Network
 * Maintains schema consistency and real-time sync protection
 * according to the server rules
 */

const { Client } = require('@notionhq/client');

module.exports = ({ strapi }) => ({
  /**
   * Initialize the Notion client with API key from environment
   * @returns {Object} Notion client instance
   */
  getNotionClient() {
    const apiKey = process.env.NOTION_API_KEY;
    if (!apiKey) {
      strapi.log.error('Notion API key is missing in environment variables');
      throw new Error('Notion API key is required for synchronization');
    }

    return new Client({ auth: apiKey });
  },

  /**
   * Sync Strapi content to Notion with optimistic locking
   *
   * @param {string} entityType Type of entity being synced (exhibit, artist, wellness, etc.)
   * @param {Object} data Entity data to sync
   * @param {string|null} notionPageId Existing Notion page ID if updating
   * @returns {Object} Sync result with Notion page ID
   */
  async syncToNotion(entityType, data, notionPageId = null) {
    try {
      const notion = this.getNotionClient();
      const databaseId = this.getNotionDatabaseId(entityType);

      // Implement optimistic locking for real-time sync protection
      const lockKey = `notion:lock:${entityType}:${notionPageId || 'new'}`;
      const lockAcquired = await this.acquireLock(lockKey);

      if (!lockAcquired) {
        throw new Error('Another synchronization is in progress. Please try again.');
      }

      try {
        // Prepare data according to Notion schema
        const notionProperties = this.mapToNotionProperties(entityType, data);

        let response;

        if (notionPageId) {
          // Update existing page
          response = await notion.pages.update({
            page_id: notionPageId,
            properties: notionProperties
          });
        } else {
          // Create new page
          response = await notion.pages.create({
            parent: { database_id: databaseId },
            properties: notionProperties
          });
        }

        // Audit trail for database operations
        await this.logSyncOperation(entityType, data.id, response.id, notionPageId ? 'update' : 'create');

        return {
          success: true,
          notionPageId: response.id
        };
      } finally {
        // Release lock regardless of outcome
        await this.releaseLock(lockKey);
      }
    } catch (error) {
      strapi.log.error('Notion sync error:', error);
      return {
        success: false,
        error: error.message
      };
    }
  },

  /**
   * Get database ID for specified entity type
   * @param {string} entityType Type of entity
   * @returns {string} Notion database ID
   */
  getNotionDatabaseId(entityType) {
    const envKey = `NOTION_DATABASE_ID_${entityType.toUpperCase()}`;
    const databaseId = process.env[envKey];

    if (!databaseId) {
      throw new Error(`Notion database ID for ${entityType} is missing in environment variables`);
    }

    return databaseId;
  },

  /**
   * Map Strapi data to Notion properties based on entity type
   * @param {string} entityType Type of entity
   * @param {Object} data Strapi data
   * @returns {Object} Notion properties
   */
  mapToNotionProperties(entityType, data) {
    // Implementation would map Strapi fields to Notion properties
    // based on the 16-database schema design
    const properties = {};

    // Map common properties
    if (data.title) {
      properties['Name'] = {
        title: [{ text: { content: data.title } }]
      };
    } else if (data.name) {
      properties['Name'] = {
        title: [{ text: { content: data.name } }]
      };
    }

    if (data.status) {
      properties['Status'] = {
        select: { name: data.status }
      };
    }

    // Entity-specific mappings would be implemented here
    // based on the schema for each entity type

    return properties;
  },

  /**
   * Acquire a distributed lock for sync operations
   * @param {string} lockKey Lock identifier
   * @returns {boolean} Whether lock was acquired
   */
  async acquireLock(lockKey) {
    try {
      // In a production implementation, this would use Redis or another
      // distributed locking mechanism. For this example, we'll simulate it.
      const lockValue = Date.now().toString();
      // Placeholder for actual distributed lock implementation
      return true;
    } catch (error) {
      strapi.log.error('Lock acquisition error:', error);
      return false;
    }
  },

  /**
   * Release a distributed lock
   * @param {string} lockKey Lock identifier
   */
  async releaseLock(lockKey) {
    try {
      // Placeholder for actual lock release implementation
      return true;
    } catch (error) {
      strapi.log.error('Lock release error:', error);
    }
  },

  /**
   * Log sync operation for audit trail
   * @param {string} entityType Entity type
   * @param {string} strapiId Strapi entity ID
   * @param {string} notionId Notion page ID
   * @param {string} operation Operation type (create, update, delete)
   */
  async logSyncOperation(entityType, strapiId, notionId, operation) {
    try {
      await strapi.entityService.create('api::sync-log.sync-log', {
        data: {
          entityType,
          strapiId,
          notionId,
          operation,
          timestamp: new Date(),
          user: strapi.requestContext.get().state?.user?.id || 'system'
        }
      });
    } catch (error) {
      strapi.log.error('Error logging sync operation:', error);
    }
  }
});
