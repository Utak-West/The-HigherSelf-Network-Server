/**
 * Gallery Controller
 * Implements the Gallery Exhibit Management Workflow
 * Maps to the workflow defined in OPERATIONAL_WORKFLOWS.md
 */
const notionService = require('../services/notionService');
const {
  exhibitStates,
  isValidStateTransition,
  createExhibitSchema,
  updateExhibitSchema,
  stateTransitionSchema
} = require('../models/galleryExhibit');
const {
  BadRequestError,
  NotFoundError,
  WorkflowStateError
} = require('../utils/errors');

// Mapping of exhibit state to Notion database property values
const stateToNotionProperty = {
  [exhibitStates.PROPOSED]: { name: 'Status', select: { name: 'Proposed' } },
  [exhibitStates.REVIEWED]: { name: 'Status', select: { name: 'Reviewed' } },
  [exhibitStates.SCHEDULED]: { name: 'Status', select: { name: 'Scheduled' } },
  [exhibitStates.INSTALLED]: { name: 'Status', select: { name: 'Installed' } },
  [exhibitStates.ACTIVE]: { name: 'Status', select: { name: 'Active' } },
  [exhibitStates.ARCHIVED]: { name: 'Status', select: { name: 'Archived' } }
};

/**
 * Transform Notion data to API response format
 * @param {Object} notionPage - Notion page data
 * @returns {Object} - Formatted exhibit data
 */
function transformNotionToExhibit(notionPage) {
  if (!notionPage || !notionPage.properties) {
    return null;
  }

  const props = notionPage.properties;

  return {
    id: notionPage.id,
    title: props.Title?.title?.[0]?.plain_text || '',
    artist: props.Artist?.rich_text?.[0]?.plain_text || '',
    description: props.Description?.rich_text?.[0]?.plain_text || '',
    mediums: props.Mediums?.multi_select?.map(item => item.name) || [],
    dimensions: props.Dimensions?.rich_text?.[0]?.plain_text || '',
    price: props.Price?.number || 0,
    images: props.Images?.files?.map(file => file.external?.url || file.file?.url) || [],
    proposedStartDate: props['Start Date']?.date?.start || null,
    proposedEndDate: props['End Date']?.date?.start || null,
    featuredPiece: props['Featured']?.checkbox || false,
    state: props.Status?.select?.name?.toLowerCase() || exhibitStates.PROPOSED,
    contactInformation: {
      email: props['Contact Email']?.email || '',
      phone: props['Contact Phone']?.phone_number || '',
      website: props['Contact Website']?.url || ''
    },
    createdTime: notionPage.created_time,
    lastEditedTime: notionPage.last_edited_time
  };
}

/**
 * Transform API data to Notion format for create/update operations
 * @param {Object} exhibitData - Raw exhibit data
 * @returns {Object} - Notion formatted properties
 */
function transformExhibitToNotion(exhibitData) {
  const properties = {};

  if (exhibitData.title) {
    properties.Title = { title: [{ text: { content: exhibitData.title } }] };
  }

  if (exhibitData.artist) {
    properties.Artist = { rich_text: [{ text: { content: exhibitData.artist } }] };
  }

  if (exhibitData.description) {
    properties.Description = { rich_text: [{ text: { content: exhibitData.description } }] };
  }

  if (exhibitData.mediums && Array.isArray(exhibitData.mediums)) {
    properties.Mediums = { multi_select: exhibitData.mediums.map(medium => ({ name: medium })) };
  }

  if (exhibitData.dimensions) {
    properties.Dimensions = { rich_text: [{ text: { content: exhibitData.dimensions } }] };
  }

  if (exhibitData.price !== undefined) {
    properties.Price = { number: parseFloat(exhibitData.price) };
  }

  if (exhibitData.images && Array.isArray(exhibitData.images)) {
    properties.Images = {
      files: exhibitData.images.map(url => ({
        type: 'external',
        name: url.split('/').pop(),
        external: { url }
      }))
    };
  }

  if (exhibitData.proposedStartDate) {
    properties['Start Date'] = { date: { start: exhibitData.proposedStartDate } };
  }

  if (exhibitData.proposedEndDate) {
    properties['End Date'] = { date: { start: exhibitData.proposedEndDate } };
  }

  if (exhibitData.featuredPiece !== undefined) {
    properties.Featured = { checkbox: !!exhibitData.featuredPiece };
  }

  if (exhibitData.state) {
    properties.Status = { select: { name: exhibitData.state.charAt(0).toUpperCase() + exhibitData.state.slice(1) } };
  }

  if (exhibitData.contactInformation) {
    if (exhibitData.contactInformation.email) {
      properties['Contact Email'] = { email: exhibitData.contactInformation.email };
    }

    if (exhibitData.contactInformation.phone) {
      properties['Contact Phone'] = { phone_number: exhibitData.contactInformation.phone };
    }

    if (exhibitData.contactInformation.website) {
      properties['Contact Website'] = { url: exhibitData.contactInformation.website };
    }
  }

  return properties;
}

// Gallery controller methods
const galleryController = {
  /**
   * Get all exhibits with optional filters
   */
  async getAllExhibits(req, res, next) {
    try {
      // Get query parameters for filtering
      const { state, artist, featured } = req.query;

      // Build filter
      let filter = {};

      if (state) {
        filter.and = filter.and || [];
        filter.and.push({
          property: 'Status',
          select: {
            equals: state.charAt(0).toUpperCase() + state.slice(1)
          }
        });
      }

      if (artist) {
        filter.and = filter.and || [];
        filter.and.push({
          property: 'Artist',
          rich_text: {
            contains: artist
          }
        });
      }

      if (featured === 'true') {
        filter.and = filter.and || [];
        filter.and.push({
          property: 'Featured',
          checkbox: {
            equals: true
          }
        });
      }

      // Sort by creation date, newest first
      const sorts = [
        {
          property: 'created_time',
          direction: 'descending'
        }
      ];

      // Query Notion database
      const results = await notionService.queryDatabase(
        process.env.NOTION_GALLERY_DB,
        filter,
        sorts
      );

      // Transform results
      const exhibits = results.map(transformNotionToExhibit).filter(Boolean);

      res.json({ exhibits });
    } catch (error) {
      next(error);
    }
  },

  /**
   * Get a single exhibit by ID
   */
  async getExhibitById(req, res, next) {
    try {
      const { id } = req.params;

      // Get the exhibit from Notion
      const exhibit = await notionService.getPage(id);

      if (!exhibit) {
        throw new NotFoundError(`Exhibit with ID ${id} not found`);
      }

      // Transform the result
      const formattedExhibit = transformNotionToExhibit(exhibit);

      res.json({ exhibit: formattedExhibit });
    } catch (error) {
      next(error);
    }
  },

  /**
   * Create a new exhibit (proposed state)
   */
  async createExhibit(req, res, next) {
    try {
      // Validate input
      const { error, value } = createExhibitSchema.validate(req.body);

      if (error) {
        throw new BadRequestError(`Invalid exhibit data: ${error.message}`);
      }

      // All new exhibits start in proposed state
      const exhibitData = {
        ...value,
        state: exhibitStates.PROPOSED
      };

      // Transform to Notion format
      const properties = transformExhibitToNotion(exhibitData);

      // Create in Notion database
      const createdExhibit = await notionService.createPage(
        process.env.NOTION_GALLERY_DB,
        properties
      );

      // Return the created exhibit
      const formattedExhibit = transformNotionToExhibit(createdExhibit);

      res.status(201).json({
        message: 'Exhibit created successfully',
        exhibit: formattedExhibit
      });
    } catch (error) {
      next(error);
    }
  },

  /**
   * Update an existing exhibit
   */
  async updateExhibit(req, res, next) {
    try {
      const { id } = req.params;

      // Validate input
      const { error, value } = updateExhibitSchema.validate(req.body);

      if (error) {
        throw new BadRequestError(`Invalid exhibit data: ${error.message}`);
      }

      // Get current exhibit to check state transition if needed
      let currentExhibit;
      try {
        const exhibit = await notionService.getPage(id);
        currentExhibit = transformNotionToExhibit(exhibit);
      } catch (error) {
        throw new NotFoundError(`Exhibit with ID ${id} not found`);
      }

      // Check state transition if requested
      if (value.state && value.state !== currentExhibit.state) {
        if (!isValidStateTransition(currentExhibit.state, value.state)) {
          throw new WorkflowStateError(
            `Invalid state transition from ${currentExhibit.state} to ${value.state}`
          );
        }
      }

      // Transform to Notion format
      const properties = transformExhibitToNotion(value);

      // Update in Notion
      const updatedExhibit = await notionService.updatePage(id, properties);

      // Return the updated exhibit
      const formattedExhibit = transformNotionToExhibit(updatedExhibit);

      res.json({
        message: 'Exhibit updated successfully',
        exhibit: formattedExhibit
      });
    } catch (error) {
      next(error);
    }
  },

  /**
   * Execute a state transition in the workflow
   */
  async transitionExhibitState(req, res, next) {
    try {
      const { id } = req.params;

      // Validate input
      const { error, value } = stateTransitionSchema.validate(req.body);

      if (error) {
        throw new BadRequestError(`Invalid transition data: ${error.message}`);
      }

      // Check if the transition is valid
      const { currentState, newState, notes } = value;

      if (!isValidStateTransition(currentState, newState)) {
        throw new WorkflowStateError(
          `Invalid state transition from ${currentState} to ${newState}`
        );
      }

      // Get the current exhibit to verify the current state
      let currentExhibit;
      try {
        const exhibit = await notionService.getPage(id);
        currentExhibit = transformNotionToExhibit(exhibit);
      } catch (error) {
        throw new NotFoundError(`Exhibit with ID ${id} not found`);
      }

      // Verify that the current state matches
      if (currentExhibit.state !== currentState) {
        throw new WorkflowStateError(
          `Current state ${currentExhibit.state} does not match expected state ${currentState}`
        );
      }

      // Prepare the properties update
      const properties = {
        Status: { select: { name: newState.charAt(0).toUpperCase() + newState.slice(1) } }
      };

      // Add notes if provided
      if (notes) {
        properties.Notes = {
          rich_text: [{ text: { content: notes } }]
        };
      }

      // Update the exhibit state
      const updatedExhibit = await notionService.updatePage(id, properties);

      // Return the updated exhibit
      const formattedExhibit = transformNotionToExhibit(updatedExhibit);

      res.json({
        message: `Exhibit state transitioned from ${currentState} to ${newState} successfully`,
        exhibit: formattedExhibit
      });
    } catch (error) {
      next(error);
    }
  },

  /**
   * Archive an exhibit (soft delete)
   */
  async archiveExhibit(req, res, next) {
    try {
      const { id } = req.params;

      // Get the current exhibit
      let currentExhibit;
      try {
        const exhibit = await notionService.getPage(id);
        currentExhibit = transformNotionToExhibit(exhibit);
      } catch (error) {
        throw new NotFoundError(`Exhibit with ID ${id} not found`);
      }

      // Check if the exhibit can be archived from its current state
      if (!isValidStateTransition(currentExhibit.state, exhibitStates.ARCHIVED)) {
        throw new WorkflowStateError(
          `Exhibit in state ${currentExhibit.state} cannot be archived`
        );
      }

      // Update to archived state
      const properties = {
        Status: { select: { name: 'Archived' } }
      };

      // Update in Notion
      await notionService.updatePage(id, properties);

      res.json({
        message: 'Exhibit archived successfully'
      });
    } catch (error) {
      next(error);
    }
  }
};

module.exports = galleryController;
