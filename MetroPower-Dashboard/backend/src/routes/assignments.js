/**
 * Assignment Routes
 *
 * Handles assignment management endpoints for the MetroPower Dashboard API
 * with comprehensive error handling and demo mode support.
 *
 * Copyright 2025 The HigherSelf Network
 */

const express = require('express');
const { asyncHandler } = require('../middleware/errorHandler');
const { requireManager } = require('../middleware/auth');
const logger = require('../utils/logger');

const router = express.Router();

/**
 * @route   POST /api/assignments
 * @desc    Create new assignment
 * @access  Private (Manager+)
 */
router.post('/', requireManager, asyncHandler(async (req, res) => {
  try {
    const assignmentData = req.body;

    // Basic validation
    const requiredFields = ['employee_id', 'project_id', 'assignment_date', 'hours_assigned'];
    const missingFields = requiredFields.filter(field => !assignmentData[field]);

    if (missingFields.length > 0) {
      return res.status(400).json({
        error: 'Validation error',
        message: `Missing required fields: ${missingFields.join(', ')}`
      });
    }

    const dataService = require('../services/demoService');
    const assignment = await dataService.createAssignment(assignmentData);

    res.status(201).json({
      success: true,
      data: assignment
    });

  } catch (error) {
    logger.error('Error creating assignment:', error);
    res.status(500).json({
      error: 'Assignment creation error',
      message: 'Failed to create assignment'
    });
  }
}));

/**
 * @route   PUT /api/assignments/:id
 * @desc    Update assignment
 * @access  Private (Manager+)
 */
router.put('/:id', requireManager, asyncHandler(async (req, res) => {
  try {
    const { id } = req.params;
    const updateData = req.body;

    const dataService = require('../services/demoService');
    const assignment = await dataService.updateAssignment(parseInt(id), updateData);

    res.json({
      success: true,
      data: assignment
    });

  } catch (error) {
    logger.error('Error updating assignment:', error);
    res.status(500).json({
      error: 'Assignment update error',
      message: 'Failed to update assignment'
    });
  }
}));

/**
 * @route   DELETE /api/assignments/:id
 * @desc    Delete assignment
 * @access  Private (Manager+)
 */
router.delete('/:id', requireManager, asyncHandler(async (req, res) => {
  try {
    const { id } = req.params;

    const dataService = require('../services/demoService');
    await dataService.deleteAssignment(parseInt(id));

    res.json({
      success: true,
      message: 'Assignment deleted successfully'
    });

  } catch (error) {
    logger.error('Error deleting assignment:', error);
    res.status(500).json({
      error: 'Assignment deletion error',
      message: 'Failed to delete assignment'
    });
  }
}));

module.exports = router;
