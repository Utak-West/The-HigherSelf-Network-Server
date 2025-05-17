/**
 * Gallery Routes
 * Defines the API endpoints for Gallery Exhibit Management
 */
const express = require('express');
const router = express.Router();
const galleryController = require('../controllers/galleryController');

/**
 * @route   GET /api/v1/gallery/exhibits
 * @desc    Get all exhibits with optional filtering
 * @access  Public
 * @query   {string} state - Filter by exhibit state
 * @query   {string} artist - Filter by artist name (partial match)
 * @query   {boolean} featured - Filter for featured exhibits
 */
router.get('/exhibits', galleryController.getAllExhibits);

/**
 * @route   GET /api/v1/gallery/exhibits/:id
 * @desc    Get a single exhibit by ID
 * @access  Public
 * @param   {string} id - Exhibit ID
 */
router.get('/exhibits/:id', galleryController.getExhibitById);

/**
 * @route   POST /api/v1/gallery/exhibits
 * @desc    Create a new exhibit (automatically in PROPOSED state)
 * @access  Requires authentication
 */
router.post('/exhibits', galleryController.createExhibit);

/**
 * @route   PUT /api/v1/gallery/exhibits/:id
 * @desc    Update an existing exhibit
 * @access  Requires authentication with appropriate role
 * @param   {string} id - Exhibit ID
 */
router.put('/exhibits/:id', galleryController.updateExhibit);

/**
 * @route   POST /api/v1/gallery/exhibits/:id/transition
 * @desc    Transition an exhibit to a new state in the workflow
 * @access  Requires authentication with appropriate role
 * @param   {string} id - Exhibit ID
 */
router.post('/exhibits/:id/transition', galleryController.transitionExhibitState);

/**
 * @route   DELETE /api/v1/gallery/exhibits/:id
 * @desc    Archive an exhibit (soft delete)
 * @access  Requires authentication with appropriate role
 * @param   {string} id - Exhibit ID
 */
router.delete('/exhibits/:id', galleryController.archiveExhibit);

module.exports = router;
