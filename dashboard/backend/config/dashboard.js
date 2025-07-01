const express = require('express');
const { body, query, validationResult } = require('express-validator');
const winston = require('winston');

const db = require('../config/database');
const redis = require('../config/redis');
const { requireOrganizationAccess, requirePermission } = require('../middleware/auth');

const router = express.Router();

// Configure logger
const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.json()
  ),
  transports: [
    new winston.transports.Console({
      format: winston.format.simple()
    })
  ]
});

// Helper functions
const handleValidationErrors = (req, res, next) => {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    return res.status(400).json({
      error: 'Validation failed',
      message: 'Please check your input',
      details: errors.array()
    });
  }
  next();
};

const calculatePercentageChange = (current, previous) => {
  if (!previous || previous === 0) return 0;
  return ((current - previous) / previous) * 100;
};

const formatMetricValue = (value, unit) => {
  if (unit === 'currency') {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(value);
  }
  
  if (unit === 'percentage') {
    return `${value.toFixed(2)}%`;
  }
  
  if (unit === 'number') {
    return new Intl.NumberFormat('en-US').format(value);
  }
  
  return value.toString();
};

// GET /api/dashboard/:organizationId/overview - Get dashboard overview
router.get('/:organizationId/overview', 
  requireOrganizationAccess('read'),
  async (req, res) => {
    try {
      const { organizationId } = req.params;
      const cacheKey = `dashboard:overview:${organizationId}`;

      // Try to get from cache first
      const cached = await redis.get(cacheKey);
      if (cached) {
        return res.json(cached);
      }

      // Get organization info
      const organizations = await db.query(`
        SELECT id, name, display_name, logo_url, primary_color, secondary_color
        FROM organizations
        WHERE id = ?
      `, [organizationId]);

      if (organizations.length === 0) {
        return res.status(404).json({
          error: 'Organization not found',
          message: 'The specified organization does not exist'
        });
      }

      const organization = organizations[0];

      // Get recent metrics for the organization
      const endDate = new Date();
      const startDate = new Date(endDate.getTime() - 30 * 24 * 60 * 60 * 1000); // 30 days ago
      const previousStartDate = new Date(startDate.getTime() - 30 * 24 * 60 * 60 * 1000); // 60 days ago

      // Get current period metrics
      const currentMetrics = await db.tenantQuery(organization.name, `
        SELECT 
          metric_category,
          metric_name,
          AVG(metric_value) as avg_value,
          SUM(metric_value) as total_value,
          COUNT(*) as data_points,
          metric_unit
        FROM business_metrics
        WHERE period_start >= ? AND period_end <= ?
        GROUP BY metric_category, metric_name, metric_unit
      `, [startDate, endDate]);

      // Get previous period metrics for comparison
      const previousMetrics = await db.tenantQuery(organization.name, `
        SELECT 
          metric_category,
          metric_name,
          AVG(metric_value) as avg_value,
          SUM(metric_value) as total_value,
          COUNT(*) as data_points
        FROM business_metrics
        WHERE period_start >= ? AND period_end <= ?
        GROUP BY metric_category, metric_name
      `, [previousStartDate, startDate]);

      // Create metrics map for easy lookup
      const previousMetricsMap = {};
      previousMetrics.forEach(metric => {
        const key = `${metric.metric_category}:${metric.metric_name}`;
        previousMetricsMap[key] = metric;
      });

      // Process metrics with change calculations
      const processedMetrics = currentMetrics.map(metric => {
        const key = `${metric.metric_category}:${metric.metric_name}`;
        const previousMetric = previousMetricsMap[key];
        
        const currentValue = metric.total_value || metric.avg_value;
        const previousValue = previousMetric ? (previousMetric.total_value || previousMetric.avg_value) : 0;
        const change = calculatePercentageChange(currentValue, previousValue);

        return {
          category: metric.metric_category,
          name: metric.metric_name,
          value: currentValue,
          formattedValue: formatMetricValue(currentValue, metric.metric_unit),
          unit: metric.metric_unit,
          change: change,
          trend: change > 0 ? 'up' : change < 0 ? 'down' : 'stable',
          dataPoints: metric.data_points
        };
      });

      // Group metrics by category
      const metricsByCategory = {};
      processedMetrics.forEach(metric => {
        if (!metricsByCategory[metric.category]) {
          metricsByCategory[metric.category] = [];
        }
        metricsByCategory[metric.category].push(metric);
      });

      // Get recent activity/audit logs
      const recentActivity = await db.query(`
        SELECT 
          action,
          resource_type,
          created_at,
          u.first_name,
          u.last_name
        FROM audit_logs al
        LEFT JOIN users u ON al.user_id = u.id
        WHERE al.organization_id = ?
        ORDER BY al.created_at DESC
        LIMIT 10
      `, [organizationId]);

      // Get active integrations count
      const integrations = await db.tenantQuery(organization.name, `
        SELECT 
          COUNT(*) as total_integrations,
          SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) as active_integrations,
          SUM(CASE WHEN sync_status = 'error' THEN 1 ELSE 0 END) as failed_integrations
        FROM integrations
      `);

      const integrationStats = integrations[0] || {
        total_integrations: 0,
        active_integrations: 0,
        failed_integrations: 0
      };

      // Get user count for organization
      const userStats = await db.query(`
        SELECT 
          COUNT(*) as total_users,
          SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active_users
        FROM user_organizations uo
        JOIN users u ON uo.user_id = u.id
        WHERE uo.organization_id = ?
      `, [organizationId]);

      const overview = {
        organization: {
          id: organization.id,
          name: organization.display_name,
          slug: organization.name,
          logoUrl: organization.logo_url,
          primaryColor: organization.primary_color,
          secondaryColor: organization.secondary_color
        },
        metrics: metricsByCategory,
        summary: {
          totalMetrics: processedMetrics.length,
          categoriesCount: Object.keys(metricsByCategory).length,
          lastUpdated: endDate.toISOString()
        },
        integrations: {
          total: integrationStats.total_integrations,
          active: integrationStats.active_integrations,
          failed: integrationStats.failed_integrations,
          healthScore: integrationStats.total_integrations > 0 
            ? ((integrationStats.active_integrations / integrationStats.total_integrations) * 100).toFixed(1)
            : 100
        },
        users: {
          total: userStats[0]?.total_users || 0,
          active: userStats[0]?.active_users || 0
        },
        recentActivity: recentActivity.map(activity => ({
          action: activity.action,
          resourceType: activity.resource_type,
          timestamp: activity.created_at,
          user: activity.first_name && activity.last_name 
            ? `${activity.first_name} ${activity.last_name}`
            : 'System'
        }))
      };

      // Cache the result for 5 minutes
      await redis.set(cacheKey, overview, 300);

      res.json(overview);

    } catch (error) {
      logger.error('Dashboard overview error:', error);
      res.status(500).json({
        error: 'Failed to load dashboard',
        message: 'An error occurred while loading the dashboard overview'
      });
    }
  }
);

// GET /api/dashboard/:organizationId/metrics - Get detailed metrics
router.get('/:organizationId/metrics',
  requireOrganizationAccess('read'),
  [
    query('category').optional().isString(),
    query('period').optional().isIn(['7d', '30d', '90d', '1y']),
    query('granularity').optional().isIn(['hourly', 'daily', 'weekly', 'monthly'])
  ],
  handleValidationErrors,
  async (req, res) => {
    try {
      const { organizationId } = req.params;
      const { category, period = '30d', granularity = 'daily' } = req.query;

      // Calculate date range
      const endDate = new Date();
      let startDate;
      
      switch (period) {
        case '7d':
          startDate = new Date(endDate.getTime() - 7 * 24 * 60 * 60 * 1000);
          break;
        case '90d':
          startDate = new Date(endDate.getTime() - 90 * 24 * 60 * 60 * 1000);
          break;
        case '1y':
          startDate = new Date(endDate.getTime() - 365 * 24 * 60 * 60 * 1000);
          break;
        default: // 30d
          startDate = new Date(endDate.getTime() - 30 * 24 * 60 * 60 * 1000);
      }

      // Get organization name for tenant query
      const organizations = await db.query('SELECT name FROM organizations WHERE id = ?', [organizationId]);
      if (organizations.length === 0) {
        return res.status(404).json({
          error: 'Organization not found',
          message: 'The specified organization does not exist'
        });
      }

      const organizationName = organizations[0].name;

      // Build query conditions
      let whereClause = 'WHERE period_start >= ? AND period_end <= ?';
      let queryParams = [startDate, endDate];

      if (category) {
        whereClause += ' AND metric_category = ?';
        queryParams.push(category);
      }

      // Get metrics data
      const metrics = await db.tenantQuery(organizationName, `
        SELECT 
          metric_category,
          metric_name,
          metric_value,
          metric_unit,
          target_value,
          period_start,
          period_end,
          metadata
        FROM business_metrics
        ${whereClause}
        ORDER BY period_start ASC, metric_category, metric_name
      `, queryParams);

      // Group metrics by category and name
      const groupedMetrics = {};
      metrics.forEach(metric => {
        const categoryKey = metric.metric_category;
        const nameKey = metric.metric_name;

        if (!groupedMetrics[categoryKey]) {
          groupedMetrics[categoryKey] = {};
        }

        if (!groupedMetrics[categoryKey][nameKey]) {
          groupedMetrics[categoryKey][nameKey] = {
            name: nameKey,
            unit: metric.metric_unit,
            data: [],
            target: metric.target_value
          };
        }

        groupedMetrics[categoryKey][nameKey].data.push({
          value: metric.metric_value,
          timestamp: metric.period_start,
          periodEnd: metric.period_end,
          metadata: metric.metadata ? JSON.parse(metric.metadata) : null
        });
      });

      // Get available categories
      const categories = await db.tenantQuery(organizationName, `
        SELECT DISTINCT metric_category, COUNT(*) as metric_count
        FROM business_metrics
        WHERE period_start >= ?
        GROUP BY metric_category
        ORDER BY metric_category
      `, [startDate]);

      res.json({
        period: {
          start: startDate.toISOString(),
          end: endDate.toISOString(),
          granularity
        },
        categories: categories.map(cat => ({
          name: cat.metric_category,
          count: cat.metric_count
        })),
        metrics: groupedMetrics,
        summary: {
          totalDataPoints: metrics.length,
          categoriesCount: Object.keys(groupedMetrics).length,
          metricsCount: Object.values(groupedMetrics).reduce((total, category) => 
            total + Object.keys(category).length, 0
          )
        }
      });

    } catch (error) {
      logger.error('Dashboard metrics error:', error);
      res.status(500).json({
        error: 'Failed to load metrics',
        message: 'An error occurred while loading metrics data'
      });
    }
  }
);

// POST /api/dashboard/:organizationId/metrics - Add new metric
router.post('/:organizationId/metrics',
  requireOrganizationAccess('write'),
  [
    body('category').notEmpty().isString().withMessage('Category is required'),
    body('name').notEmpty().isString().withMessage('Metric name is required'),
    body('value').isNumeric().withMessage('Value must be a number'),
    body('unit').optional().isString(),
    body('target').optional().isNumeric(),
    body('periodStart').isISO8601().withMessage('Period start must be a valid date'),
    body('periodEnd').isISO8601().withMessage('Period end must be a valid date'),
    body('metadata').optional().isObject()
  ],
  handleValidationErrors,
  async (req, res) => {
    try {
      const { organizationId } = req.params;
      const { category, name, value, unit, target, periodStart, periodEnd, metadata } = req.body;

      // Get organization name for tenant query
      const organizations = await db.query('SELECT name FROM organizations WHERE id = ?', [organizationId]);
      if (organizations.length === 0) {
        return res.status(404).json({
          error: 'Organization not found',
          message: 'The specified organization does not exist'
        });
      }

      const organizationName = organizations[0].name;

      // Insert metric
      const result = await db.tenantQuery(organizationName, `
        INSERT INTO business_metrics (
          metric_category, metric_name, metric_value, metric_unit, 
          target_value, period_start, period_end, metadata
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
      `, [
        category, name, value, unit || null, 
        target || null, periodStart, periodEnd, 
        metadata ? JSON.stringify(metadata) : null
      ]);

      // Clear cache
      await redis.del(`dashboard:overview:${organizationId}`);

      // Log audit event
      await db.query(`
        INSERT INTO audit_logs (organization_id, user_id, action, resource_type, resource_id, new_values, ip_address, user_agent)
        VALUES (?, ?, 'metric_created', 'metric', ?, ?, ?, ?)
      `, [
        organizationId, req.user.id, result.insertId.toString(),
        JSON.stringify({ category, name, value, unit }),
        req.ip, req.get('User-Agent')
      ]);

      res.status(201).json({
        message: 'Metric created successfully',
        metric: {
          id: result.insertId,
          category,
          name,
          value,
          unit,
          target,
          periodStart,
          periodEnd,
          metadata
        }
      });

    } catch (error) {
      logger.error('Create metric error:', error);
      res.status(500).json({
        error: 'Failed to create metric',
        message: 'An error occurred while creating the metric'
      });
    }
  }
);

// GET /api/dashboard/:organizationId/widgets - Get user's dashboard widgets
router.get('/:organizationId/widgets',
  requireOrganizationAccess('read'),
  async (req, res) => {
    try {
      const { organizationId } = req.params;

      // Get organization name for tenant query
      const organizations = await db.query('SELECT name FROM organizations WHERE id = ?', [organizationId]);
      if (organizations.length === 0) {
        return res.status(404).json({
          error: 'Organization not found',
          message: 'The specified organization does not exist'
        });
      }

      const organizationName = organizations[0].name;

      // Get user's widgets
      const widgets = await db.tenantQuery(organizationName, `
        SELECT 
          id, widget_type, title, configuration, 
          position_x, position_y, width, height, is_visible,
          created_at, updated_at
        FROM dashboard_widgets
        WHERE user_id = ? AND is_visible = 1
        ORDER BY position_y, position_x
      `, [req.user.id]);

      const processedWidgets = widgets.map(widget => ({
        id: widget.id,
        type: widget.widget_type,
        title: widget.title,
        configuration: JSON.parse(widget.configuration),
        position: {
          x: widget.position_x,
          y: widget.position_y
        },
        size: {
          width: widget.width,
          height: widget.height
        },
        isVisible: widget.is_visible === 1,
        createdAt: widget.created_at,
        updatedAt: widget.updated_at
      }));

      res.json({
        widgets: processedWidgets,
        summary: {
          totalWidgets: processedWidgets.length,
          visibleWidgets: processedWidgets.filter(w => w.isVisible).length
        }
      });

    } catch (error) {
      logger.error('Get widgets error:', error);
      res.status(500).json({
        error: 'Failed to load widgets',
        message: 'An error occurred while loading dashboard widgets'
      });
    }
  }
);

// POST /api/dashboard/:organizationId/widgets - Create new widget
router.post('/:organizationId/widgets',
  requireOrganizationAccess('write'),
  [
    body('type').notEmpty().isString().withMessage('Widget type is required'),
    body('title').notEmpty().isString().withMessage('Widget title is required'),
    body('configuration').isObject().withMessage('Configuration must be an object'),
    body('position').optional().isObject(),
    body('size').optional().isObject()
  ],
  handleValidationErrors,
  async (req, res) => {
    try {
      const { organizationId } = req.params;
      const { type, title, configuration, position = { x: 0, y: 0 }, size = { width: 4, height: 3 } } = req.body;

      // Get organization name for tenant query
      const organizations = await db.query('SELECT name FROM organizations WHERE id = ?', [organizationId]);
      if (organizations.length === 0) {
        return res.status(404).json({
          error: 'Organization not found',
          message: 'The specified organization does not exist'
        });
      }

      const organizationName = organizations[0].name;

      // Insert widget
      const result = await db.tenantQuery(organizationName, `
        INSERT INTO dashboard_widgets (
          user_id, widget_type, title, configuration,
          position_x, position_y, width, height
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
      `, [
        req.user.id, type, title, JSON.stringify(configuration),
        position.x, position.y, size.width, size.height
      ]);

      // Log audit event
      await db.query(`
        INSERT INTO audit_logs (organization_id, user_id, action, resource_type, resource_id, new_values, ip_address, user_agent)
        VALUES (?, ?, 'widget_created', 'widget', ?, ?, ?, ?)
      `, [
        organizationId, req.user.id, result.insertId.toString(),
        JSON.stringify({ type, title, configuration }),
        req.ip, req.get('User-Agent')
      ]);

      res.status(201).json({
        message: 'Widget created successfully',
        widget: {
          id: result.insertId,
          type,
          title,
          configuration,
          position,
          size,
          isVisible: true
        }
      });

    } catch (error) {
      logger.error('Create widget error:', error);
      res.status(500).json({
        error: 'Failed to create widget',
        message: 'An error occurred while creating the widget'
      });
    }
  }
);

// PUT /api/dashboard/:organizationId/widgets/:widgetId - Update widget
router.put('/:organizationId/widgets/:widgetId',
  requireOrganizationAccess('write'),
  [
    body('title').optional().isString(),
    body('configuration').optional().isObject(),
    body('position').optional().isObject(),
    body('size').optional().isObject(),
    body('isVisible').optional().isBoolean()
  ],
  handleValidationErrors,
  async (req, res) => {
    try {
      const { organizationId, widgetId } = req.params;
      const updates = req.body;

      // Get organization name for tenant query
      const organizations = await db.query('SELECT name FROM organizations WHERE id = ?', [organizationId]);
      if (organizations.length === 0) {
        return res.status(404).json({
          error: 'Organization not found',
          message: 'The specified organization does not exist'
        });
      }

      const organizationName = organizations[0].name;

      // Check if widget exists and belongs to user
      const widgets = await db.tenantQuery(organizationName, `
        SELECT id, configuration FROM dashboard_widgets
        WHERE id = ? AND user_id = ?
      `, [widgetId, req.user.id]);

      if (widgets.length === 0) {
        return res.status(404).json({
          error: 'Widget not found',
          message: 'Widget not found or you do not have permission to modify it'
        });
      }

      // Build update query
      const updateFields = [];
      const updateValues = [];

      if (updates.title) {
        updateFields.push('title = ?');
        updateValues.push(updates.title);
      }

      if (updates.configuration) {
        updateFields.push('configuration = ?');
        updateValues.push(JSON.stringify(updates.configuration));
      }

      if (updates.position) {
        updateFields.push('position_x = ?, position_y = ?');
        updateValues.push(updates.position.x, updates.position.y);
      }

      if (updates.size) {
        updateFields.push('width = ?, height = ?');
        updateValues.push(updates.size.width, updates.size.height);
      }

      if (typeof updates.isVisible === 'boolean') {
        updateFields.push('is_visible = ?');
        updateValues.push(updates.isVisible);
      }

      if (updateFields.length === 0) {
        return res.status(400).json({
          error: 'No updates provided',
          message: 'Please provide at least one field to update'
        });
      }

      updateFields.push('updated_at = CURRENT_TIMESTAMP');
      updateValues.push(widgetId, req.user.id);

      // Update widget
      await db.tenantQuery(organizationName, `
        UPDATE dashboard_widgets 
        SET ${updateFields.join(', ')}
        WHERE id = ? AND user_id = ?
      `, updateValues);

      // Log audit event
      await db.query(`
        INSERT INTO audit_logs (organization_id, user_id, action, resource_type, resource_id, new_values, ip_address, user_agent)
        VALUES (?, ?, 'widget_updated', 'widget', ?, ?, ?, ?)
      `, [
        organizationId, req.user.id, widgetId,
        JSON.stringify(updates),
        req.ip, req.get('User-Agent')
      ]);

      res.json({
        message: 'Widget updated successfully'
      });

    } catch (error) {
      logger.error('Update widget error:', error);
      res.status(500).json({
        error: 'Failed to update widget',
        message: 'An error occurred while updating the widget'
      });
    }
  }
);

// DELETE /api/dashboard/:organizationId/widgets/:widgetId - Delete widget
router.delete('/:organizationId/widgets/:widgetId',
  requireOrganizationAccess('write'),
  async (req, res) => {
    try {
      const { organizationId, widgetId } = req.params;

      // Get organization name for tenant query
      const organizations = await db.query('SELECT name FROM organizations WHERE id = ?', [organizationId]);
      if (organizations.length === 0) {
        return res.status(404).json({
          error: 'Organization not found',
          message: 'The specified organization does not exist'
        });
      }

      const organizationName = organizations[0].name;

      // Check if widget exists and belongs to user
      const widgets = await db.tenantQuery(organizationName, `
        SELECT id FROM dashboard_widgets
        WHERE id = ? AND user_id = ?
      `, [widgetId, req.user.id]);

      if (widgets.length === 0) {
        return res.status(404).json({
          error: 'Widget not found',
          message: 'Widget not found or you do not have permission to delete it'
        });
      }

      // Delete widget
      await db.tenantQuery(organizationName, `
        DELETE FROM dashboard_widgets
        WHERE id = ? AND user_id = ?
      `, [widgetId, req.user.id]);

      // Log audit event
      await db.query(`
        INSERT INTO audit_logs (organization_id, user_id, action, resource_type, resource_id, ip_address, user_agent)
        VALUES (?, ?, 'widget_deleted', 'widget', ?, ?, ?)
      `, [
        organizationId, req.user.id, widgetId,
        req.ip, req.get('User-Agent')
      ]);

      res.json({
        message: 'Widget deleted successfully'
      });

    } catch (error) {
      logger.error('Delete widget error:', error);
      res.status(500).json({
        error: 'Failed to delete widget',
        message: 'An error occurred while deleting the widget'
      });
    }
  }
);

module.exports = router;

