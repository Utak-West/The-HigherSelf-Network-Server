'use strict';

/**
 * Exhibit content type lifecycle hooks
 * Enforces State Machine Compliance rule for Gallery Exhibit Management workflow
 */

module.exports = {
  beforeCreate(event) {
    validateStateTransition(null, event.params.data);
  },

  beforeUpdate(event) {
    validateStateTransition(event.params.where.id, event.params.data);
  },

  afterCreate(event) {
    const { result } = event;
    notifyAgentsOfStateChange(result);
    syncToNotion(result);
  },

  afterUpdate(event) {
    const { result } = event;
    notifyAgentsOfStateChange(result);
    syncToNotion(result);
  }
};

/**
 * Validates that the state transition follows allowed paths
 * @param {string|null} id Entity ID if updating
 * @param {Object} data Updated data
 */
async function validateStateTransition(id, data) {
  // Skip validation if state isn't changing
  if (!data.exhibitStatus) {
    return;
  }

  try {
    const strapi = require('@strapi/strapi').factories.createStrapi();

    // For new exhibits, only 'concept' state is allowed
    if (!id) {
      if (data.exhibitStatus !== 'concept') {
        throw new Error('New exhibits must start in concept state');
      }
      return;
    }

    // Get current exhibit
    const exhibit = await strapi.entityService.findOne('api::exhibit.exhibit', id, {});
    if (!exhibit) {
      throw new Error('Exhibit not found');
    }

    // Get valid transitions for current state
    const validTransitions = await getValidTransitions('Gallery_Exhibit', exhibit.exhibitStatus);

    // Check if transition is allowed
    if (!validTransitions.includes(data.exhibitStatus)) {
      throw new Error(`Invalid state transition from ${exhibit.exhibitStatus} to ${data.exhibitStatus}. Allowed transitions: ${validTransitions.join(', ')}`);
    }

    // Add audit trail for state transition
    await strapi.entityService.create('api::state-transition-log.state-transition-log', {
      data: {
        entityType: 'exhibit',
        entityId: id,
        fromState: exhibit.exhibitStatus,
        toState: data.exhibitStatus,
        transitionTime: new Date(),
        user: strapi.requestContext.get().state?.user?.id || 'system'
      }
    });
  } catch (error) {
    strapi.log.error('State transition validation error:', error);
    throw error;
  }
}

/**
 * Get valid state transitions for the given workflow and current state
 * @param {string} workflowType Workflow type
 * @param {string} currentState Current state
 * @returns {string[]} Array of valid next states
 */
async function getValidTransitions(workflowType, currentState) {
  try {
    const strapi = require('@strapi/strapi').factories.createStrapi();

    // Get current state from workflow states
    const stateRecord = await strapi.db.query('api::workflow-state.workflow-state').findOne({
      where: {
        workflowType,
        stateKey: currentState
      }
    });

    if (!stateRecord) {
      throw new Error(`State ${currentState} not found in workflow ${workflowType}`);
    }

    // Get transitions from this state
    const transitions = await strapi.db.query('api::workflow-transition.workflow-transition').findMany({
      where: {
        fromState: stateRecord.id
      },
      populate: ['toState']
    });

    // Return array of valid next state keys
    return transitions.map(transition => transition.toState.stateKey);
  } catch (error) {
    strapi.log.error('Error getting valid transitions:', error);
    // Default valid transitions for Gallery Exhibit workflow if DB lookup fails
    const fallbackTransitions = {
      concept: ['artist_selection'],
      artist_selection: ['planning'],
      planning: ['artwork_collection'],
      artwork_collection: ['curation'],
      curation: ['promotion'],
      promotion: ['installation'],
      installation: ['active'],
      active: ['closing'],
      closing: ['post_analysis'],
      post_analysis: ['archived']
    };

    return fallbackTransitions[currentState] || [];
  }
}

/**
 * Notify agents when exhibit state changes
 * @param {Object} exhibit Updated exhibit data
 */
async function notifyAgentsOfStateChange(exhibit) {
  try {
    const strapi = require('@strapi/strapi').factories.createStrapi();

    // Map exhibit states to responsible agents based on the workflow definition
    const responsibleAgents = {
      concept: ['design_agent'],
      artist_selection: ['community_engagement_agent'],
      planning: ['task_management_agent'],
      artwork_collection: ['community_engagement_agent'],
      curation: ['design_agent'],
      promotion: ['marketing_campaign_agent', 'content_lifecycle_agent'],
      installation: ['task_management_agent'],
      active: ['community_engagement_agent'],
      closing: ['task_management_agent'],
      post_analysis: ['marketing_campaign_agent']
    };

    const agents = responsibleAgents[exhibit.exhibitStatus] || [];

    // Notify each responsible agent
    for (const agentKey of agents) {
      await strapi.service('api::api-gateway.api-gateway').notifyGateway('exhibit_state_change', {
        exhibitId: exhibit.id,
        exhibitTitle: exhibit.title,
        newState: exhibit.exhibitStatus,
        targetAgent: agentKey
      });
    }
  } catch (error) {
    strapi.log.error('Error notifying agents:', error);
  }
}

/**
 * Sync exhibit data to Notion
 * @param {Object} exhibit Exhibit data
 */
async function syncToNotion(exhibit) {
  try {
    const strapi = require('@strapi/strapi').factories.createStrapi();
    await strapi.service('api::notion-sync.notion-sync').syncToNotion('EXHIBITS', exhibit, exhibit.notionSyncId);
  } catch (error) {
    strapi.log.error('Error syncing to Notion:', error);
  }
}
