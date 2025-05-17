/**
 * Gallery Exhibit Model
 * Defines the structure and validation for gallery exhibits
 * Maps to the Gallery Exhibit Management Workflow in OPERATIONAL_WORKFLOWS.md
 */
const Joi = require('joi');

// Define the valid exhibit states based on the workflow
const exhibitStates = {
  PROPOSED: 'proposed',
  REVIEWED: 'reviewed',
  SCHEDULED: 'scheduled',
  INSTALLED: 'installed',
  ACTIVE: 'active',
  ARCHIVED: 'archived'
};

// Define valid state transitions according to the workflow
const validStateTransitions = {
  [exhibitStates.PROPOSED]: [exhibitStates.REVIEWED],
  [exhibitStates.REVIEWED]: [exhibitStates.SCHEDULED, exhibitStates.ARCHIVED],
  [exhibitStates.SCHEDULED]: [exhibitStates.INSTALLED, exhibitStates.ARCHIVED],
  [exhibitStates.INSTALLED]: [exhibitStates.ACTIVE, exhibitStates.ARCHIVED],
  [exhibitStates.ACTIVE]: [exhibitStates.ARCHIVED],
  [exhibitStates.ARCHIVED]: []
};

// Schema for creating a new exhibit
const createExhibitSchema = Joi.object({
  title: Joi.string().required().max(100),
  artist: Joi.string().required().max(100),
  description: Joi.string().required().max(1000),
  mediums: Joi.array().items(Joi.string()).min(1).required(),
  dimensions: Joi.string().optional(),
  price: Joi.number().min(0).optional(),
  images: Joi.array().items(Joi.string().uri()).min(1).required(),
  proposedStartDate: Joi.date().iso().greater('now').required(),
  proposedEndDate: Joi.date().iso().greater(Joi.ref('proposedStartDate')).required(),
  featuredPiece: Joi.boolean().default(false),
  contactInformation: Joi.object({
    email: Joi.string().email().required(),
    phone: Joi.string().optional(),
    website: Joi.string().uri().optional()
  }).required()
});

// Schema for updating an exhibit
const updateExhibitSchema = Joi.object({
  title: Joi.string().max(100),
  artist: Joi.string().max(100),
  description: Joi.string().max(1000),
  mediums: Joi.array().items(Joi.string()).min(1),
  dimensions: Joi.string(),
  price: Joi.number().min(0),
  images: Joi.array().items(Joi.string().uri()).min(1),
  proposedStartDate: Joi.date().iso(),
  proposedEndDate: Joi.date().iso(),
  featuredPiece: Joi.boolean(),
  contactInformation: Joi.object({
    email: Joi.string().email(),
    phone: Joi.string(),
    website: Joi.string().uri()
  }),
  state: Joi.string().valid(...Object.values(exhibitStates))
}).min(1);

// Schema for transitioning an exhibit state
const stateTransitionSchema = Joi.object({
  currentState: Joi.string().valid(...Object.values(exhibitStates)).required(),
  newState: Joi.string().valid(...Object.values(exhibitStates)).required(),
  notes: Joi.string().max(500).optional()
});

/**
 * Validate if a state transition is valid according to the workflow
 * @param {string} currentState - Current exhibit state
 * @param {string} newState - Target state to transition to
 * @returns {boolean} - Whether the transition is valid
 */
function isValidStateTransition(currentState, newState) {
  return validStateTransitions[currentState]?.includes(newState) || false;
}

module.exports = {
  exhibitStates,
  validStateTransitions,
  createExhibitSchema,
  updateExhibitSchema,
  stateTransitionSchema,
  isValidStateTransition
};
