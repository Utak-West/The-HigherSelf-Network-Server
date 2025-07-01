const axios = require('axios');
const winston = require('winston');
const redis = require('../config/redis');
const db = require('../config/database');
const { AppError } = require('../middleware/errorHandler');

// Configure logger
const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.json()
  ),
  transports: [
    new winston.transports.File({ filename: 'logs/integrations.log' }),
    new winston.transports.Console({
      format: winston.format.simple()
    })
  ]
});

/**
 * A.M. Consulting Integration Service
 * Handles integration with A.M. Consulting's systems for conflict management,
 * practitioner scheduling, and revenue tracking.
 */
class AMConsultingIntegrationService {
  constructor() {
    this.baseUrl = process.env.AM_CONSULTING_API_URL;
    this.apiKey = process.env.AM_CONSULTING_API_KEY;
    this.client = axios.create({
      baseURL: this.baseUrl,
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': this.apiKey
      }
    });
  }

  /**
   * Initialize the integration for an organization
   * @param {string} organizationId - The organization ID
   * @param {Object} config - Integration configuration
   * @returns {Promise<Object>} - Integration status
   */
  async initialize(organizationId, config = {}) {
    try {
      logger.info(`Initializing A.M. Consulting integration for organization ${organizationId}`);
      
      // Get organization name for tenant operations
      const organizations = await db.query('SELECT name FROM organizations WHERE id = ?', [organizationId]);
      if (organizations.length === 0) {
        throw new AppError('Organization not found', 404);
      }
      
      const organizationName = organizations[0].name;
      
      // Check if integration already exists
      const existingIntegrations = await db.tenantQuery(organizationName, `
        SELECT id FROM integrations 
        WHERE service_name = 'am_consulting' AND is_active = 1
      `);
      
      if (existingIntegrations.length > 0) {
        throw new AppError('A.M. Consulting integration already exists for this organization', 409);
      }
      
      // Create integration record
      const integrationConfig = {
        apiUrl: config.apiUrl || this.baseUrl,
        apiKey: config.apiKey || this.apiKey,
        syncSchedule: config.syncSchedule || '0 0 * * *', // Default: daily at midnight
        syncEnabled: config.syncEnabled !== undefined ? config.syncEnabled : true,
        dataMapping: config.dataMapping || {
          conflicts: {
            enabled: true,
            fields: ['id', 'title', 'description', 'status', 'priority', 'assignedTo', 'createdAt', 'updatedAt']
          },
          practitioners: {
            enabled: true,
            fields: ['id', 'name', 'specialty', 'availability', 'hourlyRate', 'status']
          },
          revenue: {
            enabled: true,
            fields: ['period', 'amount', 'source', 'category']
          }
        }
      };
      
      // Insert integration record
      const result = await db.tenantQuery(organizationName, `
        INSERT INTO integrations (
          service_name, service_type, config, is_active, 
          last_sync, sync_status, created_at, updated_at
        ) VALUES (?, ?, ?, ?, NULL, 'pending', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
      `, [
        'am_consulting',
        'api',
        JSON.stringify(integrationConfig),
        true
      ]);
      
      const integrationId = result.insertId;
      
      // Create necessary tables for storing integrated data
      await this.createIntegrationTables(organizationName);
      
      // Perform initial sync
      if (config.performInitialSync !== false) {
        await this.syncData(organizationId, integrationId);
      }
      
      return {
        success: true,
        integrationId,
        message: 'A.M. Consulting integration initialized successfully'
      };
    } catch (error) {
      logger.error('Error initializing A.M. Consulting integration:', error);
      throw error;
    }
  }
  
  /**
   * Create necessary tables for storing integrated data
   * @param {string} organizationName - The organization name (for tenant operations)
   * @returns {Promise<void>}
   */
  async createIntegrationTables(organizationName) {
    try {
      // Create conflicts table
      await db.tenantQuery(organizationName, `
        CREATE TABLE IF NOT EXISTS am_consulting_conflicts (
          id VARCHAR(36) PRIMARY KEY,
          title VARCHAR(255) NOT NULL,
          description TEXT,
          status VARCHAR(50) NOT NULL,
          priority VARCHAR(20) NOT NULL,
          assigned_to VARCHAR(100),
          external_id VARCHAR(100),
          external_url VARCHAR(255),
          created_at TIMESTAMP NOT NULL,
          updated_at TIMESTAMP NOT NULL,
          synced_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
          metadata JSON
        )
      `);
      
      // Create practitioners table
      await db.tenantQuery(organizationName, `
        CREATE TABLE IF NOT EXISTS am_consulting_practitioners (
          id VARCHAR(36) PRIMARY KEY,
          name VARCHAR(100) NOT NULL,
          specialty VARCHAR(100),
          availability JSON,
          hourly_rate DECIMAL(10, 2),
          status VARCHAR(20) NOT NULL,
          external_id VARCHAR(100),
          external_url VARCHAR(255),
          created_at TIMESTAMP NOT NULL,
          updated_at TIMESTAMP NOT NULL,
          synced_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
          metadata JSON
        )
      `);
      
      // Create revenue table
      await db.tenantQuery(organizationName, `
        CREATE TABLE IF NOT EXISTS am_consulting_revenue (
          id INT AUTO_INCREMENT PRIMARY KEY,
          period_start DATE NOT NULL,
          period_end DATE NOT NULL,
          amount DECIMAL(15, 2) NOT NULL,
          source VARCHAR(100),
          category VARCHAR(100),
          external_id VARCHAR(100),
          created_at TIMESTAMP NOT NULL,
          updated_at TIMESTAMP NOT NULL,
          synced_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
          metadata JSON
        )
      `);
      
      logger.info(`Created A.M. Consulting integration tables for organization ${organizationName}`);
    } catch (error) {
      logger.error(`Error creating integration tables for ${organizationName}:`, error);
      throw error;
    }
  }
  
  /**
   * Sync data from A.M. Consulting API
   * @param {string} organizationId - The organization ID
   * @param {number} integrationId - The integration ID
   * @returns {Promise<Object>} - Sync results
   */
  async syncData(organizationId, integrationId) {
    try {
      logger.info(`Starting A.M. Consulting data sync for organization ${organizationId}, integration ${integrationId}`);
      
      // Get organization name for tenant operations
      const organizations = await db.query('SELECT name FROM organizations WHERE id = ?', [organizationId]);
      if (organizations.length === 0) {
        throw new AppError('Organization not found', 404);
      }
      
      const organizationName = organizations[0].name;
      
      // Get integration config
      const integrations = await db.tenantQuery(organizationName, `
        SELECT id, config FROM integrations 
        WHERE id = ? AND service_name = 'am_consulting' AND is_active = 1
      `, [integrationId]);
      
      if (integrations.length === 0) {
        throw new AppError('Active A.M. Consulting integration not found', 404);
      }
      
      const integration = integrations[0];
      const config = JSON.parse(integration.config);
      
      // Update sync status
      await db.tenantQuery(organizationName, `
        UPDATE integrations 
        SET sync_status = 'in_progress', last_sync_started = CURRENT_TIMESTAMP
        WHERE id = ?
      `, [integrationId]);
      
      // Initialize sync results
      const syncResults = {
        conflicts: { added: 0, updated: 0, errors: 0 },
        practitioners: { added: 0, updated: 0, errors: 0 },
        revenue: { added: 0, updated: 0, errors: 0 }
      };
      
      // Sync conflicts if enabled
      if (config.dataMapping.conflicts?.enabled) {
        try {
          const conflictsResult = await this.syncConflicts(organizationName, config);
          syncResults.conflicts = conflictsResult;
        } catch (error) {
          logger.error(`Error syncing conflicts for ${organizationName}:`, error);
          syncResults.conflicts.errors++;
        }
      }
      
      // Sync practitioners if enabled
      if (config.dataMapping.practitioners?.enabled) {
        try {
          const practitionersResult = await this.syncPractitioners(organizationName, config);
          syncResults.practitioners = practitionersResult;
        } catch (error) {
          logger.error(`Error syncing practitioners for ${organizationName}:`, error);
          syncResults.practitioners.errors++;
        }
      }
      
      // Sync revenue if enabled
      if (config.dataMapping.revenue?.enabled) {
        try {
          const revenueResult = await this.syncRevenue(organizationName, config);
          syncResults.revenue = revenueResult;
        } catch (error) {
          logger.error(`Error syncing revenue for ${organizationName}:`, error);
          syncResults.revenue.errors++;
        }
      }
      
      // Calculate total metrics
      const totalAdded = syncResults.conflicts.added + syncResults.practitioners.added + syncResults.revenue.added;
      const totalUpdated = syncResults.conflicts.updated + syncResults.practitioners.updated + syncResults.revenue.updated;
      const totalErrors = syncResults.conflicts.errors + syncResults.practitioners.errors + syncResults.revenue.errors;
      
      // Update sync status
      const syncStatus = totalErrors > 0 ? 'completed_with_errors' : 'completed';
      
      await db.tenantQuery(organizationName, `
        UPDATE integrations 
        SET 
          sync_status = ?, 
          last_sync = CURRENT_TIMESTAMP,
          sync_results = ?,
          error_count = ?
        WHERE id = ?
      `, [
        syncStatus,
        JSON.stringify(syncResults),
        totalErrors,
        integrationId
      ]);
      
      // Create business metrics from the sync data
      await this.createBusinessMetrics(organizationId, organizationName);
      
      // Clear cache
      await redis.del(`dashboard:overview:${organizationId}`);
      
      logger.info(`Completed A.M. Consulting data sync for organization ${organizationId}`, {
        added: totalAdded,
        updated: totalUpdated,
        errors: totalErrors
      });
      
      return {
        success: true,
        status: syncStatus,
        results: syncResults,
        totalAdded,
        totalUpdated,
        totalErrors
      };
    } catch (error) {
      logger.error(`Error during A.M. Consulting data sync for organization ${organizationId}:`, error);
      
      // Update sync status to error
      const organizations = await db.query('SELECT name FROM organizations WHERE id = ?', [organizationId]);
      if (organizations.length > 0) {
        const organizationName = organizations[0].name;
        
        await db.tenantQuery(organizationName, `
          UPDATE integrations 
          SET 
            sync_status = 'error', 
            last_sync = CURRENT_TIMESTAMP,
            error_message = ?
          WHERE id = ?
        `, [
          error.message || 'Unknown error during sync',
          integrationId
        ]);
      }
      
      throw error;
    }
  }
  
  /**
   * Sync conflicts data
   * @param {string} organizationName - The organization name
   * @param {Object} config - Integration configuration
   * @returns {Promise<Object>} - Sync results
   */
  async syncConflicts(organizationName, config) {
    try {
      logger.info(`Syncing conflicts for ${organizationName}`);
      
      // In a real implementation, this would call the actual API
      // For demonstration, we'll simulate API data
      const conflicts = await this.fetchMockConflicts();
      
      const result = { added: 0, updated: 0, errors: 0 };
      
      // Process each conflict
      for (const conflict of conflicts) {
        try {
          // Check if conflict already exists
          const existingConflicts = await db.tenantQuery(organizationName, `
            SELECT id FROM am_consulting_conflicts WHERE id = ?
          `, [conflict.id]);
          
          if (existingConflicts.length > 0) {
            // Update existing conflict
            await db.tenantQuery(organizationName, `
              UPDATE am_consulting_conflicts
              SET 
                title = ?,
                description = ?,
                status = ?,
                priority = ?,
                assigned_to = ?,
                external_id = ?,
                external_url = ?,
                updated_at = ?,
                synced_at = CURRENT_TIMESTAMP,
                metadata = ?
              WHERE id = ?
            `, [
              conflict.title,
              conflict.description,
              conflict.status,
              conflict.priority,
              conflict.assignedTo,
              conflict.externalId,
              conflict.externalUrl,
              new Date(conflict.updatedAt),
              JSON.stringify(conflict.metadata || {}),
              conflict.id
            ]);
            
            result.updated++;
          } else {
            // Insert new conflict
            await db.tenantQuery(organizationName, `
              INSERT INTO am_consulting_conflicts (
                id, title, description, status, priority, assigned_to,
                external_id, external_url, created_at, updated_at, synced_at, metadata
              ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
            `, [
              conflict.id,
              conflict.title,
              conflict.description,
              conflict.status,
              conflict.priority,
              conflict.assignedTo,
              conflict.externalId,
              conflict.externalUrl,
              new Date(conflict.createdAt),
              new Date(conflict.updatedAt),
              JSON.stringify(conflict.metadata || {})
            ]);
            
            result.added++;
          }
        } catch (error) {
          logger.error(`Error processing conflict ${conflict.id}:`, error);
          result.errors++;
        }
      }
      
      logger.info(`Completed conflicts sync for ${organizationName}`, result);
      return result;
    } catch (error) {
      logger.error(`Error syncing conflicts for ${organizationName}:`, error);
      throw error;
    }
  }
  
  /**
   * Sync practitioners data
   * @param {string} organizationName - The organization name
   * @param {Object} config - Integration configuration
   * @returns {Promise<Object>} - Sync results
   */
  async syncPractitioners(organizationName, config) {
    try {
      logger.info(`Syncing practitioners for ${organizationName}`);
      
      // In a real implementation, this would call the actual API
      // For demonstration, we'll simulate API data
      const practitioners = await this.fetchMockPractitioners();
      
      const result = { added: 0, updated: 0, errors: 0 };
      
      // Process each practitioner
      for (const practitioner of practitioners) {
        try {
          // Check if practitioner already exists
          const existingPractitioners = await db.tenantQuery(organizationName, `
            SELECT id FROM am_consulting_practitioners WHERE id = ?
          `, [practitioner.id]);
          
          if (existingPractitioners.length > 0) {
            // Update existing practitioner
            await db.tenantQuery(organizationName, `
              UPDATE am_consulting_practitioners
              SET 
                name = ?,
                specialty = ?,
                availability = ?,
                hourly_rate = ?,
                status = ?,
                external_id = ?,
                external_url = ?,
                updated_at = ?,
                synced_at = CURRENT_TIMESTAMP,
                metadata = ?
              WHERE id = ?
            `, [
              practitioner.name,
              practitioner.specialty,
              JSON.stringify(practitioner.availability || {}),
              practitioner.hourlyRate,
              practitioner.status,
              practitioner.externalId,
              practitioner.externalUrl,
              new Date(practitioner.updatedAt),
              JSON.stringify(practitioner.metadata || {}),
              practitioner.id
            ]);
            
            result.updated++;
          } else {
            // Insert new practitioner
            await db.tenantQuery(organizationName, `
              INSERT INTO am_consulting_practitioners (
                id, name, specialty, availability, hourly_rate, status,
                external_id, external_url, created_at, updated_at, synced_at, metadata
              ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
            `, [
              practitioner.id,
              practitioner.name,
              practitioner.specialty,
              JSON.stringify(practitioner.availability || {}),
              practitioner.hourlyRate,
              practitioner.status,
              practitioner.externalId,
              practitioner.externalUrl,
              new Date(practitioner.createdAt),
              new Date(practitioner.updatedAt),
              JSON.stringify(practitioner.metadata || {})
            ]);
            
            result.added++;
          }
        } catch (error) {
          logger.error(`Error processing practitioner ${practitioner.id}:`, error);
          result.errors++;
        }
      }
      
      logger.info(`Completed practitioners sync for ${organizationName}`, result);
      return result;
    } catch (error) {
      logger.error(`Error syncing practitioners for ${organizationName}:`, error);
      throw error;
    }
  }
  
  /**
   * Sync revenue data
   * @param {string} organizationName - The organization name
   * @param {Object} config - Integration configuration
   * @returns {Promise<Object>} - Sync results
   */
  async syncRevenue(organizationName, config) {
    try {
      logger.info(`Syncing revenue for ${organizationName}`);
      
      // In a real implementation, this would call the actual API
      // For demonstration, we'll simulate API data
      const revenueData = await this.fetchMockRevenue();
      
      const result = { added: 0, updated: 0, errors: 0 };
      
      // Process each revenue entry
      for (const revenue of revenueData) {
        try {
          // Check if revenue entry already exists by external ID
          const existingRevenue = await db.tenantQuery(organizationName, `
            SELECT id FROM am_consulting_revenue WHERE external_id = ?
          `, [revenue.externalId]);
          
          if (existingRevenue.length > 0) {
            // Update existing revenue entry
            await db.tenantQuery(organizationName, `
              UPDATE am_consulting_revenue
              SET 
                period_start = ?,
                period_end = ?,
                amount = ?,
                source = ?,
                category = ?,
                updated_at = ?,
                synced_at = CURRENT_TIMESTAMP,
                metadata = ?
              WHERE external_id = ?
            `, [
              new Date(revenue.periodStart),
              new Date(revenue.periodEnd),
              revenue.amount,
              revenue.source,
              revenue.category,
              new Date(revenue.updatedAt),
              JSON.stringify(revenue.metadata || {}),
              revenue.externalId
            ]);
            
            result.updated++;
          } else {
            // Insert new revenue entry
            await db.tenantQuery(organizationName, `
              INSERT INTO am_consulting_revenue (
                period_start, period_end, amount, source, category,
                external_id, created_at, updated_at, synced_at, metadata
              ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
            `, [
              new Date(revenue.periodStart),
              new Date(revenue.periodEnd),
              revenue.amount,
              revenue.source,
              revenue.category,
              revenue.externalId,
              new Date(revenue.createdAt),
              new Date(revenue.updatedAt),
              JSON.stringify(revenue.metadata || {})
            ]);
            
            result.added++;
          }
        } catch (error) {
          logger.error(`Error processing revenue entry ${revenue.externalId}:`, error);
          result.errors++;
        }
      }
      
      logger.info(`Completed revenue sync for ${organizationName}`, result);
      return result;
    } catch (error) {
      logger.error(`Error syncing revenue for ${organizationName}:`, error);
      throw error;
    }
  }
  
  /**
   * Create business metrics from the synced data
   * @param {string} organizationId - The organization ID
   * @param {string} organizationName - The organization name
   * @returns {Promise<void>}
   */
  async createBusinessMetrics(organizationId, organizationName) {
    try {
      logger.info(`Creating business metrics for ${organizationName}`);
      
      // Get current date for period calculations
      const now = new Date();
      const currentMonth = now.getMonth();
      const currentYear = now.getFullYear();
      
      // Calculate period start/end for current month
      const periodStart = new Date(currentYear, currentMonth, 1);
      const periodEnd = new Date(currentYear, currentMonth + 1, 0);
      
      // Calculate total revenue for current month
      const revenueResult = await db.tenantQuery(organizationName, `
        SELECT SUM(amount) as total_revenue
        FROM am_consulting_revenue
        WHERE period_start >= ? AND period_end <= ?
      `, [periodStart, periodEnd]);
      
      const totalRevenue = revenueResult[0]?.total_revenue || 0;
      
      // Calculate previous month's revenue for comparison
      const prevPeriodStart = new Date(currentYear, currentMonth - 1, 1);
      const prevPeriodEnd = new Date(currentYear, currentMonth, 0);
      
      const prevRevenueResult = await db.tenantQuery(organizationName, `
        SELECT SUM(amount) as total_revenue
        FROM am_consulting_revenue
        WHERE period_start >= ? AND period_end <= ?
      `, [prevPeriodStart, prevPeriodEnd]);
      
      const prevTotalRevenue = prevRevenueResult[0]?.total_revenue || 0;
      
      // Calculate target revenue (example: 10% increase from previous month)
      const targetRevenue = prevTotalRevenue * 1.1;
      
      // Insert revenue metric
      await db.tenantQuery(organizationName, `
        INSERT INTO business_metrics (
          metric_category, metric_name, metric_value, metric_unit,
          target_value, period_start, period_end, metadata
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
      `, [
        'financial',
        'monthly_revenue',
        totalRevenue,
        'currency',
        targetRevenue,
        periodStart,
        periodEnd,
        JSON.stringify({
          source: 'am_consulting_integration',
          previousValue: prevTotalRevenue,
          changePercentage: prevTotalRevenue > 0 ? ((totalRevenue - prevTotalRevenue) / prevTotalRevenue) * 100 : 0
        })
      ]);
      
      // Count active practitioners
      const practitionersResult = await db.tenantQuery(organizationName, `
        SELECT COUNT(*) as active_practitioners
        FROM am_consulting_practitioners
        WHERE status = 'active'
      `);
      
      const activePractitioners = practitionersResult[0]?.active_practitioners || 0;
      
      // Insert practitioners metric
      await db.tenantQuery(organizationName, `
        INSERT INTO business_metrics (
          metric_category, metric_name, metric_value, metric_unit,
          target_value, period_start, period_end, metadata
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
      `, [
        'operations',
        'active_practitioners',
        activePractitioners,
        'number',
        null,
        periodStart,
        periodEnd,
        JSON.stringify({
          source: 'am_consulting_integration'
        })
      ]);
      
      // Count open conflicts
      const conflictsResult = await db.tenantQuery(organizationName, `
        SELECT 
          COUNT(*) as total_conflicts,
          SUM(CASE WHEN status = 'open' THEN 1 ELSE 0 END) as open_conflicts,
          SUM(CASE WHEN status = 'resolved' THEN 1 ELSE 0 END) as resolved_conflicts
      `);
      
      const openConflicts = conflictsResult[0]?.open_conflicts || 0;
      const totalConflicts = conflictsResult[0]?.total_conflicts || 0;
      
      // Insert conflicts metric
      await db.tenantQuery(organizationName, `
        INSERT INTO business_metrics (
          metric_category, metric_name, metric_value, metric_unit,
          target_value, period_start, period_end, metadata
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
      `, [
        'operations',
        'open_conflicts',
        openConflicts,
        'number',
        0, // Target is always 0 open conflicts
        periodStart,
        periodEnd,
        JSON.stringify({
          source: 'am_consulting_integration',
          totalConflicts,
          resolvedConflicts: conflictsResult[0]?.resolved_conflicts || 0,
          resolutionRate: totalConflicts > 0 ? 
            ((totalConflicts - openConflicts) / totalConflicts) * 100 : 0
        })
      ]);
      
      logger.info(`Created business metrics for ${organizationName}`);
    } catch (error) {
      logger.error(`Error creating business metrics for ${organizationName}:`, error);
      throw error;
    }
  }
  
  /**
   * Test the integration connection
   * @param {string} organizationId - The organization ID
   * @param {Object} config - Integration configuration to test
   * @returns {Promise<Object>} - Test results
   */
  async testConnection(organizationId, config = {}) {
    try {
      logger.info(`Testing A.M. Consulting integration for organization ${organizationId}`);
      
      // In a real implementation, this would test the actual API connection
      // For demonstration, we'll simulate a successful connection
      
      return {
        success: true,
        message: 'Successfully connected to A.M. Consulting API',
        details: {
          apiVersion: '2.1.0',
          endpoints: ['conflicts', 'practitioners', 'revenue'],
          permissions: ['read', 'write']
        }
      };
    } catch (error) {
      logger.error('Error testing A.M. Consulting integration:', error);
      throw error;
    }
  }
  
  /**
   * Fetch mock conflicts data for demonstration
   * @returns {Promise<Array>} - Mock conflicts data
   */
  async fetchMockConflicts() {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 200));
    
    return [
      {
        id: 'c1',
        title: 'Schedule conflict between practitioners',
        description: 'Two practitioners scheduled for the same room at overlapping times',
        status: 'open',
        priority: 'high',
        assignedTo: 'Sarah Johnson',
        externalId: 'CONF-001',
        externalUrl: 'https://am-consulting.example.com/conflicts/CONF-001',
        createdAt: '2025-06-15T10:30:00Z',
        updatedAt: '2025-06-15T14:45:00Z',
        metadata: {
          room: 'Conference Room A',
          practitioners: ['Dr. Smith', 'Dr. Jones'],
          timeSlot: '2025-06-20 14:00-15:30'
        }
      },
      {
        id: 'c2',
        title: 'Client billing dispute',
        description: 'Client claims they were overcharged for services',
        status: 'open',
        priority: 'medium',
        assignedTo: 'Michael Chen',
        externalId: 'CONF-002',
        externalUrl: 'https://am-consulting.example.com/conflicts/CONF-002',
        createdAt: '2025-06-10T09:15:00Z',
        updatedAt: '2025-06-14T11:20:00Z',
        metadata: {
          client: 'Acme Corp',
          invoiceNumber: 'INV-2025-0342',
          amount: 1250.00,
          disputedAmount: 450.00
        }
      },
      {
        id: 'c3',
        title: 'Resource allocation issue',
        description: 'Not enough consultation rooms available for scheduled sessions',
        status: 'resolved',
        priority: 'high',
        assignedTo: 'Emma Wilson',
        externalId: 'CONF-003',
        externalUrl: 'https://am-consulting.example.com/conflicts/CONF-003',
        createdAt: '2025-06-05T13:45:00Z',
        updatedAt: '2025-06-12T16:30:00Z',
        metadata: {
          date: '2025-06-18',
          requiredRooms: 5,
          availableRooms: 3,
          resolution: 'Two virtual sessions scheduled instead'
        }
      }
    ];
  }
  
  /**
   * Fetch mock practitioners data for demonstration
   * @returns {Promise<Array>} - Mock practitioners data
   */
  async fetchMockPractitioners() {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 200));
    
    return [
      {
        id: 'p1',
        name: 'Dr. Sarah Johnson',
        specialty: 'Conflict Resolution',
        availability: {
          monday: ['9:00-12:00', '13:00-17:00'],
          tuesday: ['9:00-12:00', '13:00-17:00'],
          wednesday: ['9:00-12:00'],
          thursday: ['13:00-17:00'],
          friday: ['9:00-12:00', '13:00-17:00']
        },
        hourlyRate: 150.00,
        status: 'active',
        externalId: 'PRAC-001',
        externalUrl: 'https://am-consulting.example.com/practitioners/PRAC-001',
        createdAt: '2024-01-15T10:30:00Z',
        updatedAt: '2025-05-20T14:45:00Z',
        metadata: {
          certifications: ['Certified Mediator', 'Conflict Resolution Specialist'],
          languages: ['English', 'Spanish'],
          rating: 4.9
        }
      },
      {
        id: 'p2',
        name: 'Michael Chen',
        specialty: 'Business Mediation',
        availability: {
          monday: ['9:00-17:00'],
          wednesday: ['9:00-17:00'],
          friday: ['9:00-17:00']
        },
        hourlyRate: 175.00,
        status: 'active',
        externalId: 'PRAC-002',
        externalUrl: 'https://am-consulting.example.com/practitioners/PRAC-002',
        createdAt: '2024-02-10T09:15:00Z',
        updatedAt: '2025-06-01T11:20:00Z',
        metadata: {
          certifications: ['MBA', 'Certified Business Mediator'],
          languages: ['English', 'Mandarin'],
          rating: 4.8
        }
      },
      {
        id: 'p3',
        name: 'Emma Wilson',
        specialty: 'Family Mediation',
        availability: {
          tuesday: ['9:00-17:00'],
          thursday: ['9:00-17:00']
        },
        hourlyRate: 140.00,
        status: 'active',
        externalId: 'PRAC-003',
        externalUrl: 'https://am-consulting.example.com/practitioners/PRAC-003',
        createdAt: '2024-03-05T13:45:00Z',
        updatedAt: '2025-05-15T16:30:00Z',
        metadata: {
          certifications: ['Family Mediation Specialist', 'Child Welfare Advocate'],
          languages: ['English', 'French'],
          rating: 4.7
        }
      },
      {
        id: 'p4',
        name: 'Dr. James Rodriguez',
        specialty: 'Workplace Conflict',
        availability: {
          monday: ['13:00-17:00'],
          wednesday: ['9:00-17:00'],
          friday: ['9:00-12:00']
        },
        hourlyRate: 160.00,
        status: 'inactive',
        externalId: 'PRAC-004',
        externalUrl: 'https://am-consulting.example.com/practitioners/PRAC-004',
        createdAt: '2024-04-20T11:30:00Z',
        updatedAt: '2025-06-10T09:45:00Z',
        metadata: {
          certifications: ['Organizational Psychology PhD', 'Workplace Mediator'],
          languages: ['English', 'Portuguese'],
          rating: 4.6,
          inactiveReason: 'Sabbatical until 2025-09-01'
        }
      }
    ];
  }
  
  /**
   * Fetch mock revenue data for demonstration
   * @returns {Promise<Array>} - Mock revenue data
   */
  async fetchMockRevenue() {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 200));
    
    return [
      {
        periodStart: '2025-06-01',
        periodEnd: '2025-06-30',
        amount: 45250.00,
        source: 'Consulting Services',
        category: 'Business',
        externalId: 'REV-2025-06-BUS',
        createdAt: '2025-06-30T23:59:59Z',
        updatedAt: '2025-06-30T23:59:59Z',
        metadata: {
          clients: 12,
          sessions: 68,
          avgSessionValue: 665.44
        }
      },
      {
        periodStart: '2025-06-01',
        periodEnd: '2025-06-30',
        amount: 28750.00,
        source: 'Consulting Services',
        category: 'Family',
        externalId: 'REV-2025-06-FAM',
        createdAt: '2025-06-30T23:59:59Z',
        updatedAt: '2025-06-30T23:59:59Z',
        metadata: {
          clients: 15,
          sessions: 45,
          avgSessionValue: 638.89
        }
      },
      {
        periodStart: '2025-06-01',
        periodEnd: '2025-06-30',
        amount: 32500.00,
        source: 'Consulting Services',
        category: 'Workplace',
        externalId: 'REV-2025-06-WRK',
        createdAt: '2025-06-30T23:59:59Z',
        updatedAt: '2025-06-30T23:59:59Z',
        metadata: {
          clients: 8,
          sessions: 40,
          avgSessionValue: 812.50
        }
      },
      {
        periodStart: '2025-05-01',
        periodEnd: '2025-05-31',
        amount: 42800.00,
        source: 'Consulting Services',
        category: 'Business',
        externalId: 'REV-2025-05-BUS',
        createdAt: '2025-05-31T23:59:59Z',
        updatedAt: '2025-05-31T23:59:59Z',
        metadata: {
          clients: 11,
          sessions: 64,
          avgSessionValue: 668.75
        }
      },
      {
        periodStart: '2025-05-01',
        periodEnd: '2025-05-31',
        amount: 26400.00,
        source: 'Consulting Services',
        category: 'Family',
        externalId: 'REV-2025-05-FAM',
        createdAt: '2025-05-31T23:59:59Z',
        updatedAt: '2025-05-31T23:59:59Z',
        metadata: {
          clients: 14,
          sessions: 42,
          avgSessionValue: 628.57
        }
      },
      {
        periodStart: '2025-05-01',
        periodEnd: '2025-05-31',
        amount: 30800.00,
        source: 'Consulting Services',
        category: 'Workplace',
        externalId: 'REV-2025-05-WRK',
        createdAt: '2025-05-31T23:59:59Z',
        updatedAt: '2025-05-31T23:59:59Z',
        metadata: {
          clients: 7,
          sessions: 38,
          avgSessionValue: 810.53
        }
      }
    ];
  }
}

module.exports = new AMConsultingIntegrationService();

