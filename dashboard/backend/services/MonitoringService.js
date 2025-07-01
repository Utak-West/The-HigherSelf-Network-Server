const os = require('os');
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
    new winston.transports.File({ filename: 'logs/monitoring.log' }),
    new winston.transports.Console({
      format: winston.format.simple()
    })
  ]
});

/**
 * System Monitoring Service
 * Handles monitoring of system health, performance metrics, and alerts
 */
class MonitoringService {
  constructor() {
    this.metricsCache = {};
    this.alertThresholds = {
      cpu: 80, // CPU usage percentage
      memory: 80, // Memory usage percentage
      disk: 80, // Disk usage percentage
      apiLatency: 1000, // API response time in ms
      errorRate: 5, // Error rate percentage
      databaseConnections: 80 // Database connection pool usage percentage
    };
  }

  /**
   * Get system health status
   * @returns {Promise<Object>} - System health metrics
   */
  async getSystemHealth() {
    try {
      logger.info('Getting system health metrics');
      
      // Get cached metrics if available (within last 60 seconds)
      const cachedMetrics = await redis.get('monitoring:system_health');
      if (cachedMetrics) {
        const parsed = JSON.parse(cachedMetrics);
        const now = Date.now();
        if (now - parsed.timestamp < 60000) {
          return parsed;
        }
      }
      
      // Calculate CPU usage
      const cpuUsage = await this.getCpuUsage();
      
      // Calculate memory usage
      const totalMemory = os.totalmem();
      const freeMemory = os.freemem();
      const usedMemory = totalMemory - freeMemory;
      const memoryUsage = (usedMemory / totalMemory) * 100;
      
      // Get database metrics
      const dbMetrics = await this.getDatabaseMetrics();
      
      // Get API metrics
      const apiMetrics = await this.getApiMetrics();
      
      // Determine overall status
      const cpuStatus = this.getStatusLevel(cpuUsage, this.alertThresholds.cpu);
      const memoryStatus = this.getStatusLevel(memoryUsage, this.alertThresholds.memory);
      const dbStatus = this.getStatusLevel(dbMetrics.connectionUsage, this.alertThresholds.databaseConnections);
      const apiStatus = this.getStatusLevel(apiMetrics.errorRate, this.alertThresholds.errorRate);
      
      const statuses = [cpuStatus, memoryStatus, dbStatus, apiStatus];
      let overallStatus = 'healthy';
      
      if (statuses.includes('critical')) {
        overallStatus = 'critical';
      } else if (statuses.includes('warning')) {
        overallStatus = 'warning';
      }
      
      // Compile metrics
      const metrics = {
        timestamp: Date.now(),
        status: overallStatus,
        cpu: {
          usage: cpuUsage.toFixed(2),
          status: cpuStatus
        },
        memory: {
          total: this.formatBytes(totalMemory),
          used: this.formatBytes(usedMemory),
          free: this.formatBytes(freeMemory),
          usage: memoryUsage.toFixed(2),
          status: memoryStatus
        },
        database: {
          activeConnections: dbMetrics.activeConnections,
          maxConnections: dbMetrics.maxConnections,
          connectionUsage: dbMetrics.connectionUsage.toFixed(2),
          queryLatency: dbMetrics.queryLatency.toFixed(2),
          status: dbStatus
        },
        api: {
          requestsPerMinute: apiMetrics.requestsPerMinute,
          avgResponseTime: apiMetrics.avgResponseTime.toFixed(2),
          errorRate: apiMetrics.errorRate.toFixed(2),
          status: apiStatus
        },
        uptime: {
          system: this.formatUptime(os.uptime()),
          process: this.formatUptime(process.uptime())
        }
      };
      
      // Cache metrics
      await redis.set('monitoring:system_health', JSON.stringify(metrics), 'EX', 60);
      
      // Store historical metrics
      await this.storeHistoricalMetrics(metrics);
      
      // Check for alerts
      await this.checkAlerts(metrics);
      
      return metrics;
    } catch (error) {
      logger.error('Error getting system health metrics:', error);
      throw error;
    }
  }
  
  /**
   * Get CPU usage percentage
   * @returns {Promise<number>} - CPU usage percentage
   */
  async getCpuUsage() {
    return new Promise((resolve) => {
      const startMeasure = this.getCpuInfo();
      
      // Wait 100ms for next measure
      setTimeout(() => {
        const endMeasure = this.getCpuInfo();
        const idleDifference = endMeasure.idle - startMeasure.idle;
        const totalDifference = endMeasure.total - startMeasure.total;
        const cpuUsage = 100 - (100 * idleDifference / totalDifference);
        resolve(cpuUsage);
      }, 100);
    });
  }
  
  /**
   * Get CPU information
   * @returns {Object} - CPU idle and total times
   */
  getCpuInfo() {
    const cpus = os.cpus();
    let idle = 0;
    let total = 0;
    
    for (const cpu of cpus) {
      for (const type in cpu.times) {
        total += cpu.times[type];
      }
      idle += cpu.times.idle;
    }
    
    return { idle, total };
  }
  
  /**
   * Get database metrics
   * @returns {Promise<Object>} - Database metrics
   */
  async getDatabaseMetrics() {
    try {
      // Get connection pool status
      const poolStatus = await db.query('SHOW STATUS WHERE Variable_name = "Threads_connected" OR Variable_name = "max_connections"');
      
      let activeConnections = 0;
      let maxConnections = 100; // Default
      
      for (const row of poolStatus) {
        if (row.Variable_name === 'Threads_connected') {
          activeConnections = parseInt(row.Value, 10);
        } else if (row.Variable_name === 'max_connections') {
          maxConnections = parseInt(row.Value, 10);
        }
      }
      
      const connectionUsage = (activeConnections / maxConnections) * 100;
      
      // Measure query latency
      const startTime = Date.now();
      await db.query('SELECT 1');
      const queryLatency = Date.now() - startTime;
      
      return {
        activeConnections,
        maxConnections,
        connectionUsage,
        queryLatency
      };
    } catch (error) {
      logger.error('Error getting database metrics:', error);
      return {
        activeConnections: 0,
        maxConnections: 100,
        connectionUsage: 0,
        queryLatency: 0
      };
    }
  }
  
  /**
   * Get API metrics
   * @returns {Promise<Object>} - API metrics
   */
  async getApiMetrics() {
    try {
      // Get API metrics from Redis
      const requestsData = await redis.get('monitoring:api_requests');
      const latencyData = await redis.get('monitoring:api_latency');
      const errorsData = await redis.get('monitoring:api_errors');
      
      const requests = requestsData ? JSON.parse(requestsData) : { count: 0, timestamp: Date.now() };
      const latency = latencyData ? JSON.parse(latencyData) : { total: 0, count: 0 };
      const errors = errorsData ? JSON.parse(errorsData) : { count: 0 };
      
      // Calculate metrics
      const timeElapsed = (Date.now() - requests.timestamp) / 1000 / 60; // minutes
      const requestsPerMinute = timeElapsed > 0 ? requests.count / timeElapsed : 0;
      const avgResponseTime = latency.count > 0 ? latency.total / latency.count : 0;
      const errorRate = requests.count > 0 ? (errors.count / requests.count) * 100 : 0;
      
      return {
        requestsPerMinute,
        avgResponseTime,
        errorRate
      };
    } catch (error) {
      logger.error('Error getting API metrics:', error);
      return {
        requestsPerMinute: 0,
        avgResponseTime: 0,
        errorRate: 0
      };
    }
  }
  
  /**
   * Store historical metrics for trending
   * @param {Object} metrics - Current system metrics
   * @returns {Promise<void>}
   */
  async storeHistoricalMetrics(metrics) {
    try {
      // Store hourly snapshots
      const currentHour = new Date();
      currentHour.setMinutes(0, 0, 0);
      
      const hourlyKey = `monitoring:hourly:${currentHour.getTime()}`;
      const exists = await redis.exists(hourlyKey);
      
      if (!exists) {
        // Store simplified metrics for historical tracking
        const historicalMetrics = {
          timestamp: metrics.timestamp,
          cpu: metrics.cpu.usage,
          memory: metrics.memory.usage,
          dbConnections: metrics.database.connectionUsage,
          dbLatency: metrics.database.queryLatency,
          apiRequests: metrics.api.requestsPerMinute,
          apiLatency: metrics.api.avgResponseTime,
          apiErrors: metrics.api.errorRate
        };
        
        await redis.set(hourlyKey, JSON.stringify(historicalMetrics), 'EX', 86400 * 7); // Keep for 7 days
        
        // Maintain list of hourly keys for querying
        await redis.zadd('monitoring:hourly_keys', currentHour.getTime(), hourlyKey);
        await redis.zremrangebyscore('monitoring:hourly_keys', 0, Date.now() - (86400 * 7 * 1000)); // Remove keys older than 7 days
      }
    } catch (error) {
      logger.error('Error storing historical metrics:', error);
    }
  }
  
  /**
   * Get historical metrics for trending
   * @param {number} hours - Number of hours to retrieve
   * @returns {Promise<Array>} - Historical metrics
   */
  async getHistoricalMetrics(hours = 24) {
    try {
      const endTime = Date.now();
      const startTime = endTime - (hours * 60 * 60 * 1000);
      
      // Get hourly keys within time range
      const hourlyKeys = await redis.zrangebyscore('monitoring:hourly_keys', startTime, endTime);
      
      if (!hourlyKeys || hourlyKeys.length === 0) {
        return [];
      }
      
      // Get metrics for each hour
      const metrics = [];
      for (const key of hourlyKeys) {
        const data = await redis.get(key);
        if (data) {
          metrics.push(JSON.parse(data));
        }
      }
      
      return metrics;
    } catch (error) {
      logger.error('Error getting historical metrics:', error);
      return [];
    }
  }
  
  /**
   * Check for alert conditions
   * @param {Object} metrics - Current system metrics
   * @returns {Promise<void>}
   */
  async checkAlerts(metrics) {
    try {
      const alerts = [];
      
      // Check CPU usage
      if (parseFloat(metrics.cpu.usage) >= this.alertThresholds.cpu) {
        alerts.push({
          type: 'cpu',
          level: metrics.cpu.status,
          message: `High CPU usage: ${metrics.cpu.usage}%`,
          timestamp: Date.now()
        });
      }
      
      // Check memory usage
      if (parseFloat(metrics.memory.usage) >= this.alertThresholds.memory) {
        alerts.push({
          type: 'memory',
          level: metrics.memory.status,
          message: `High memory usage: ${metrics.memory.usage}%`,
          timestamp: Date.now()
        });
      }
      
      // Check database connection usage
      if (parseFloat(metrics.database.connectionUsage) >= this.alertThresholds.databaseConnections) {
        alerts.push({
          type: 'database',
          level: metrics.database.status,
          message: `High database connection usage: ${metrics.database.connectionUsage}%`,
          timestamp: Date.now()
        });
      }
      
      // Check API error rate
      if (parseFloat(metrics.api.errorRate) >= this.alertThresholds.errorRate) {
        alerts.push({
          type: 'api',
          level: metrics.api.status,
          message: `High API error rate: ${metrics.api.errorRate}%`,
          timestamp: Date.now()
        });
      }
      
      // Store alerts if any
      if (alerts.length > 0) {
        for (const alert of alerts) {
          await redis.lpush('monitoring:alerts', JSON.stringify(alert));
        }
        
        // Trim alert list to last 100
        await redis.ltrim('monitoring:alerts', 0, 99);
        
        // Log critical alerts
        const criticalAlerts = alerts.filter(alert => alert.level === 'critical');
        for (const alert of criticalAlerts) {
          logger.warn(`CRITICAL ALERT: ${alert.message}`);
        }
      }
    } catch (error) {
      logger.error('Error checking alerts:', error);
    }
  }
  
  /**
   * Get recent alerts
   * @param {number} limit - Maximum number of alerts to retrieve
   * @returns {Promise<Array>} - Recent alerts
   */
  async getAlerts(limit = 10) {
    try {
      const alertsData = await redis.lrange('monitoring:alerts', 0, limit - 1);
      
      if (!alertsData || alertsData.length === 0) {
        return [];
      }
      
      return alertsData.map(data => JSON.parse(data));
    } catch (error) {
      logger.error('Error getting alerts:', error);
      return [];
    }
  }
  
  /**
   * Track API request
   * @param {number} responseTime - API response time in ms
   * @param {boolean} isError - Whether the request resulted in an error
   * @returns {Promise<void>}
   */
  async trackApiRequest(responseTime, isError = false) {
    try {
      // Update request count
      const requestsData = await redis.get('monitoring:api_requests');
      let requests = { count: 0, timestamp: Date.now() };
      
      if (requestsData) {
        requests = JSON.parse(requestsData);
        requests.count++;
      } else {
        requests.count = 1;
      }
      
      await redis.set('monitoring:api_requests', JSON.stringify(requests), 'EX', 3600); // 1 hour
      
      // Update latency metrics
      const latencyData = await redis.get('monitoring:api_latency');
      let latency = { total: 0, count: 0 };
      
      if (latencyData) {
        latency = JSON.parse(latencyData);
      }
      
      latency.total += responseTime;
      latency.count++;
      
      await redis.set('monitoring:api_latency', JSON.stringify(latency), 'EX', 3600); // 1 hour
      
      // Update error count if applicable
      if (isError) {
        const errorsData = await redis.get('monitoring:api_errors');
        let errors = { count: 0 };
        
        if (errorsData) {
          errors = JSON.parse(errorsData);
          errors.count++;
        } else {
          errors.count = 1;
        }
        
        await redis.set('monitoring:api_errors', JSON.stringify(errors), 'EX', 3600); // 1 hour
      }
    } catch (error) {
      logger.error('Error tracking API request:', error);
    }
  }
  
  /**
   * Reset API metrics
   * @returns {Promise<void>}
   */
  async resetApiMetrics() {
    try {
      await redis.del('monitoring:api_requests');
      await redis.del('monitoring:api_latency');
      await redis.del('monitoring:api_errors');
      
      logger.info('API metrics reset');
    } catch (error) {
      logger.error('Error resetting API metrics:', error);
    }
  }
  
  /**
   * Update alert thresholds
   * @param {Object} thresholds - New alert thresholds
   * @returns {Promise<Object>} - Updated thresholds
   */
  async updateAlertThresholds(thresholds) {
    try {
      this.alertThresholds = {
        ...this.alertThresholds,
        ...thresholds
      };
      
      // Store thresholds in Redis for persistence
      await redis.set('monitoring:alert_thresholds', JSON.stringify(this.alertThresholds));
      
      logger.info('Alert thresholds updated:', this.alertThresholds);
      
      return this.alertThresholds;
    } catch (error) {
      logger.error('Error updating alert thresholds:', error);
      throw error;
    }
  }
  
  /**
   * Get alert thresholds
   * @returns {Promise<Object>} - Current alert thresholds
   */
  async getAlertThresholds() {
    try {
      const thresholds = await redis.get('monitoring:alert_thresholds');
      
      if (thresholds) {
        this.alertThresholds = JSON.parse(thresholds);
      }
      
      return this.alertThresholds;
    } catch (error) {
      logger.error('Error getting alert thresholds:', error);
      return this.alertThresholds;
    }
  }
  
  /**
   * Get status level based on value and threshold
   * @param {number} value - Metric value
   * @param {number} threshold - Alert threshold
   * @returns {string} - Status level (healthy, warning, critical)
   */
  getStatusLevel(value, threshold) {
    if (value >= threshold) {
      return 'critical';
    } else if (value >= threshold * 0.8) {
      return 'warning';
    } else {
      return 'healthy';
    }
  }
  
  /**
   * Format bytes to human-readable string
   * @param {number} bytes - Bytes to format
   * @returns {string} - Formatted string
   */
  formatBytes(bytes) {
    if (bytes === 0) return '0 B';
    
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }
  
  /**
   * Format uptime to human-readable string
   * @param {number} seconds - Uptime in seconds
   * @returns {string} - Formatted string
   */
  formatUptime(seconds) {
    const days = Math.floor(seconds / 86400);
    seconds %= 86400;
    
    const hours = Math.floor(seconds / 3600);
    seconds %= 3600;
    
    const minutes = Math.floor(seconds / 60);
    seconds = Math.floor(seconds % 60);
    
    const parts = [];
    
    if (days > 0) parts.push(`${days}d`);
    if (hours > 0) parts.push(`${hours}h`);
    if (minutes > 0) parts.push(`${minutes}m`);
    if (seconds > 0 || parts.length === 0) parts.push(`${seconds}s`);
    
    return parts.join(' ');
  }
}

module.exports = new MonitoringService();

