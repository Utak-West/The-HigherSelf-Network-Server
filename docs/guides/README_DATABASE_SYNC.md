# <img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/sync-24.svg" alt="Sync" width="24" height="24" /> The HigherSelf Network Database Synchronization System <img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/globe-24.svg" alt="Globe" width="24" height="24" />

<div align="center">

![Database System Overview](assets/database_system_overview.svg)

**Aligning and Syncing the 16 Notion Databases with Supabase**

</div>

## <img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/checklist-24.svg" alt="Checklist" width="20" height="20" /> Overview

This system provides a seamless synchronization between the 16 Notion databases used by The HigherSelf Network and corresponding Supabase tables. This dual-database approach combines the user-friendly interface of Notion with the powerful database capabilities of Supabase.

## <img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/sparkle-fill-24.svg" alt="Sparkle" width="20" height="20" /> Key Features

- **<img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/sync-24.svg" alt="Sync" width="16" height="16" /> Bidirectional Sync**: Changes in either system are reflected in the other
- **<img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/clock-24.svg" alt="Clock" width="16" height="16" /> Automated Synchronization**: Regular sync process keeps data consistent
- **<img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/zap-24.svg" alt="Zap" width="16" height="16" /> Enhanced Performance**: Faster queries and reporting capabilities
- **<img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/lock-24.svg" alt="Lock" width="16" height="16" /> Data Redundancy**: Critical data is stored in both systems for safety
- **<img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/puzzle-24.svg" alt="Puzzle" width="16" height="16" /> Unified Structure**: All 16 databases are properly aligned across systems
- **<img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/clock-24.svg" alt="Clock" width="16" height="16" /> Timestamp Filtering**: Efficient synchronization by only processing records updated since last sync

## <img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/book-24.svg" alt="Book" width="20" height="20" /> Documentation

We've created comprehensive guides for both developers and staff:

- [<img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/book-24.svg" alt="Book" width="16" height="16" /> Implementation Guide](documentation/IMPLEMENTATION_GUIDE.md) - Overview of the system
- [<img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/person-24.svg" alt="Person" width="16" height="16" /> Developer Implementation Guide](documentation/DEVELOPER_IMPLEMENTATION_GUIDE.md) - Technical details for developers
- [<img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/people-24.svg" alt="People" width="16" height="16" /> Staff Implementation Guide](documentation/STAFF_IMPLEMENTATION_GUIDE.md) - User-friendly guide for staff

## <img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/search-24.svg" alt="Search" width="20" height="20" /> Interactive Visualization

For a visual representation of the database structure, open the [Database Visualization](assets/database_visualization.html) in your web browser.

## <img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/rocket-24.svg" alt="Rocket" width="20" height="20" /> Getting Started

### <img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/person-24.svg" alt="Person" width="18" height="18" /> For Developers

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

### <img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/people-24.svg" alt="People" width="18" height="18" /> For Staff

Your workflow in Notion remains largely unchanged! The synchronization happens automatically in the background, providing enhanced capabilities while maintaining the familiar Notion interface.

See the [Staff Implementation Guide](documentation/STAFF_IMPLEMENTATION_GUIDE.md) for more information.

## <img src="https://raw.githubusercontent.com/readme-workflows/readme-icons/main/icons/octicons/issue-opened-24.svg" alt="Issue" width="20" height="20" /> Support

If you encounter any issues with the database synchronization system, please contact support@thehigherself.network.
