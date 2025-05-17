// MongoDB initialization script for Higher Self Network Server

// Create application database and user
db = db.getSiblingDB('higherselfnetwork');

// Create application user if it doesn't exist
db.createUser({
  user: process.env.MONGO_APP_USER || 'higherself_app',
  pwd: process.env.MONGO_APP_PASSWORD || 'app_password',
  roles: [
    { role: 'readWrite', db: 'higherselfnetwork' }
  ]
});

// Create initial collections
db.createCollection('agents');
db.createCollection('workflows');
db.createCollection('agent_communication_registry');
db.createCollection('system_health');

// Create indexes
db.agents.createIndex({ "agent_id": 1 }, { unique: true });
db.workflows.createIndex({ "workflow_id": 1 }, { unique: true });
db.agent_communication_registry.createIndex({ "pattern_id": 1 }, { unique: true });
db.system_health.createIndex({ "timestamp": 1 });

// Insert some initial agent communication patterns
db.agent_communication_registry.insertMany([
  {
    "pattern_id": "direct_request_response",
    "name": "Direct Request-Response",
    "description": "Standard synchronous request-response pattern between agents",
    "authorized_source_agents": ["*"], // All agents can use this pattern
    "authorized_target_agents": ["*"] // All agents can be targets
  },
  {
    "pattern_id": "event_notification",
    "name": "Event Notification",
    "description": "Asynchronous event notification pattern",
    "authorized_source_agents": ["*"], 
    "authorized_target_agents": ["*"]
  },
  {
    "pattern_id": "workflow_handoff",
    "name": "Workflow Handoff",
    "description": "Handoff pattern for workflow stage transitions",
    "authorized_source_agents": ["*"],
    "authorized_target_agents": ["*"]
  }
]);

print('MongoDB initialization completed successfully');
