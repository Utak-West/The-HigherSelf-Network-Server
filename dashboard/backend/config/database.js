const mysql = require('mysql2/promise');
const winston = require('winston');

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

// Database configuration
const dbConfig = {
  host: process.env.DB_HOST || 'localhost',
  port: process.env.DB_PORT || 3306,
  user: process.env.DB_USER || 'dashboard_user',
  password: process.env.DB_PASSWORD || 'dashboard_pass',
  database: process.env.DB_NAME || 'dashboard',
  waitForConnections: true,
  connectionLimit: 10,
  queueLimit: 0,
  acquireTimeout: 60000,
  timeout: 60000,
  reconnect: true,
  charset: 'utf8mb4',
  timezone: '+00:00'
};

// Multi-tenant database configurations
const tenantConfigs = {
  'am-consulting': {
    ...dbConfig,
    database: process.env.AM_CONSULTING_DB || 'am_consulting_prod'
  },
  'seven-space': {
    ...dbConfig,
    database: process.env.SEVEN_SPACE_DB || 'seven_space_prod'
  },
  'higherself': {
    ...dbConfig,
    database: process.env.HIGHERSELF_DB || 'higherself_prod'
  }
};

// Create connection pools
const mainPool = mysql.createPool(dbConfig);
const tenantPools = {};

// Initialize tenant pools
Object.keys(tenantConfigs).forEach(tenant => {
  tenantPools[tenant] = mysql.createPool(tenantConfigs[tenant]);
});

// Database connection wrapper
class Database {
  constructor() {
    this.mainPool = mainPool;
    this.tenantPools = tenantPools;
  }

  // Get main database connection
  async getConnection() {
    try {
      return await this.mainPool.getConnection();
    } catch (error) {
      logger.error('Failed to get main database connection:', error);
      throw error;
    }
  }

  // Get tenant-specific connection
  async getTenantConnection(tenant) {
    if (!this.tenantPools[tenant]) {
      throw new Error(`Invalid tenant: ${tenant}`);
    }
    
    try {
      return await this.tenantPools[tenant].getConnection();
    } catch (error) {
      logger.error(`Failed to get ${tenant} database connection:`, error);
      throw error;
    }
  }

  // Execute query on main database
  async query(sql, params = []) {
    const connection = await this.getConnection();
    try {
      const [results] = await connection.execute(sql, params);
      return results;
    } catch (error) {
      logger.error('Database query error:', { sql, params, error: error.message });
      throw error;
    } finally {
      connection.release();
    }
  }

  // Execute query on tenant database
  async tenantQuery(tenant, sql, params = []) {
    const connection = await this.getTenantConnection(tenant);
    try {
      const [results] = await connection.execute(sql, params);
      return results;
    } catch (error) {
      logger.error(`Tenant ${tenant} query error:`, { sql, params, error: error.message });
      throw error;
    } finally {
      connection.release();
    }
  }

  // Transaction wrapper for main database
  async transaction(callback) {
    const connection = await this.getConnection();
    try {
      await connection.beginTransaction();
      const result = await callback(connection);
      await connection.commit();
      return result;
    } catch (error) {
      await connection.rollback();
      logger.error('Transaction error:', error);
      throw error;
    } finally {
      connection.release();
    }
  }

  // Transaction wrapper for tenant database
  async tenantTransaction(tenant, callback) {
    const connection = await this.getTenantConnection(tenant);
    try {
      await connection.beginTransaction();
      const result = await callback(connection);
      await connection.commit();
      return result;
    } catch (error) {
      await connection.rollback();
      logger.error(`Tenant ${tenant} transaction error:`, error);
      throw error;
    } finally {
      connection.release();
    }
  }

  // Health check
  async healthCheck() {
    try {
      // Check main database
      await this.query('SELECT 1 as health');
      
      // Check tenant databases
      const tenantChecks = await Promise.all(
        Object.keys(this.tenantPools).map(async tenant => {
          try {
            await this.tenantQuery(tenant, 'SELECT 1 as health');
            return { tenant, status: 'healthy' };
          } catch (error) {
            return { tenant, status: 'unhealthy', error: error.message };
          }
        })
      );

      return {
        main: 'healthy',
        tenants: tenantChecks
      };
    } catch (error) {
      logger.error('Database health check failed:', error);
      throw error;
    }
  }

  // Close all connections
  async close() {
    try {
      await this.mainPool.end();
      await Promise.all(
        Object.values(this.tenantPools).map(pool => pool.end())
      );
      logger.info('All database connections closed');
    } catch (error) {
      logger.error('Error closing database connections:', error);
      throw error;
    }
  }

  // Get database statistics
  async getStats() {
    try {
      const mainStats = await this.query(`
        SELECT 
          'main' as database_name,
          COUNT(*) as total_connections,
          SUM(CASE WHEN COMMAND != 'Sleep' THEN 1 ELSE 0 END) as active_connections
        FROM information_schema.PROCESSLIST 
        WHERE DB = ?
      `, [dbConfig.database]);

      const tenantStats = await Promise.all(
        Object.keys(tenantConfigs).map(async tenant => {
          try {
            const stats = await this.tenantQuery(tenant, `
              SELECT 
                ? as database_name,
                COUNT(*) as total_connections,
                SUM(CASE WHEN COMMAND != 'Sleep' THEN 1 ELSE 0 END) as active_connections
              FROM information_schema.PROCESSLIST 
              WHERE DB = ?
            `, [tenant, tenantConfigs[tenant].database]);
            return stats[0];
          } catch (error) {
            return { database_name: tenant, error: error.message };
          }
        })
      );

      return {
        main: mainStats[0],
        tenants: tenantStats
      };
    } catch (error) {
      logger.error('Error getting database stats:', error);
      throw error;
    }
  }
}

// Create and export database instance
const db = new Database();

// Test connections on startup
(async () => {
  try {
    await db.healthCheck();
    logger.info('Database connections established successfully');
  } catch (error) {
    logger.error('Failed to establish database connections:', error);
    process.exit(1);
  }
})();

module.exports = db;

