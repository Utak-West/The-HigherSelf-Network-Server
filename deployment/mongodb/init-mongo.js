// MongoDB initialization script for Higher Self Network Server

// Create application database and user
db = db.getSiblingDB('higherselfnetwork');

// Create application user if it doesn't exist
try {
  db.createUser({
    user: process.env.MONGO_APP_USER || 'higherself_app',
    pwd: process.env.MONGO_APP_PASSWORD || 'secure_app_password',
    roles: [
      { role: 'readWrite', db: 'higherselfnetwork' },
      { role: 'dbAdmin', db: 'higherselfnetwork' }
    ]
  });
  print('Application user created successfully');
} catch (e) {
  if (e.code === 51003) {
    print('Application user already exists');
  } else {
    print('Error creating application user: ' + e.message);
  }
}

// Create initial collections with validation
const collections = [
  'agents',
  'workflows',
  'workflow_instances',
  'tasks',
  'agent_communication',
  'agent_communication_registry',
  'api_integrations',
  'system_health',
  'data_transformations',
  'notification_templates',
  'use_cases',
  'business_entities',
  'contacts_profiles',
  'community_hub',
  'products_services',
  'marketing_campaigns',
  'feedback_surveys',
  'rewards_bounties'
];

collections.forEach(function(collectionName) {
  try {
    db.createCollection(collectionName);
    print('Created collection: ' + collectionName);
  } catch (e) {
    print('Collection ' + collectionName + ' already exists or error: ' + e.message);
  }
});

// Create indexes for performance optimization
print('Creating indexes...');

// Agents collection indexes
db.agents.createIndex({ "id": 1 }, { unique: true });
db.agents.createIndex({ "name": 1 }, { unique: true });
db.agents.createIndex({ "status": 1 });
db.agents.createIndex({ "agent_type": 1 });
db.agents.createIndex({ "last_active": 1 });

// Workflows collection indexes
db.workflows.createIndex({ "id": 1 }, { unique: true });
db.workflows.createIndex({ "name": 1 });
db.workflows.createIndex({ "workflow_type": 1 });
db.workflows.createIndex({ "created_at": 1 });

// Workflow instances collection indexes
db.workflow_instances.createIndex({ "id": 1 }, { unique: true });
db.workflow_instances.createIndex({ "workflow_id": 1 });
db.workflow_instances.createIndex({ "status": 1 });
db.workflow_instances.createIndex({ "started_at": 1 });
db.workflow_instances.createIndex({ "completed_at": 1 });

// Tasks collection indexes
db.tasks.createIndex({ "id": 1 }, { unique: true });
db.tasks.createIndex({ "assigned_agent": 1 });
db.tasks.createIndex({ "status": 1 });
db.tasks.createIndex({ "priority": 1 });
db.tasks.createIndex({ "due_date": 1 });
db.tasks.createIndex({ "created_at": 1 });

// Agent communication indexes
db.agent_communication.createIndex({ "id": 1 }, { unique: true });
db.agent_communication.createIndex({ "source_agent": 1 });
db.agent_communication.createIndex({ "target_agent": 1 });
db.agent_communication.createIndex({ "timestamp": 1 });
db.agent_communication.createIndex({ "communication_type": 1 });

// Agent communication registry indexes
db.agent_communication_registry.createIndex({ "pattern_id": 1 }, { unique: true });
db.agent_communication_registry.createIndex({ "name": 1 });

// API integrations indexes
db.api_integrations.createIndex({ "id": 1 }, { unique: true });
db.api_integrations.createIndex({ "platform": 1 });
db.api_integrations.createIndex({ "status": 1 });
db.api_integrations.createIndex({ "created_at": 1 });

// System health indexes
db.system_health.createIndex({ "timestamp": 1 });
db.system_health.createIndex({ "timestamp": 1, "cpu_usage": 1 });
db.system_health.createIndex({ "timestamp": 1, "memory_usage": 1 });

// Business entities indexes
db.business_entities.createIndex({ "id": 1 }, { unique: true });
db.business_entities.createIndex({ "name": 1 });
db.business_entities.createIndex({ "entity_type": 1 });
db.business_entities.createIndex({ "status": 1 });

print('Indexes created successfully');

// Insert initial agent communication patterns
print('Inserting initial agent communication patterns...');
try {
  db.agent_communication_registry.insertMany([
    {
      "pattern_id": "direct_request_response",
      "name": "Direct Request-Response",
      "description": "Standard synchronous request-response pattern between agents",
      "authorized_source_agents": ["*"], // All agents can use this pattern
      "authorized_target_agents": ["*"], // All agents can be targets
      "created_at": new Date(),
      "updated_at": new Date()
    },
    {
      "pattern_id": "event_notification",
      "name": "Event Notification",
      "description": "Asynchronous event notification pattern",
      "authorized_source_agents": ["*"],
      "authorized_target_agents": ["*"],
      "created_at": new Date(),
      "updated_at": new Date()
    },
    {
      "pattern_id": "workflow_handoff",
      "name": "Workflow Handoff",
      "description": "Handoff pattern for workflow stage transitions",
      "authorized_source_agents": ["*"],
      "authorized_target_agents": ["*"],
      "created_at": new Date(),
      "updated_at": new Date()
    },
    {
      "pattern_id": "task_assignment",
      "name": "Task Assignment",
      "description": "Pattern for assigning tasks between agents",
      "authorized_source_agents": ["*"],
      "authorized_target_agents": ["*"],
      "created_at": new Date(),
      "updated_at": new Date()
    },
    {
      "pattern_id": "status_update",
      "name": "Status Update",
      "description": "Pattern for status updates and progress reporting",
      "authorized_source_agents": ["*"],
      "authorized_target_agents": ["*"],
      "created_at": new Date(),
      "updated_at": new Date()
    }
  ]);
  print('Agent communication patterns inserted successfully');
} catch (e) {
  print('Error inserting communication patterns: ' + e.message);
}

// Insert initial system health record
print('Inserting initial system health record...');
try {
  db.system_health.insertOne({
    "timestamp": new Date(),
    "cpu_usage": 0.0,
    "memory_usage": 0.0,
    "disk_usage": 0.0,
    "active_agents": 0,
    "active_workflows": 0,
    "pending_tasks": 0,
    "api_response_times": {},
    "errors": [],
    "status": "initializing"
  });
  print('Initial system health record inserted');
} catch (e) {
  print('Error inserting system health record: ' + e.message);
}

// Create TTL index for system health (keep records for 30 days)
try {
  db.system_health.createIndex({ "timestamp": 1 }, { expireAfterSeconds: 2592000 });
  print('TTL index created for system_health collection');
} catch (e) {
  print('Error creating TTL index: ' + e.message);
}

print('=== MongoDB initialization completed successfully ===');
print('Database: higherselfnetwork');
print('Collections created: ' + collections.length);
print('User: ' + (process.env.MONGO_APP_USER || 'higherself_app'));
print('Ready for HigherSelf Network Server operations');
