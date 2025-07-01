const express = require('express');
const router = express.Router();
const { authenticateJWT, authorizeRole } = require('../middleware/auth');
const MonitoringService = require('../services/MonitoringService');

/**
 * @route GET /api/monitoring/health
 * @desc Get system health status
 * @access Private (Admin, Manager)
 */
router.get('/health', authenticateJWT, authorizeRole(['admin', 'manager']), async (req, res, next) => {
  try {
    const health = await MonitoringService.getSystemHealth();
    
    return res.json({
      success: true,
      data: health
    });
  } catch (error) {
    next(error);
  }
});

/**
 * @route GET /api/monitoring/history
 * @desc Get historical metrics
 * @access Private (Admin, Manager)
 */
router.get('/history', authenticateJWT, authorizeRole(['admin', 'manager']), async (req, res, next) => {
  try {
    const { hours } = req.query;
    const hoursNum = parseInt(hours, 10) || 24;
    
    const history = await MonitoringService.getHistoricalMetrics(hoursNum);
    
    return res.json({
      success: true,
      data: history
    });
  } catch (error) {
    next(error);
  }
});

/**
 * @route GET /api/monitoring/alerts
 * @desc Get recent alerts
 * @access Private (Admin, Manager)
 */
router.get('/alerts', authenticateJWT, authorizeRole(['admin', 'manager']), async (req, res, next) => {
  try {
    const { limit } = req.query;
    const limitNum = parseInt(limit, 10) || 10;
    
    const alerts = await MonitoringService.getAlerts(limitNum);
    
    return res.json({
      success: true,
      data: alerts
    });
  } catch (error) {
    next(error);
  }
});

/**
 * @route GET /api/monitoring/thresholds
 * @desc Get alert thresholds
 * @access Private (Admin, Manager)
 */
router.get('/thresholds', authenticateJWT, authorizeRole(['admin', 'manager']), async (req, res, next) => {
  try {
    const thresholds = await MonitoringService.getAlertThresholds();
    
    return res.json({
      success: true,
      data: thresholds
    });
  } catch (error) {
    next(error);
  }
});

/**
 * @route PUT /api/monitoring/thresholds
 * @desc Update alert thresholds
 * @access Private (Admin)
 */
router.put('/thresholds', authenticateJWT, authorizeRole(['admin']), async (req, res, next) => {
  try {
    const thresholds = req.body;
    
    const updatedThresholds = await MonitoringService.updateAlertThresholds(thresholds);
    
    return res.json({
      success: true,
      data: updatedThresholds
    });
  } catch (error) {
    next(error);
  }
});

/**
 * @route POST /api/monitoring/reset-metrics
 * @desc Reset API metrics
 * @access Private (Admin)
 */
router.post('/reset-metrics', authenticateJWT, authorizeRole(['admin']), async (req, res, next) => {
  try {
    await MonitoringService.resetApiMetrics();
    
    return res.json({
      success: true,
      message: 'API metrics reset successfully'
    });
  } catch (error) {
    next(error);
  }
});

module.exports = router;

