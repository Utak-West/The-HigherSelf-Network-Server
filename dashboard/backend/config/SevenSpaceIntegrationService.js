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
 * The 7 Space Integration Service
 * Handles integration with The 7 Space's systems for exhibitions,
 * wellness programs, events, and visitor analytics.
 */
class SevenSpaceIntegrationService {
  constructor() {
    this.baseUrl = process.env.SEVEN_SPACE_API_URL;
    this.apiKey = process.env.SEVEN_SPACE_API_KEY;
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
      logger.info(`Initializing The 7 Space integration for organization ${organizationId}`);
      
      // Get organization name for tenant operations
      const organizations = await db.query('SELECT name FROM organizations WHERE id = ?', [organizationId]);
      if (organizations.length === 0) {
        throw new AppError('Organization not found', 404);
      }
      
      const organizationName = organizations[0].name;
      
      // Check if integration already exists
      const existingIntegrations = await db.tenantQuery(organizationName, `
        SELECT id FROM integrations 
        WHERE service_name = 'seven_space' AND is_active = 1
      `);
      
      if (existingIntegrations.length > 0) {
        throw new AppError('The 7 Space integration already exists for this organization', 409);
      }
      
      // Create integration record
      const integrationConfig = {
        apiUrl: config.apiUrl || this.baseUrl,
        apiKey: config.apiKey || this.apiKey,
        syncSchedule: config.syncSchedule || '0 0 * * *', // Default: daily at midnight
        syncEnabled: config.syncEnabled !== undefined ? config.syncEnabled : true,
        dataMapping: config.dataMapping || {
          exhibitions: {
            enabled: true,
            fields: ['id', 'title', 'description', 'startDate', 'endDate', 'status', 'artist', 'location']
          },
          events: {
            enabled: true,
            fields: ['id', 'title', 'description', 'startDate', 'endDate', 'type', 'capacity', 'registrations']
          },
          wellnessPrograms: {
            enabled: true,
            fields: ['id', 'name', 'description', 'instructor', 'schedule', 'capacity', 'participants']
          },
          visitors: {
            enabled: true,
            fields: ['date', 'count', 'demographics', 'source', 'feedback']
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
        'seven_space',
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
        message: 'The 7 Space integration initialized successfully'
      };
    } catch (error) {
      logger.error('Error initializing The 7 Space integration:', error);
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
      // Create exhibitions table
      await db.tenantQuery(organizationName, `
        CREATE TABLE IF NOT EXISTS seven_space_exhibitions (
          id VARCHAR(36) PRIMARY KEY,
          title VARCHAR(255) NOT NULL,
          description TEXT,
          artist VARCHAR(255),
          start_date DATE NOT NULL,
          end_date DATE NOT NULL,
          status VARCHAR(50) NOT NULL,
          location VARCHAR(100),
          ticket_price DECIMAL(10, 2),
          attendance INT,
          external_id VARCHAR(100),
          external_url VARCHAR(255),
          created_at TIMESTAMP NOT NULL,
          updated_at TIMESTAMP NOT NULL,
          synced_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
          metadata JSON
        )
      `);
      
      // Create events table
      await db.tenantQuery(organizationName, `
        CREATE TABLE IF NOT EXISTS seven_space_events (
          id VARCHAR(36) PRIMARY KEY,
          title VARCHAR(255) NOT NULL,
          description TEXT,
          start_date DATETIME NOT NULL,
          end_date DATETIME NOT NULL,
          type VARCHAR(50) NOT NULL,
          capacity INT,
          registrations INT,
          location VARCHAR(100),
          ticket_price DECIMAL(10, 2),
          external_id VARCHAR(100),
          external_url VARCHAR(255),
          created_at TIMESTAMP NOT NULL,
          updated_at TIMESTAMP NOT NULL,
          synced_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
          metadata JSON
        )
      `);
      
      // Create wellness programs table
      await db.tenantQuery(organizationName, `
        CREATE TABLE IF NOT EXISTS seven_space_wellness_programs (
          id VARCHAR(36) PRIMARY KEY,
          name VARCHAR(255) NOT NULL,
          description TEXT,
          instructor VARCHAR(100),
          schedule JSON,
          capacity INT,
          participants INT,
          status VARCHAR(50) NOT NULL,
          external_id VARCHAR(100),
          external_url VARCHAR(255),
          created_at TIMESTAMP NOT NULL,
          updated_at TIMESTAMP NOT NULL,
          synced_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
          metadata JSON
        )
      `);
      
      // Create visitors table
      await db.tenantQuery(organizationName, `
        CREATE TABLE IF NOT EXISTS seven_space_visitors (
          id INT AUTO_INCREMENT PRIMARY KEY,
          date DATE NOT NULL,
          count INT NOT NULL,
          demographics JSON,
          source VARCHAR(50),
          feedback_score DECIMAL(3, 2),
          external_id VARCHAR(100),
          created_at TIMESTAMP NOT NULL,
          updated_at TIMESTAMP NOT NULL,
          synced_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
          metadata JSON
        )
      `);
      
      logger.info(`Created The 7 Space integration tables for organization ${organizationName}`);
    } catch (error) {
      logger.error(`Error creating integration tables for ${organizationName}:`, error);
      throw error;
    }
  }
  
  /**
   * Sync data from The 7 Space API
   * @param {string} organizationId - The organization ID
   * @param {number} integrationId - The integration ID
   * @returns {Promise<Object>} - Sync results
   */
  async syncData(organizationId, integrationId) {
    try {
      logger.info(`Starting The 7 Space data sync for organization ${organizationId}, integration ${integrationId}`);
      
      // Get organization name for tenant operations
      const organizations = await db.query('SELECT name FROM organizations WHERE id = ?', [organizationId]);
      if (organizations.length === 0) {
        throw new AppError('Organization not found', 404);
      }
      
      const organizationName = organizations[0].name;
      
      // Get integration config
      const integrations = await db.tenantQuery(organizationName, `
        SELECT id, config FROM integrations 
        WHERE id = ? AND service_name = 'seven_space' AND is_active = 1
      `, [integrationId]);
      
      if (integrations.length === 0) {
        throw new AppError('Active The 7 Space integration not found', 404);
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
        exhibitions: { added: 0, updated: 0, errors: 0 },
        events: { added: 0, updated: 0, errors: 0 },
        wellnessPrograms: { added: 0, updated: 0, errors: 0 },
        visitors: { added: 0, updated: 0, errors: 0 }
      };
      
      // Sync exhibitions if enabled
      if (config.dataMapping.exhibitions?.enabled) {
        try {
          const exhibitionsResult = await this.syncExhibitions(organizationName, config);
          syncResults.exhibitions = exhibitionsResult;
        } catch (error) {
          logger.error(`Error syncing exhibitions for ${organizationName}:`, error);
          syncResults.exhibitions.errors++;
        }
      }
      
      // Sync events if enabled
      if (config.dataMapping.events?.enabled) {
        try {
          const eventsResult = await this.syncEvents(organizationName, config);
          syncResults.events = eventsResult;
        } catch (error) {
          logger.error(`Error syncing events for ${organizationName}:`, error);
          syncResults.events.errors++;
        }
      }
      
      // Sync wellness programs if enabled
      if (config.dataMapping.wellnessPrograms?.enabled) {
        try {
          const wellnessProgramsResult = await this.syncWellnessPrograms(organizationName, config);
          syncResults.wellnessPrograms = wellnessProgramsResult;
        } catch (error) {
          logger.error(`Error syncing wellness programs for ${organizationName}:`, error);
          syncResults.wellnessPrograms.errors++;
        }
      }
      
      // Sync visitors if enabled
      if (config.dataMapping.visitors?.enabled) {
        try {
          const visitorsResult = await this.syncVisitors(organizationName, config);
          syncResults.visitors = visitorsResult;
        } catch (error) {
          logger.error(`Error syncing visitors for ${organizationName}:`, error);
          syncResults.visitors.errors++;
        }
      }
      
      // Calculate total metrics
      const totalAdded = 
        syncResults.exhibitions.added + 
        syncResults.events.added + 
        syncResults.wellnessPrograms.added + 
        syncResults.visitors.added;
      
      const totalUpdated = 
        syncResults.exhibitions.updated + 
        syncResults.events.updated + 
        syncResults.wellnessPrograms.updated + 
        syncResults.visitors.updated;
      
      const totalErrors = 
        syncResults.exhibitions.errors + 
        syncResults.events.errors + 
        syncResults.wellnessPrograms.errors + 
        syncResults.visitors.errors;
      
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
      
      logger.info(`Completed The 7 Space data sync for organization ${organizationId}`, {
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
      logger.error(`Error during The 7 Space data sync for organization ${organizationId}:`, error);
      
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
   * Sync exhibitions data
   * @param {string} organizationName - The organization name
   * @param {Object} config - Integration configuration
   * @returns {Promise<Object>} - Sync results
   */
  async syncExhibitions(organizationName, config) {
    try {
      logger.info(`Syncing exhibitions for ${organizationName}`);
      
      // In a real implementation, this would call the actual API
      // For demonstration, we'll simulate API data
      const exhibitions = await this.fetchMockExhibitions();
      
      const result = { added: 0, updated: 0, errors: 0 };
      
      // Process each exhibition
      for (const exhibition of exhibitions) {
        try {
          // Check if exhibition already exists
          const existingExhibitions = await db.tenantQuery(organizationName, `
            SELECT id FROM seven_space_exhibitions WHERE id = ?
          `, [exhibition.id]);
          
          if (existingExhibitions.length > 0) {
            // Update existing exhibition
            await db.tenantQuery(organizationName, `
              UPDATE seven_space_exhibitions
              SET 
                title = ?,
                description = ?,
                artist = ?,
                start_date = ?,
                end_date = ?,
                status = ?,
                location = ?,
                ticket_price = ?,
                attendance = ?,
                external_id = ?,
                external_url = ?,
                updated_at = ?,
                synced_at = CURRENT_TIMESTAMP,
                metadata = ?
              WHERE id = ?
            `, [
              exhibition.title,
              exhibition.description,
              exhibition.artist,
              new Date(exhibition.startDate),
              new Date(exhibition.endDate),
              exhibition.status,
              exhibition.location,
              exhibition.ticketPrice,
              exhibition.attendance,
              exhibition.externalId,
              exhibition.externalUrl,
              new Date(exhibition.updatedAt),
              JSON.stringify(exhibition.metadata || {}),
              exhibition.id
            ]);
            
            result.updated++;
          } else {
            // Insert new exhibition
            await db.tenantQuery(organizationName, `
              INSERT INTO seven_space_exhibitions (
                id, title, description, artist, start_date, end_date, status, location,
                ticket_price, attendance, external_id, external_url, created_at, updated_at, 
                synced_at, metadata
              ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
            `, [
              exhibition.id,
              exhibition.title,
              exhibition.description,
              exhibition.artist,
              new Date(exhibition.startDate),
              new Date(exhibition.endDate),
              exhibition.status,
              exhibition.location,
              exhibition.ticketPrice,
              exhibition.attendance,
              exhibition.externalId,
              exhibition.externalUrl,
              new Date(exhibition.createdAt),
              new Date(exhibition.updatedAt),
              JSON.stringify(exhibition.metadata || {})
            ]);
            
            result.added++;
          }
        } catch (error) {
          logger.error(`Error processing exhibition ${exhibition.id}:`, error);
          result.errors++;
        }
      }
      
      logger.info(`Completed exhibitions sync for ${organizationName}`, result);
      return result;
    } catch (error) {
      logger.error(`Error syncing exhibitions for ${organizationName}:`, error);
      throw error;
    }
  }
  
  /**
   * Sync events data
   * @param {string} organizationName - The organization name
   * @param {Object} config - Integration configuration
   * @returns {Promise<Object>} - Sync results
   */
  async syncEvents(organizationName, config) {
    try {
      logger.info(`Syncing events for ${organizationName}`);
      
      // In a real implementation, this would call the actual API
      // For demonstration, we'll simulate API data
      const events = await this.fetchMockEvents();
      
      const result = { added: 0, updated: 0, errors: 0 };
      
      // Process each event
      for (const event of events) {
        try {
          // Check if event already exists
          const existingEvents = await db.tenantQuery(organizationName, `
            SELECT id FROM seven_space_events WHERE id = ?
          `, [event.id]);
          
          if (existingEvents.length > 0) {
            // Update existing event
            await db.tenantQuery(organizationName, `
              UPDATE seven_space_events
              SET 
                title = ?,
                description = ?,
                start_date = ?,
                end_date = ?,
                type = ?,
                capacity = ?,
                registrations = ?,
                location = ?,
                ticket_price = ?,
                external_id = ?,
                external_url = ?,
                updated_at = ?,
                synced_at = CURRENT_TIMESTAMP,
                metadata = ?
              WHERE id = ?
            `, [
              event.title,
              event.description,
              new Date(event.startDate),
              new Date(event.endDate),
              event.type,
              event.capacity,
              event.registrations,
              event.location,
              event.ticketPrice,
              event.externalId,
              event.externalUrl,
              new Date(event.updatedAt),
              JSON.stringify(event.metadata || {}),
              event.id
            ]);
            
            result.updated++;
          } else {
            // Insert new event
            await db.tenantQuery(organizationName, `
              INSERT INTO seven_space_events (
                id, title, description, start_date, end_date, type, capacity,
                registrations, location, ticket_price, external_id, external_url, 
                created_at, updated_at, synced_at, metadata
              ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
            `, [
              event.id,
              event.title,
              event.description,
              new Date(event.startDate),
              new Date(event.endDate),
              event.type,
              event.capacity,
              event.registrations,
              event.location,
              event.ticketPrice,
              event.externalId,
              event.externalUrl,
              new Date(event.createdAt),
              new Date(event.updatedAt),
              JSON.stringify(event.metadata || {})
            ]);
            
            result.added++;
          }
        } catch (error) {
          logger.error(`Error processing event ${event.id}:`, error);
          result.errors++;
        }
      }
      
      logger.info(`Completed events sync for ${organizationName}`, result);
      return result;
    } catch (error) {
      logger.error(`Error syncing events for ${organizationName}:`, error);
      throw error;
    }
  }
  
  /**
   * Sync wellness programs data
   * @param {string} organizationName - The organization name
   * @param {Object} config - Integration configuration
   * @returns {Promise<Object>} - Sync results
   */
  async syncWellnessPrograms(organizationName, config) {
    try {
      logger.info(`Syncing wellness programs for ${organizationName}`);
      
      // In a real implementation, this would call the actual API
      // For demonstration, we'll simulate API data
      const programs = await this.fetchMockWellnessPrograms();
      
      const result = { added: 0, updated: 0, errors: 0 };
      
      // Process each wellness program
      for (const program of programs) {
        try {
          // Check if program already exists
          const existingPrograms = await db.tenantQuery(organizationName, `
            SELECT id FROM seven_space_wellness_programs WHERE id = ?
          `, [program.id]);
          
          if (existingPrograms.length > 0) {
            // Update existing program
            await db.tenantQuery(organizationName, `
              UPDATE seven_space_wellness_programs
              SET 
                name = ?,
                description = ?,
                instructor = ?,
                schedule = ?,
                capacity = ?,
                participants = ?,
                status = ?,
                external_id = ?,
                external_url = ?,
                updated_at = ?,
                synced_at = CURRENT_TIMESTAMP,
                metadata = ?
              WHERE id = ?
            `, [
              program.name,
              program.description,
              program.instructor,
              JSON.stringify(program.schedule || {}),
              program.capacity,
              program.participants,
              program.status,
              program.externalId,
              program.externalUrl,
              new Date(program.updatedAt),
              JSON.stringify(program.metadata || {}),
              program.id
            ]);
            
            result.updated++;
          } else {
            // Insert new program
            await db.tenantQuery(organizationName, `
              INSERT INTO seven_space_wellness_programs (
                id, name, description, instructor, schedule, capacity,
                participants, status, external_id, external_url, 
                created_at, updated_at, synced_at, metadata
              ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
            `, [
              program.id,
              program.name,
              program.description,
              program.instructor,
              JSON.stringify(program.schedule || {}),
              program.capacity,
              program.participants,
              program.status,
              program.externalId,
              program.externalUrl,
              new Date(program.createdAt),
              new Date(program.updatedAt),
              JSON.stringify(program.metadata || {})
            ]);
            
            result.added++;
          }
        } catch (error) {
          logger.error(`Error processing wellness program ${program.id}:`, error);
          result.errors++;
        }
      }
      
      logger.info(`Completed wellness programs sync for ${organizationName}`, result);
      return result;
    } catch (error) {
      logger.error(`Error syncing wellness programs for ${organizationName}:`, error);
      throw error;
    }
  }
  
  /**
   * Sync visitors data
   * @param {string} organizationName - The organization name
   * @param {Object} config - Integration configuration
   * @returns {Promise<Object>} - Sync results
   */
  async syncVisitors(organizationName, config) {
    try {
      logger.info(`Syncing visitors for ${organizationName}`);
      
      // In a real implementation, this would call the actual API
      // For demonstration, we'll simulate API data
      const visitorsData = await this.fetchMockVisitors();
      
      const result = { added: 0, updated: 0, errors: 0 };
      
      // Process each visitor entry
      for (const visitor of visitorsData) {
        try {
          // Check if visitor entry already exists by external ID
          const existingVisitors = await db.tenantQuery(organizationName, `
            SELECT id FROM seven_space_visitors WHERE external_id = ?
          `, [visitor.externalId]);
          
          if (existingVisitors.length > 0) {
            // Update existing visitor entry
            await db.tenantQuery(organizationName, `
              UPDATE seven_space_visitors
              SET 
                date = ?,
                count = ?,
                demographics = ?,
                source = ?,
                feedback_score = ?,
                updated_at = ?,
                synced_at = CURRENT_TIMESTAMP,
                metadata = ?
              WHERE external_id = ?
            `, [
              new Date(visitor.date),
              visitor.count,
              JSON.stringify(visitor.demographics || {}),
              visitor.source,
              visitor.feedbackScore,
              new Date(visitor.updatedAt),
              JSON.stringify(visitor.metadata || {}),
              visitor.externalId
            ]);
            
            result.updated++;
          } else {
            // Insert new visitor entry
            await db.tenantQuery(organizationName, `
              INSERT INTO seven_space_visitors (
                date, count, demographics, source, feedback_score,
                external_id, created_at, updated_at, synced_at, metadata
              ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
            `, [
              new Date(visitor.date),
              visitor.count,
              JSON.stringify(visitor.demographics || {}),
              visitor.source,
              visitor.feedbackScore,
              visitor.externalId,
              new Date(visitor.createdAt),
              new Date(visitor.updatedAt),
              JSON.stringify(visitor.metadata || {})
            ]);
            
            result.added++;
          }
        } catch (error) {
          logger.error(`Error processing visitor entry ${visitor.externalId}:`, error);
          result.errors++;
        }
      }
      
      logger.info(`Completed visitors sync for ${organizationName}`, result);
      return result;
    } catch (error) {
      logger.error(`Error syncing visitors for ${organizationName}:`, error);
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
      
      // Calculate total visitors for current month
      const visitorsResult = await db.tenantQuery(organizationName, `
        SELECT SUM(count) as total_visitors
        FROM seven_space_visitors
        WHERE date >= ? AND date <= ?
      `, [periodStart, periodEnd]);
      
      const totalVisitors = visitorsResult[0]?.total_visitors || 0;
      
      // Calculate previous month's visitors for comparison
      const prevPeriodStart = new Date(currentYear, currentMonth - 1, 1);
      const prevPeriodEnd = new Date(currentYear, currentMonth, 0);
      
      const prevVisitorsResult = await db.tenantQuery(organizationName, `
        SELECT SUM(count) as total_visitors
        FROM seven_space_visitors
        WHERE date >= ? AND date <= ?
      `, [prevPeriodStart, prevPeriodEnd]);
      
      const prevTotalVisitors = prevVisitorsResult[0]?.total_visitors || 0;
      
      // Calculate target visitors (example: 10% increase from previous month)
      const targetVisitors = prevTotalVisitors * 1.1;
      
      // Insert visitors metric
      await db.tenantQuery(organizationName, `
        INSERT INTO business_metrics (
          metric_category, metric_name, metric_value, metric_unit,
          target_value, period_start, period_end, metadata
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
      `, [
        'operations',
        'monthly_visitors',
        totalVisitors,
        'number',
        targetVisitors,
        periodStart,
        periodEnd,
        JSON.stringify({
          source: 'seven_space_integration',
          previousValue: prevTotalVisitors,
          changePercentage: prevTotalVisitors > 0 ? ((totalVisitors - prevTotalVisitors) / prevTotalVisitors) * 100 : 0
        })
      ]);
      
      // Calculate average feedback score
      const feedbackResult = await db.tenantQuery(organizationName, `
        SELECT AVG(feedback_score) as avg_feedback
        FROM seven_space_visitors
        WHERE date >= ? AND date <= ?
      `, [periodStart, periodEnd]);
      
      const avgFeedback = feedbackResult[0]?.avg_feedback || 0;
      
      // Insert feedback metric
      await db.tenantQuery(organizationName, `
        INSERT INTO business_metrics (
          metric_category, metric_name, metric_value, metric_unit,
          target_value, period_start, period_end, metadata
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
      `, [
        'customer',
        'visitor_satisfaction',
        avgFeedback,
        'number',
        4.5, // Target is 4.5 out of 5
        periodStart,
        periodEnd,
        JSON.stringify({
          source: 'seven_space_integration',
          scale: '1-5'
        })
      ]);
      
      // Count active exhibitions
      const exhibitionsResult = await db.tenantQuery(organizationName, `
        SELECT 
          COUNT(*) as total_exhibitions,
          SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active_exhibitions,
          SUM(attendance) as total_attendance
        FROM seven_space_exhibitions
        WHERE (start_date <= ? AND end_date >= ?)
      `, [periodEnd, periodStart]);
      
      const activeExhibitions = exhibitionsResult[0]?.active_exhibitions || 0;
      const totalAttendance = exhibitionsResult[0]?.total_attendance || 0;
      
      // Insert exhibitions metric
      await db.tenantQuery(organizationName, `
        INSERT INTO business_metrics (
          metric_category, metric_name, metric_value, metric_unit,
          target_value, period_start, period_end, metadata
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
      `, [
        'operations',
        'active_exhibitions',
        activeExhibitions,
        'number',
        null,
        periodStart,
        periodEnd,
        JSON.stringify({
          source: 'seven_space_integration',
          totalAttendance
        })
      ]);
      
      // Count upcoming events
      const eventsResult = await db.tenantQuery(organizationName, `
        SELECT 
          COUNT(*) as total_events,
          SUM(CASE WHEN start_date >= ? THEN 1 ELSE 0 END) as upcoming_events,
          SUM(registrations) as total_registrations
        FROM seven_space_events
        WHERE start_date >= ?
      `, [now, periodStart]);
      
      const upcomingEvents = eventsResult[0]?.upcoming_events || 0;
      const totalRegistrations = eventsResult[0]?.total_registrations || 0;
      
      // Insert events metric
      await db.tenantQuery(organizationName, `
        INSERT INTO business_metrics (
          metric_category, metric_name, metric_value, metric_unit,
          target_value, period_start, period_end, metadata
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
      `, [
        'operations',
        'upcoming_events',
        upcomingEvents,
        'number',
        null,
        periodStart,
        periodEnd,
        JSON.stringify({
          source: 'seven_space_integration',
          totalRegistrations
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
      logger.info(`Testing The 7 Space integration for organization ${organizationId}`);
      
      // In a real implementation, this would test the actual API connection
      // For demonstration, we'll simulate a successful connection
      
      return {
        success: true,
        message: 'Successfully connected to The 7 Space API',
        details: {
          apiVersion: '1.5.2',
          endpoints: ['exhibitions', 'events', 'wellness-programs', 'visitors'],
          permissions: ['read', 'write']
        }
      };
    } catch (error) {
      logger.error('Error testing The 7 Space integration:', error);
      throw error;
    }
  }
  
  /**
   * Fetch mock exhibitions data for demonstration
   * @returns {Promise<Array>} - Mock exhibitions data
   */
  async fetchMockExhibitions() {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 200));
    
    return [
      {
        id: 'e1',
        title: 'Harmony in Chaos: Modern Art Exhibition',
        description: 'An exploration of order within disorder through contemporary art pieces',
        artist: 'Various Artists',
        startDate: '2025-06-01',
        endDate: '2025-07-15',
        status: 'active',
        location: 'Main Gallery',
        ticketPrice: 15.00,
        attendance: 1250,
        externalId: 'EXH-2025-001',
        externalUrl: 'https://7space.example.com/exhibitions/EXH-2025-001',
        createdAt: '2025-04-15T10:30:00Z',
        updatedAt: '2025-06-02T14:45:00Z',
        metadata: {
          featuredArtists: ['Maya Johnson', 'Takashi Mori', 'Elena Vasquez'],
          categories: ['Contemporary', 'Mixed Media', 'Installation'],
          sponsors: ['ArtTech Foundation', 'City Arts Council']
        }
      },
      {
        id: 'e2',
        title: 'Digital Frontiers: NFT Showcase',
        description: 'Exploring the intersection of blockchain technology and creative expression',
        artist: 'Collective Digital Artists',
        startDate: '2025-06-20',
        endDate: '2025-08-10',
        status: 'upcoming',
        location: 'Tech Gallery',
        ticketPrice: 20.00,
        attendance: 0,
        externalId: 'EXH-2025-002',
        externalUrl: 'https://7space.example.com/exhibitions/EXH-2025-002',
        createdAt: '2025-05-10T09:15:00Z',
        updatedAt: '2025-06-01T11:20:00Z',
        metadata: {
          featuredArtists: ['CryptoCreative', 'BlockchainBrush', 'MetaverseStudio'],
          categories: ['Digital Art', 'NFT', 'Interactive'],
          sponsors: ['CryptoArt Foundation', 'BlockTech Ventures']
        }
      },
      {
        id: 'e3',
        title: 'Echoes of Nature: Environmental Photography',
        description: 'A photographic journey through Earth\'s most pristine and endangered landscapes',
        artist: 'James Rodriguez',
        startDate: '2025-05-01',
        endDate: '2025-06-15',
        status: 'completed',
        location: 'West Wing',
        ticketPrice: 12.50,
        attendance: 1850,
        externalId: 'EXH-2025-003',
        externalUrl: 'https://7space.example.com/exhibitions/EXH-2025-003',
        createdAt: '2025-03-05T13:45:00Z',
        updatedAt: '2025-06-16T16:30:00Z',
        metadata: {
          regions: ['Amazon', 'Arctic', 'Sahara', 'Great Barrier Reef'],
          categories: ['Photography', 'Environmental', 'Documentary'],
          sponsors: ['EcoVision Foundation', 'National Geographic']
        }
      }
    ];
  }
  
  /**
   * Fetch mock events data for demonstration
   * @returns {Promise<Array>} - Mock events data
   */
  async fetchMockEvents() {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 200));
    
    return [
      {
        id: 'ev1',
        title: 'Mindfulness Workshop',
        description: 'A guided session on mindfulness practices for daily life',
        startDate: '2025-07-05T14:00:00Z',
        endDate: '2025-07-05T16:00:00Z',
        type: 'workshop',
        capacity: 30,
        registrations: 25,
        location: 'Meditation Room',
        ticketPrice: 25.00,
        externalId: 'EVT-2025-001',
        externalUrl: 'https://7space.example.com/events/EVT-2025-001',
        createdAt: '2025-06-01T10:30:00Z',
        updatedAt: '2025-06-20T14:45:00Z',
        metadata: {
          instructor: 'Dr. Sarah Johnson',
          materials: ['Yoga mat', 'Comfortable clothing'],
          level: 'All levels'
        }
      },
      {
        id: 'ev2',
        title: 'Art & Wine Evening',
        description: 'Enjoy fine wines while creating your own masterpiece',
        startDate: '2025-07-10T18:00:00Z',
        endDate: '2025-07-10T21:00:00Z',
        type: 'social',
        capacity: 40,
        registrations: 38,
        location: 'Creative Studio',
        ticketPrice: 45.00,
        externalId: 'EVT-2025-002',
        externalUrl: 'https://7space.example.com/events/EVT-2025-002',
        createdAt: '2025-06-05T09:15:00Z',
        updatedAt: '2025-06-25T11:20:00Z',
        metadata: {
          host: 'Elena Vasquez',
          includes: ['Canvas', 'Paints', 'Wine tasting (3 varieties)'],
          ageRestriction: '21+'
        }
      },
      {
        id: 'ev3',
        title: 'Tech Talk: AI in Creative Industries',
        description: 'Panel discussion on how artificial intelligence is transforming art and design',
        startDate: '2025-07-15T19:00:00Z',
        endDate: '2025-07-15T21:00:00Z',
        type: 'lecture',
        capacity: 100,
        registrations: 72,
        location: 'Auditorium',
        ticketPrice: 10.00,
        externalId: 'EVT-2025-003',
        externalUrl: 'https://7space.example.com/events/EVT-2025-003',
        createdAt: '2025-06-10T13:45:00Z',
        updatedAt: '2025-06-28T16:30:00Z',
        metadata: {
          speakers: ['Dr. Michael Chen', 'Prof. Aisha Patel', 'Maya Johnson'],
          topics: ['Generative Art', 'AI Collaboration', 'Future of Creativity'],
          sponsors: ['TechArts Initiative', 'AI Creative Labs']
        }
      }
    ];
  }
  
  /**
   * Fetch mock wellness programs data for demonstration
   * @returns {Promise<Array>} - Mock wellness programs data
   */
  async fetchMockWellnessPrograms() {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 200));
    
    return [
      {
        id: 'wp1',
        name: 'Morning Yoga Flow',
        description: 'Start your day with energizing yoga sequences to awaken body and mind',
        instructor: 'Emma Wilson',
        schedule: {
          monday: ['07:00-08:00'],
          wednesday: ['07:00-08:00'],
          friday: ['07:00-08:00']
        },
        capacity: 20,
        participants: 18,
        status: 'active',
        externalId: 'WP-2025-001',
        externalUrl: 'https://7space.example.com/wellness/WP-2025-001',
        createdAt: '2025-01-15T10:30:00Z',
        updatedAt: '2025-06-01T14:45:00Z',
        metadata: {
          level: 'All levels',
          equipment: ['Yoga mat', 'Water bottle'],
          benefits: ['Improved flexibility', 'Stress reduction', 'Energy boost']
        }
      },
      {
        id: 'wp2',
        name: 'Mindful Meditation',
        description: 'Guided meditation sessions focusing on presence and stress reduction',
        instructor: 'David Chen',
        schedule: {
          tuesday: ['12:00-12:45'],
          thursday: ['12:00-12:45']
        },
        capacity: 30,
        participants: 25,
        status: 'active',
        externalId: 'WP-2025-002',
        externalUrl: 'https://7space.example.com/wellness/WP-2025-002',
        createdAt: '2025-01-20T09:15:00Z',
        updatedAt: '2025-06-05T11:20:00Z',
        metadata: {
          level: 'Beginner to intermediate',
          equipment: ['Meditation cushion (optional)'],
          benefits: ['Stress reduction', 'Improved focus', 'Emotional balance']
        }
      },
      {
        id: 'wp3',
        name: 'Sound Bath Healing',
        description: 'Immersive sound experience using singing bowls and gongs for deep relaxation',
        instructor: 'Sophia Martinez',
        schedule: {
          sunday: ['16:00-17:30']
        },
        capacity: 25,
        participants: 22,
        status: 'active',
        externalId: 'WP-2025-003',
        externalUrl: 'https://7space.example.com/wellness/WP-2025-003',
        createdAt: '2025-02-05T13:45:00Z',
        updatedAt: '2025-06-10T16:30:00Z',
        metadata: {
          level: 'All levels',
          equipment: ['Yoga mat', 'Blanket', 'Eye mask (optional)'],
          benefits: ['Deep relaxation', 'Stress relief', 'Improved sleep']
        }
      },
      {
        id: 'wp4',
        name: 'Breathwork Fundamentals',
        description: 'Learn powerful breathing techniques to manage stress and increase vitality',
        instructor: 'James Taylor',
        schedule: {
          monday: ['18:00-19:00'],
          thursday: ['18:00-19:00']
        },
        capacity: 15,
        participants: 12,
        status: 'active',
        externalId: 'WP-2025-004',
        externalUrl: 'https://7space.example.com/wellness/WP-2025-004',
        createdAt: '2025-03-10T11:30:00Z',
        updatedAt: '2025-06-15T09:45:00Z',
        metadata: {
          level: 'All levels',
          equipment: ['Comfortable clothing'],
          benefits: ['Stress reduction', 'Increased energy', 'Mental clarity']
        }
      }
    ];
  }
  
  /**
   * Fetch mock visitors data for demonstration
   * @returns {Promise<Array>} - Mock visitors data
   */
  async fetchMockVisitors() {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 200));
    
    return [
      {
        date: '2025-06-01',
        count: 145,
        demographics: {
          ageGroups: {
            'under18': 15,
            '18-24': 32,
            '25-34': 48,
            '35-44': 25,
            '45-54': 15,
            '55+': 10
          },
          gender: {
            'female': 78,
            'male': 62,
            'nonBinary': 5
          }
        },
        source: 'walk-in',
        feedbackScore: 4.7,
        externalId: 'VIS-2025-06-01',
        createdAt: '2025-06-01T23:59:59Z',
        updatedAt: '2025-06-01T23:59:59Z',
        metadata: {
          weather: 'Sunny',
          specialEvents: ['Art & Wine Evening'],
          peakHours: ['14:00-16:00']
        }
      },
      {
        date: '2025-06-02',
        count: 98,
        demographics: {
          ageGroups: {
            'under18': 8,
            '18-24': 22,
            '25-34': 35,
            '35-44': 18,
            '45-54': 10,
            '55+': 5
          },
          gender: {
            'female': 53,
            'male': 42,
            'nonBinary': 3
          }
        },
        source: 'walk-in',
        feedbackScore: 4.5,
        externalId: 'VIS-2025-06-02',
        createdAt: '2025-06-02T23:59:59Z',
        updatedAt: '2025-06-02T23:59:59Z',
        metadata: {
          weather: 'Cloudy',
          specialEvents: [],
          peakHours: ['12:00-14:00']
        }
      },
      {
        date: '2025-06-03',
        count: 112,
        demographics: {
          ageGroups: {
            'under18': 12,
            '18-24': 25,
            '25-34': 38,
            '35-44': 20,
            '45-54': 12,
            '55+': 5
          },
          gender: {
            'female': 60,
            'male': 48,
            'nonBinary': 4
          }
        },
        source: 'walk-in',
        feedbackScore: 4.6,
        externalId: 'VIS-2025-06-03',
        createdAt: '2025-06-03T23:59:59Z',
        updatedAt: '2025-06-03T23:59:59Z',
        metadata: {
          weather: 'Partly Cloudy',
          specialEvents: ['Mindfulness Workshop'],
          peakHours: ['15:00-17:00']
        }
      },
      {
        date: '2025-06-04',
        count: 105,
        demographics: {
          ageGroups: {
            'under18': 10,
            '18-24': 24,
            '25-34': 36,
            '35-44': 19,
            '45-54': 11,
            '55+': 5
          },
          gender: {
            'female': 57,
            'male': 45,
            'nonBinary': 3
          }
        },
        source: 'walk-in',
        feedbackScore: 4.5,
        externalId: 'VIS-2025-06-04',
        createdAt: '2025-06-04T23:59:59Z',
        updatedAt: '2025-06-04T23:59:59Z',
        metadata: {
          weather: 'Sunny',
          specialEvents: [],
          peakHours: ['13:00-15:00']
        }
      }
    ];
  }
}

module.exports = new SevenSpaceIntegrationService();

