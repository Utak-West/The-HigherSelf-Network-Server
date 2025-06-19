// MongoDB initialization script for The 7 Space Demo Environment

// Switch to the demo database
db = db.getSiblingDB('higherself_demo');

// Create demo user
db.createUser({
  user: 'demo_user',
  pwd: 'demo_password',
  roles: [
    {
      role: 'readWrite',
      db: 'higherself_demo'
    }
  ]
});

// Create collections for The 7 Space demo
db.createCollection('contacts');
db.createCollection('workflows');
db.createCollection('tasks');
db.createCollection('notifications');
db.createCollection('business_entities');
db.createCollection('workflow_instances');

// Create indexes for better performance
db.contacts.createIndex({ "email": 1 }, { unique: true });
db.contacts.createIndex({ "contact_type": 1 });
db.contacts.createIndex({ "business_entity": 1 });
db.contacts.createIndex({ "lead_source": 1 });
db.contacts.createIndex({ "created_at": 1 });
db.contacts.createIndex({ "lead_score": 1 });

db.workflows.createIndex({ "workflow_name": 1 });
db.workflows.createIndex({ "business_entity": 1 });
db.workflows.createIndex({ "contact_type": 1 });

db.tasks.createIndex({ "contact_id": 1 });
db.tasks.createIndex({ "assignee": 1 });
db.tasks.createIndex({ "status": 1 });
db.tasks.createIndex({ "priority": 1 });
db.tasks.createIndex({ "due_date": 1 });

db.workflow_instances.createIndex({ "contact_id": 1 });
db.workflow_instances.createIndex({ "workflow_name": 1 });
db.workflow_instances.createIndex({ "status": 1 });
db.workflow_instances.createIndex({ "created_at": 1 });

// Insert demo business entity
db.business_entities.insertOne({
  _id: "the_7_space",
  name: "The 7 Space",
  type: "gallery_wellness",
  description: "Contemporary art gallery and wellness center",
  contact_types: [
    "artist",
    "gallery_visitor", 
    "wellness_client",
    "event_attendee",
    "workshop_participant",
    "community_member",
    "vendor",
    "media",
    "collector",
    "curator"
  ],
  lead_sources: [
    "gallery_visit",
    "website_contact",
    "social_media",
    "event_signup",
    "workshop_registration",
    "artist_referral",
    "wellness_inquiry",
    "exhibition_interest",
    "community_referral",
    "walk_in"
  ],
  settings: {
    demo_mode: true,
    contact_count: 191,
    auto_classification: true,
    workflow_automation: true,
    lead_scoring: true
  },
  created_at: new Date(),
  updated_at: new Date()
});

print('The 7 Space demo database initialized successfully!');
print('Collections created: contacts, workflows, tasks, notifications, business_entities, workflow_instances');
print('Indexes created for optimal performance');
print('Demo business entity configured');
print('Demo user created with readWrite permissions');
