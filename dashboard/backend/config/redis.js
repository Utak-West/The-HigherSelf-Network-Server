const redis = require('redis');
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

// Redis configuration
const redisConfig = {
  url: process.env.REDIS_URL || 'redis://localhost:6379',
  password: process.env.REDIS_PASSWORD || undefined,
  retryDelayOnFailover: 100,
  enableReadyCheck: true,
  maxRetriesPerRequest: 3,
  lazyConnect: true,
  keepAlive: 30000,
  connectTimeout: 10000,
  commandTimeout: 5000
};

// Create Redis client
const client = redis.createClient(redisConfig);

// Redis client event handlers
client.on('connect', () => {
  logger.info('Redis client connected');
});

client.on('ready', () => {
  logger.info('Redis client ready');
});

client.on('error', (error) => {
  logger.error('Redis client error:', error);
});

client.on('end', () => {
  logger.info('Redis client connection ended');
});

client.on('reconnecting', () => {
  logger.info('Redis client reconnecting');
});

// Redis wrapper class
class RedisManager {
  constructor() {
    this.client = client;
    this.isConnected = false;
  }

  // Connect to Redis
  async connect() {
    try {
      if (!this.isConnected) {
        await this.client.connect();
        this.isConnected = true;
        logger.info('Redis connection established');
      }
    } catch (error) {
      logger.error('Failed to connect to Redis:', error);
      throw error;
    }
  }

  // Disconnect from Redis
  async disconnect() {
    try {
      if (this.isConnected) {
        await this.client.quit();
        this.isConnected = false;
        logger.info('Redis connection closed');
      }
    } catch (error) {
      logger.error('Error disconnecting from Redis:', error);
      throw error;
    }
  }

  // Set key-value pair with optional expiration
  async set(key, value, expireInSeconds = null) {
    try {
      const serializedValue = JSON.stringify(value);
      if (expireInSeconds) {
        await this.client.setEx(key, expireInSeconds, serializedValue);
      } else {
        await this.client.set(key, serializedValue);
      }
      logger.debug(`Redis SET: ${key}`);
    } catch (error) {
      logger.error(`Redis SET error for key ${key}:`, error);
      throw error;
    }
  }

  // Get value by key
  async get(key) {
    try {
      const value = await this.client.get(key);
      if (value === null) {
        return null;
      }
      logger.debug(`Redis GET: ${key}`);
      return JSON.parse(value);
    } catch (error) {
      logger.error(`Redis GET error for key ${key}:`, error);
      throw error;
    }
  }

  // Delete key
  async del(key) {
    try {
      const result = await this.client.del(key);
      logger.debug(`Redis DEL: ${key}`);
      return result;
    } catch (error) {
      logger.error(`Redis DEL error for key ${key}:`, error);
      throw error;
    }
  }

  // Check if key exists
  async exists(key) {
    try {
      const result = await this.client.exists(key);
      return result === 1;
    } catch (error) {
      logger.error(`Redis EXISTS error for key ${key}:`, error);
      throw error;
    }
  }

  // Set expiration for key
  async expire(key, seconds) {
    try {
      const result = await this.client.expire(key, seconds);
      logger.debug(`Redis EXPIRE: ${key} (${seconds}s)`);
      return result === 1;
    } catch (error) {
      logger.error(`Redis EXPIRE error for key ${key}:`, error);
      throw error;
    }
  }

  // Get keys by pattern
  async keys(pattern) {
    try {
      const keys = await this.client.keys(pattern);
      logger.debug(`Redis KEYS: ${pattern} (${keys.length} found)`);
      return keys;
    } catch (error) {
      logger.error(`Redis KEYS error for pattern ${pattern}:`, error);
      throw error;
    }
  }

  // Hash operations
  async hSet(key, field, value) {
    try {
      const serializedValue = JSON.stringify(value);
      await this.client.hSet(key, field, serializedValue);
      logger.debug(`Redis HSET: ${key}.${field}`);
    } catch (error) {
      logger.error(`Redis HSET error for ${key}.${field}:`, error);
      throw error;
    }
  }

  async hGet(key, field) {
    try {
      const value = await this.client.hGet(key, field);
      if (value === null) {
        return null;
      }
      logger.debug(`Redis HGET: ${key}.${field}`);
      return JSON.parse(value);
    } catch (error) {
      logger.error(`Redis HGET error for ${key}.${field}:`, error);
      throw error;
    }
  }

  async hGetAll(key) {
    try {
      const hash = await this.client.hGetAll(key);
      const result = {};
      for (const [field, value] of Object.entries(hash)) {
        result[field] = JSON.parse(value);
      }
      logger.debug(`Redis HGETALL: ${key}`);
      return result;
    } catch (error) {
      logger.error(`Redis HGETALL error for key ${key}:`, error);
      throw error;
    }
  }

  async hDel(key, field) {
    try {
      const result = await this.client.hDel(key, field);
      logger.debug(`Redis HDEL: ${key}.${field}`);
      return result;
    } catch (error) {
      logger.error(`Redis HDEL error for ${key}.${field}:`, error);
      throw error;
    }
  }

  // List operations
  async lPush(key, ...values) {
    try {
      const serializedValues = values.map(v => JSON.stringify(v));
      const result = await this.client.lPush(key, ...serializedValues);
      logger.debug(`Redis LPUSH: ${key} (${values.length} items)`);
      return result;
    } catch (error) {
      logger.error(`Redis LPUSH error for key ${key}:`, error);
      throw error;
    }
  }

  async rPush(key, ...values) {
    try {
      const serializedValues = values.map(v => JSON.stringify(v));
      const result = await this.client.rPush(key, ...serializedValues);
      logger.debug(`Redis RPUSH: ${key} (${values.length} items)`);
      return result;
    } catch (error) {
      logger.error(`Redis RPUSH error for key ${key}:`, error);
      throw error;
    }
  }

  async lRange(key, start, stop) {
    try {
      const values = await this.client.lRange(key, start, stop);
      const result = values.map(v => JSON.parse(v));
      logger.debug(`Redis LRANGE: ${key} (${start}-${stop})`);
      return result;
    } catch (error) {
      logger.error(`Redis LRANGE error for key ${key}:`, error);
      throw error;
    }
  }

  // Set operations
  async sAdd(key, ...members) {
    try {
      const serializedMembers = members.map(m => JSON.stringify(m));
      const result = await this.client.sAdd(key, ...serializedMembers);
      logger.debug(`Redis SADD: ${key} (${members.length} members)`);
      return result;
    } catch (error) {
      logger.error(`Redis SADD error for key ${key}:`, error);
      throw error;
    }
  }

  async sMembers(key) {
    try {
      const members = await this.client.sMembers(key);
      const result = members.map(m => JSON.parse(m));
      logger.debug(`Redis SMEMBERS: ${key}`);
      return result;
    } catch (error) {
      logger.error(`Redis SMEMBERS error for key ${key}:`, error);
      throw error;
    }
  }

  // Cache helper methods
  async cache(key, fetchFunction, expireInSeconds = 3600) {
    try {
      // Try to get from cache first
      const cached = await this.get(key);
      if (cached !== null) {
        logger.debug(`Cache HIT: ${key}`);
        return cached;
      }

      // Cache miss - fetch data
      logger.debug(`Cache MISS: ${key}`);
      const data = await fetchFunction();
      
      // Store in cache
      await this.set(key, data, expireInSeconds);
      return data;
    } catch (error) {
      logger.error(`Cache error for key ${key}:`, error);
      throw error;
    }
  }

  // Session management
  async setSession(sessionId, sessionData, expireInSeconds = 86400) {
    const key = `session:${sessionId}`;
    await this.set(key, sessionData, expireInSeconds);
  }

  async getSession(sessionId) {
    const key = `session:${sessionId}`;
    return await this.get(key);
  }

  async deleteSession(sessionId) {
    const key = `session:${sessionId}`;
    return await this.del(key);
  }

  // Rate limiting
  async checkRateLimit(identifier, limit, windowInSeconds) {
    const key = `rate_limit:${identifier}`;
    const current = await this.client.incr(key);
    
    if (current === 1) {
      await this.client.expire(key, windowInSeconds);
    }
    
    return {
      count: current,
      limit: limit,
      remaining: Math.max(0, limit - current),
      resetTime: Date.now() + (windowInSeconds * 1000)
    };
  }

  // Health check
  async ping() {
    try {
      const result = await this.client.ping();
      return result === 'PONG';
    } catch (error) {
      logger.error('Redis ping failed:', error);
      throw error;
    }
  }

  // Get Redis info
  async info() {
    try {
      const info = await this.client.info();
      return info;
    } catch (error) {
      logger.error('Redis info failed:', error);
      throw error;
    }
  }

  // Flush all data (use with caution)
  async flushAll() {
    try {
      await this.client.flushAll();
      logger.warn('Redis FLUSHALL executed - all data cleared');
    } catch (error) {
      logger.error('Redis FLUSHALL failed:', error);
      throw error;
    }
  }
}

// Create and export Redis manager instance
const redisManager = new RedisManager();

// Connect on startup
(async () => {
  try {
    await redisManager.connect();
    logger.info('Redis connection established successfully');
  } catch (error) {
    logger.error('Failed to establish Redis connection:', error);
    // Don't exit process - Redis is not critical for basic functionality
  }
})();

module.exports = redisManager;

