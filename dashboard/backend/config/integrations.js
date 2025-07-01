const express = require('express');
const router = express.Router();
const { authenticateJWT, authorizeRole } = require('../middleware/auth');
const AMConsultingIntegrationService = require('../services/AMConsultingIntegrationService');
const SevenSpaceIntegrationService = require('../services/SevenSpaceIntegrationService');
const HigherSelfIntegrationService = require('../services/HigherSelfIntegrationService');
const db = require('../config/database');
const { AppError } = require('../middleware/errorHandler');

/**
 * @route GET /api/integrations
 * @desc Get all integrations for the organization
 * @access Private (Admin, Manager)
 */
router.get('/', authenticateJWT, authorizeRole(['admin', 'manager']), async (req, res, next) => {
  try {
    const { organizationId } = req.user;
    
    // Get organization name for tenant operations
    const organizations = await db.query('SELECT name FROM organizations WHERE id = ?', [organizationId]);
    if (organizations.length === 0) {
      throw new AppError('Organization not found', 404);
    }
    
    const organizationName = organizations[0].name;
    
    // Get all integrations for the organization
    const integrations = await db.tenantQuery(organizationName, `
      SELECT 
        id, service_name, service_type, is_active, 
        last_sync, sync_status, error_count, error_message,
        created_at, updated_at
      FROM integrations
      ORDER BY service_name ASC, created_at DESC
    `);
    
    return res.json({
      success: true,
      data: integrations
    });
  } catch (error) {
    next(error);
  }
});

/**
 * @route GET /api/integrations/:id
 * @desc Get integration details by ID
 * @access Private (Admin, Manager)
 */
router.get('/:id', authenticateJWT, authorizeRole(['admin', 'manager']), async (req, res, next) => {
  try {
    const { organizationId } = req.user;
    const { id } = req.params;
    
    // Get organization name for tenant operations
    const organizations = await db.query('SELECT name FROM organizations WHERE id = ?', [organizationId]);
    if (organizations.length === 0) {
      throw new AppError('Organization not found', 404);
    }
    
    const organizationName = organizations[0].name;
    
    // Get integration details
    const integrations = await db.tenantQuery(organizationName, `
      SELECT 
        id, service_name, service_type, config, is_active, 
        last_sync, sync_status, sync_results, error_count, error_message,
        created_at, updated_at
      FROM integrations
      WHERE id = ?
    `, [id]);
    
    if (integrations.length === 0) {
      throw new AppError('Integration not found', 404);
    }
    
    const integration = integrations[0];
    
    // Parse config and sync results
    integration.config = JSON.parse(integration.config || '{}');
    integration.sync_results = JSON.parse(integration.sync_results || '{}');
    
    return res.json({
      success: true,
      data: integration
    });
  } catch (error) {
    next(error);
  }
});

/**
 * @route POST /api/integrations/am-consulting/initialize
 * @desc Initialize A.M. Consulting integration
 * @access Private (Admin)
 */
router.post('/am-consulting/initialize', authenticateJWT, authorizeRole(['admin']), async (req, res, next) => {
  try {
    const { organizationId } = req.user;
    const config = req.body;
    
    const result = await AMConsultingIntegrationService.initialize(organizationId, config);
    
    return res.json({
      success: true,
      data: result
    });
  } catch (error) {
    next(error);
  }
});

/**
 * @route POST /api/integrations/seven-space/initialize
 * @desc Initialize The 7 Space integration
 * @access Private (Admin)
 */
router.post('/seven-space/initialize', authenticateJWT, authorizeRole(['admin']), async (req, res, next) => {
  try {
    const { organizationId } = req.user;
    const config = req.body;
    
    const result = await SevenSpaceIntegrationService.initialize(organizationId, config);
    
    return res.json({
      success: true,
      data: result
    });
  } catch (error) {
    next(error);
  }
});

/**
 * @route POST /api/integrations/higherself-network/initialize
 * @desc Initialize HigherSelf Network integration
 * @access Private (Admin)
 */
router.post('/higherself-network/initialize', authenticateJWT, authorizeRole(['admin']), async (req, res, next) => {
  try {
    const { organizationId } = req.user;
    const config = req.body;
    
    const result = await HigherSelfIntegrationService.initialize(organizationId, config);
    
    return res.json({
      success: true,
      data: result
    });
  } catch (error) {
    next(error);
  }
});

/**
 * @route POST /api/integrations/:id/sync
 * @desc Trigger manual sync for an integration
 * @access Private (Admin, Manager)
 */
router.post('/:id/sync', authenticateJWT, authorizeRole(['admin', 'manager']), async (req, res, next) => {
  try {
    const { organizationId } = req.user;
    const { id } = req.params;
    
    // Get organization name for tenant operations
    const organizations = await db.query('SELECT name FROM organizations WHERE id = ?', [organizationId]);
    if (organizations.length === 0) {
      throw new AppError('Organization not found', 404);
    }
    
    const organizationName = organizations[0].name;
    
    // Get integration details
    const integrations = await db.tenantQuery(organizationName, `
      SELECT id, service_name, is_active
      FROM integrations
      WHERE id = ?
    `, [id]);
    
    if (integrations.length === 0) {
      throw new AppError('Integration not found', 404);
    }
    
    const integration = integrations[0];
    
    if (!integration.is_active) {
      throw new AppError('Cannot sync inactive integration', 400);
    }
    
    let result;
    
    // Call appropriate service based on integration type
    switch (integration.service_name) {
      case 'am_consulting':
        result = await AMConsultingIntegrationService.syncData(organizationId, integration.id);
        break;
      case 'seven_space':
        result = await SevenSpaceIntegrationService.syncData(organizationId, integration.id);
        break;
      case 'higherself_network':
        result = await HigherSelfIntegrationService.syncData(organizationId, integration.id);
        break;
      default:
        throw new AppError('Unknown integration service', 400);
    }
    
    return res.json({
      success: true,
      data: result
    });
  } catch (error) {
    next(error);
  }
});

/**
 * @route PUT /api/integrations/:id/toggle
 * @desc Toggle integration active status
 * @access Private (Admin)
 */
router.put('/:id/toggle', authenticateJWT, authorizeRole(['admin']), async (req, res, next) => {
  try {
    const { organizationId } = req.user;
    const { id } = req.params;
    
    // Get organization name for tenant operations
    const organizations = await db.query('SELECT name FROM organizations WHERE id = ?', [organizationId]);
    if (organizations.length === 0) {
      throw new AppError('Organization not found', 404);
    }
    
    const organizationName = organizations[0].name;
    
    // Get current status
    const integrations = await db.tenantQuery(organizationName, `
      SELECT id, is_active
      FROM integrations
      WHERE id = ?
    `, [id]);
    
    if (integrations.length === 0) {
      throw new AppError('Integration not found', 404);
    }
    
    const integration = integrations[0];
    const newStatus = !integration.is_active;
    
    // Update status
    await db.tenantQuery(organizationName, `
      UPDATE integrations
      SET is_active = ?, updated_at = CURRENT_TIMESTAMP
      WHERE id = ?
    `, [newStatus, id]);
    
    return res.json({
      success: true,
      data: {
        id,
        is_active: newStatus
      }
    });
  } catch (error) {
    next(error);
  }
});

/**
 * @route PUT /api/integrations/:id/config
 * @desc Update integration configuration
 * @access Private (Admin)
 */
router.put('/:id/config', authenticateJWT, authorizeRole(['admin']), async (req, res, next) => {
  try {
    const { organizationId } = req.user;
    const { id } = req.params;
    const newConfig = req.body;
    
    // Get organization name for tenant operations
    const organizations = await db.query('SELECT name FROM organizations WHERE id = ?', [organizationId]);
    if (organizations.length === 0) {
      throw new AppError('Organization not found', 404);
    }
    
    const organizationName = organizations[0].name;
    
    // Get current config
    const integrations = await db.tenantQuery(organizationName, `
      SELECT id, service_name, config
      FROM integrations
      WHERE id = ?
    `, [id]);
    
    if (integrations.length === 0) {
      throw new AppError('Integration not found', 404);
    }
    
    const integration = integrations[0];
    const currentConfig = JSON.parse(integration.config || '{}');
    
    // Merge configs
    const mergedConfig = {
      ...currentConfig,
      ...newConfig
    };
    
    // Update config
    await db.tenantQuery(organizationName, `
      UPDATE integrations
      SET config = ?, updated_at = CURRENT_TIMESTAMP
      WHERE id = ?
    `, [JSON.stringify(mergedConfig), id]);
    
    return res.json({
      success: true,
      data: {
        id,
        config: mergedConfig
      }
    });
  } catch (error) {
    next(error);
  }
});

/**
 * @route POST /api/integrations/am-consulting/test
 * @desc Test A.M. Consulting integration connection
 * @access Private (Admin)
 */
router.post('/am-consulting/test', authenticateJWT, authorizeRole(['admin']), async (req, res, next) => {
  try {
    const { organizationId } = req.user;
    const config = req.body;
    
    const result = await AMConsultingIntegrationService.testConnection(organizationId, config);
    
    return res.json({
      success: true,
      data: result
    });
  } catch (error) {
    next(error);
  }
});

/**
 * @route POST /api/integrations/seven-space/test
 * @desc Test The 7 Space integration connection
 * @access Private (Admin)
 */
router.post('/seven-space/test', authenticateJWT, authorizeRole(['admin']), async (req, res, next) => {
  try {
    const { organizationId } = req.user;
    const config = req.body;
    
    const result = await SevenSpaceIntegrationService.testConnection(organizationId, config);
    
    return res.json({
      success: true,
      data: result
    });
  } catch (error) {
    next(error);
  }
});

/**
 * @route POST /api/integrations/higherself-network/test
 * @desc Test HigherSelf Network integration connection
 * @access Private (Admin)
 */
router.post('/higherself-network/test', authenticateJWT, authorizeRole(['admin']), async (req, res, next) => {
  try {
    const { organizationId } = req.user;
    const config = req.body;
    
    const result = await HigherSelfIntegrationService.testConnection(organizationId, config);
    
    return res.json({
      success: true,
      data: result
    });
  } catch (error) {
    next(error);
  }
});

module.exports = router;

