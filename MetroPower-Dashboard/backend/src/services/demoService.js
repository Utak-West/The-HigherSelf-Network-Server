/**
 * Demo Service
 *
 * Provides in-memory data and functionality when database is unavailable
 * for the MetroPower Dashboard demonstration mode.
 *
 * Copyright 2025 The HigherSelf Network
 */

const config = require('../config/app');
const logger = require('../utils/logger');
const employeeDataService = require('./employeeDataService');

// In-memory data
let appData = {
  users: [
    {
      user_id: 1,
      username: 'antione.harrell',
      email: 'Antione.Harrell@metropower.com',
      password_hash: '$2a$12$4JYI8yrfXfMSY1m31gMbhOc/3CwpPtwAjC/.sHyBFheam35YM/JvO', // password: "password"
      first_name: 'Antione',
      last_name: 'Harrell',
      role: 'Project Manager',
      is_active: true,
      created_at: '2024-01-01T00:00:00.000Z',
      updated_at: '2024-01-01T00:00:00.000Z',
      last_login: new Date().toISOString()
    }
  ],
  employees: [
    {
      employee_id: 1,
      first_name: 'John',
      last_name: 'Smith',
      trade: 'Electrician',
      level: 'Journeyman',
      hourly_rate: 28.50,
      is_active: true,
      hire_date: '2023-01-15',
      phone: '555-0101',
      email: 'john.smith@metropower.com'
    },
    {
      employee_id: 2,
      first_name: 'Mike',
      last_name: 'Johnson',
      trade: 'Electrician',
      level: 'Apprentice',
      hourly_rate: 22.00,
      is_active: true,
      hire_date: '2023-03-20',
      phone: '555-0102',
      email: 'mike.johnson@metropower.com'
    },
    {
      employee_id: 3,
      first_name: 'Sarah',
      last_name: 'Williams',
      trade: 'Field Supervisor',
      level: 'Senior',
      hourly_rate: 35.00,
      is_active: true,
      hire_date: '2022-08-10',
      phone: '555-0103',
      email: 'sarah.williams@metropower.com'
    },
    {
      employee_id: 4,
      first_name: 'David',
      last_name: 'Brown',
      trade: 'Electrician',
      level: 'Master',
      hourly_rate: 32.00,
      is_active: true,
      hire_date: '2021-11-05',
      phone: '555-0104',
      email: 'david.brown@metropower.com'
    },
    {
      employee_id: 5,
      first_name: 'Lisa',
      last_name: 'Davis',
      trade: 'Electrician',
      level: 'Journeyman',
      hourly_rate: 29.00,
      is_active: true,
      hire_date: '2023-02-14',
      phone: '555-0105',
      email: 'lisa.davis@metropower.com'
    }
  ],
  projects: [
    {
      project_id: 1,
      project_name: 'Tucker Mall Renovation',
      project_code: 'TM-2024-001',
      client_name: 'Tucker Development Corp',
      start_date: '2024-01-15',
      end_date: '2024-06-30',
      status: 'Active',
      project_manager: 'Antione Harrell',
      estimated_hours: 2400,
      actual_hours: 1200
    },
    {
      project_id: 2,
      project_name: 'Office Complex Wiring',
      project_code: 'OC-2024-002',
      client_name: 'Metro Business Park',
      start_date: '2024-02-01',
      end_date: '2024-05-15',
      status: 'Active',
      project_manager: 'Antione Harrell',
      estimated_hours: 1800,
      actual_hours: 900
    },
    {
      project_id: 3,
      project_name: 'Residential Development',
      project_code: 'RD-2024-003',
      client_name: 'Tucker Homes LLC',
      start_date: '2024-03-01',
      end_date: '2024-08-31',
      status: 'Active',
      project_manager: 'Antione Harrell',
      estimated_hours: 3200,
      actual_hours: 800
    }
  ],
  assignments: [
    {
      assignment_id: 1,
      employee_id: 1,
      project_id: 1,
      assignment_date: new Date().toISOString().split('T')[0],
      hours_assigned: 8,
      status: 'Assigned'
    },
    {
      assignment_id: 2,
      employee_id: 2,
      project_id: 1,
      assignment_date: new Date().toISOString().split('T')[0],
      hours_assigned: 8,
      status: 'Assigned'
    },
    {
      assignment_id: 3,
      employee_id: 3,
      project_id: 2,
      assignment_date: new Date().toISOString().split('T')[0],
      hours_assigned: 8,
      status: 'Assigned'
    }
  ]
};

class DataService {
  /**
   * Initialize data service
   */
  static async initialize() {
    // Try to load real employee data
    const loaded = await employeeDataService.loadEmployeeData();

    if (loaded) {
      // Update app data with real employee data
      appData.employees = employeeDataService.getEmployees();
      appData.projects = employeeDataService.getActiveProjects();

      // Generate some sample assignments for demo
      this.generateSampleAssignments();

      logger.info('Employee data service initialized with real employee data');
    } else {
      logger.info('Employee data service initialized with mock data');
    }

    logger.info(`Users: ${appData.users.length}`);
    logger.info(`Employees: ${appData.employees.length}`);
    logger.info(`Projects: ${appData.projects.length}`);
    logger.info(`Assignments: ${appData.assignments.length}`);
  }

  /**
   * Generate sample assignments
   */
  static generateSampleAssignments() {
    const today = new Date();
    const assignments = [];
    let assignmentId = 1;

    // Get a subset of employees for assignments (not all employees are assigned every day)
    const activeEmployees = appData.employees.filter(e => e.is_active);
    const assignedEmployees = activeEmployees.slice(0, Math.floor(activeEmployees.length * 0.7)); // 70% assigned

    // Generate assignments for the current week
    for (let dayOffset = 0; dayOffset < 7; dayOffset++) {
      const date = new Date(today);
      date.setDate(today.getDate() - today.getDay() + dayOffset); // Start from Sunday
      const dateStr = date.toISOString().split('T')[0];

      // Assign employees to projects for this day
      assignedEmployees.forEach((employee, index) => {
        const projectIndex = index % appData.projects.length;
        const project = appData.projects[projectIndex];

        assignments.push({
          assignment_id: assignmentId++,
          employee_id: employee.employee_id,
          project_id: project.project_id,
          assignment_date: dateStr,
          hours_assigned: 8,
          status: 'Assigned'
        });
      });
    }

    appData.assignments = assignments;
  }

  /**
   * Find user by ID
   * @param {number} userId - User ID
   * @returns {Promise<Object|null>} User data or null
   */
  static async findUserById(userId) {
    const user = appData.users.find(u => u.user_id === userId);
    return user ? { ...user } : null;
  }

  /**
   * Find user by identifier (username or email)
   * @param {string} identifier - Username or email
   * @returns {Promise<Object|null>} User data or null
   */
  static async findUserByIdentifier(identifier) {
    const user = appData.users.find(u =>
      u.username === identifier || u.email === identifier
    );
    return user ? { ...user } : null;
  }

  /**
   * Get all employees
   * @returns {Promise<Array>} Array of employees
   */
  static async getEmployees() {
    return [...appData.employees];
  }

  /**
   * Get unassigned employees for a specific date
   * @param {string} date - Date in YYYY-MM-DD format
   * @returns {Promise<Array>} Array of unassigned employees
   */
  static async getUnassignedEmployees(date) {
    const assignedEmployeeIds = appData.assignments
      .filter(a => a.assignment_date === date)
      .map(a => a.employee_id);

    return appData.employees.filter(e =>
      e.is_active && !assignedEmployeeIds.includes(e.employee_id)
    );
  }

  /**
   * Get all projects
   * @returns {Promise<Array>} Array of projects
   */
  static async getProjects() {
    return [...appData.projects];
  }

  /**
   * Get active projects
   * @returns {Promise<Array>} Array of active projects
   */
  static async getActiveProjects() {
    return appData.projects.filter(p => p.status === 'Active');
  }

  /**
   * Get assignments for a specific week
   * @param {string} weekStart - Week start date in YYYY-MM-DD format
   * @returns {Promise<Object>} Assignments grouped by date and project
   */
  static async getWeekAssignments(weekStart) {
    const weekDates = [];
    const startDate = new Date(weekStart);

    // Generate 7 days from start date
    for (let i = 0; i < 7; i++) {
      const date = new Date(startDate);
      date.setDate(startDate.getDate() + i);
      weekDates.push(date.toISOString().split('T')[0]);
    }

    const assignments = {};

    weekDates.forEach(date => {
      assignments[date] = {};

      appData.projects.forEach(project => {
        assignments[date][project.project_id] = appData.assignments
          .filter(a => a.assignment_date === date && a.project_id === project.project_id)
          .map(a => {
            const employee = appData.employees.find(e => e.employee_id === a.employee_id);
            return {
              ...a,
              employee
            };
          });
      });
    });

    return assignments;
  }

  /**
   * Get dashboard metrics
   * @returns {Promise<Object>} Dashboard metrics
   */
  static async getDashboardMetrics() {
    const today = new Date().toISOString().split('T')[0];

    return {
      totalEmployees: appData.employees.filter(e => e.is_active).length,
      activeProjects: appData.projects.filter(p => p.status === 'Active').length,
      todayAssignments: appData.assignments.filter(a => a.assignment_date === today).length,
      unassignedToday: await this.getUnassignedEmployees(today)
    };
  }

  /**
   * Create assignment (demo mode)
   * @param {Object} assignmentData - Assignment data
   * @returns {Promise<Object>} Created assignment
   */
  static async createAssignment(assignmentData) {
    const newAssignment = {
      assignment_id: Math.max(...appData.assignments.map(a => a.assignment_id)) + 1,
      ...assignmentData,
      status: 'Assigned'
    };

    appData.assignments.push(newAssignment);

    logger.info('Assignment created', {
      assignmentId: newAssignment.assignment_id,
      employeeId: newAssignment.employee_id,
      projectId: newAssignment.project_id
    });

    return newAssignment;
  }

  /**
   * Update assignment (demo mode)
   * @param {number} assignmentId - Assignment ID
   * @param {Object} updateData - Update data
   * @returns {Promise<Object>} Updated assignment
   */
  static async updateAssignment(assignmentId, updateData) {
    const index = appData.assignments.findIndex(a => a.assignment_id === assignmentId);

    if (index === -1) {
      throw new Error('Assignment not found');
    }

    appData.assignments[index] = {
      ...appData.assignments[index],
      ...updateData
    };

    logger.info('Assignment updated', {
      assignmentId,
      updateData
    });

    return appData.assignments[index];
  }

  /**
   * Delete assignment (demo mode)
   * @param {number} assignmentId - Assignment ID
   * @returns {Promise<boolean>} Success status
   */
  static async deleteAssignment(assignmentId) {
    const index = appData.assignments.findIndex(a => a.assignment_id === assignmentId);

    if (index === -1) {
      throw new Error('Assignment not found');
    }

    appData.assignments.splice(index, 1);

    logger.info('Assignment deleted', {
      assignmentId
    });

    return true;
  }
}

// Initialize data service when module is loaded
DataService.initialize().catch(error => {
  logger.error('Failed to initialize data service:', error);
});

module.exports = DataService;
