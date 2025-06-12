/**
 * Notion API Service
 * Handles all interactions with Notion databases and follows the Notion Database Integrity Rules
 */
const { Client } = require('@notionhq/client');
const { NotionDatabaseError } = require('../utils/errors');

// Initialize Notion client
const notion = new Client({
  auth: process.env.NOTION_API_KEY,
});

/**
 * Query a Notion database with optional filters
 * @param {string} databaseId - Notion database ID
 * @param {object} filter - Optional Notion filter object
 * @param {object} sorts - Optional sort parameters
 * @returns {Promise<Array>} - Query results
 */
async function queryDatabase(databaseId, filter = {}, sorts = []) {
  try {
    // Build the query parameters
    const queryParams = {
      database_id: databaseId,
    };

    // Add filter if provided
    if (Object.keys(filter).length > 0) {
      queryParams.filter = filter;
    }

    // Add sorts if provided
    if (sorts.length > 0) {
      queryParams.sorts = sorts;
    }

    // Execute the query with rate limit awareness
    const response = await notion.databases.query(queryParams);

    // Return the results
    return response.results;
  } catch (error) {
    // Transform error for better diagnostics
    throw new NotionDatabaseError(`Error querying Notion database: ${error.message}`, error);
  }
}

/**
 * Retrieve a single page from Notion
 * @param {string} pageId - Notion page ID
 * @returns {Promise<Object>} - Page data
 */
async function getPage(pageId) {
  try {
    const response = await notion.pages.retrieve({ page_id: pageId });
    return response;
  } catch (error) {
    throw new NotionDatabaseError(`Error retrieving Notion page: ${error.message}`, error);
  }
}

/**
 * Create a new page in a Notion database
 * @param {string} databaseId - Parent database ID
 * @param {object} properties - Page properties according to database schema
 * @returns {Promise<Object>} - Created page data
 */
async function createPage(databaseId, properties) {
  try {
    const response = await notion.pages.create({
      parent: { database_id: databaseId },
      properties
    });
    return response;
  } catch (error) {
    throw new NotionDatabaseError(`Error creating Notion page: ${error.message}`, error);
  }
}

/**
 * Update an existing page in Notion
 * @param {string} pageId - Notion page ID
 * @param {object} properties - Page properties to update
 * @returns {Promise<Object>} - Updated page data
 */
async function updatePage(pageId, properties) {
  try {
    const response = await notion.pages.update({
      page_id: pageId,
      properties
    });
    return response;
  } catch (error) {
    throw new NotionDatabaseError(`Error updating Notion page: ${error.message}`, error);
  }
}

/**
 * Archive (soft delete) a page in Notion
 * @param {string} pageId - Notion page ID
 * @returns {Promise<Object>} - Operation result
 */
async function archivePage(pageId) {
  try {
    const response = await notion.pages.update({
      page_id: pageId,
      archived: true
    });
    return response;
  } catch (error) {
    throw new NotionDatabaseError(`Error archiving Notion page: ${error.message}`, error);
  }
}

module.exports = {
  queryDatabase,
  getPage,
  createPage,
  updatePage,
  archivePage
};
