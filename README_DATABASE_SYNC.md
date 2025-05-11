# 🔄 The HigherSelf Network Database Synchronization System 🌐

<div align="center">

![Database System Overview](assets/database_system_overview.svg)

**Aligning and Syncing the 16 Notion Databases with Supabase**

</div>

## 📋 Overview

This system provides a seamless synchronization between the 16 Notion databases used by The HigherSelf Network and corresponding Supabase tables. This dual-database approach combines the user-friendly interface of Notion with the powerful database capabilities of Supabase.

## ✨ Key Features

- **🔄 Bidirectional Sync**: Changes in either system are reflected in the other
- **⏱️ Automated Synchronization**: Regular sync process keeps data consistent
- **⚡ Enhanced Performance**: Faster queries and reporting capabilities
- **🔒 Data Redundancy**: Critical data is stored in both systems for safety
- **🧩 Unified Structure**: All 16 databases are properly aligned across systems
- **⏰ Timestamp Filtering**: Efficient synchronization by only processing records updated since last sync

## 📚 Documentation

We've created comprehensive guides for both developers and staff:

- [📖 Implementation Guide](documentation/IMPLEMENTATION_GUIDE.md) - Overview of the system
- [👩‍💻 Developer Implementation Guide](documentation/DEVELOPER_IMPLEMENTATION_GUIDE.md) - Technical details for developers
- [👥 Staff Implementation Guide](documentation/STAFF_IMPLEMENTATION_GUIDE.md) - User-friendly guide for staff

## 🔍 Interactive Visualization

For a visual representation of the database structure, open the [Database Visualization](assets/database_visualization.html) in your web browser.

## 🚀 Getting Started

### 👩‍💻 For Developers

1. Configure environment variables for Supabase
2. Run the database setup script
3. Perform initial synchronization
4. Set up automated sync process

```bash
# Sync all databases with timestamp filtering
python -m tools.sync_databases

# Sync only records updated in the last 24 hours
python -m tools.sync_databases --since $(date -u -v-1d +"%Y-%m-%dT%H:%M:%S")

# Sync only from Notion to Supabase
python -m tools.sync_databases --direction notion_to_supabase
```

See the [Developer Implementation Guide](documentation/DEVELOPER_IMPLEMENTATION_GUIDE.md) for detailed instructions.

### 👥 For Staff

Your workflow in Notion remains largely unchanged! The synchronization happens automatically in the background, providing enhanced capabilities while maintaining the familiar Notion interface.

See the [Staff Implementation Guide](documentation/STAFF_IMPLEMENTATION_GUIDE.md) for more information.

## 🆘 Support

If you encounter any issues with the database synchronization system, please contact support@thehigherself.network.
