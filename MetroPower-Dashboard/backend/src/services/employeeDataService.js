/**
 * Employee Data Service
 *
 * Loads and manages real employee data from the Excel file
 * for the MetroPower Dashboard.
 *
 * Copyright 2025 The HigherSelf Network
 */

const fs = require('fs');
const path = require('path');
const logger = require('../utils/logger');

class EmployeeDataService {
  constructor() {
    this.employees = [];
    this.projects = [];
    this.loaded = false;
  }

  /**
   * Load employee data from the extracted JSON file
   */
  async loadEmployeeData() {
    try {
      const dataPath = path.join(__dirname, '../../data/extracted-employees.json');

      if (!fs.existsSync(dataPath)) {
        logger.warn('Employee data file not found, using demo data');
        return false;
      }

      const rawData = fs.readFileSync(dataPath, 'utf8');
      const employeeData = JSON.parse(rawData);

      // Transform the data to match our expected format
      this.employees = employeeData.map((emp, index) => ({
        employee_id: emp.employee_id || `emp_${index + 1}`,
        first_name: emp.first_name || '',
        last_name: emp.last_name || '',
        name: emp.name || `${emp.first_name} ${emp.last_name}`,
        trade: emp.trade || 'General',
        level: emp.level || '',
        position: emp.position || emp.trade,
        hourly_rate: emp.hourly_rate || this.estimateHourlyRate(emp.trade, emp.level),
        is_active: emp.status === 'Active',
        supervisor: emp.supervisor || null,
        type: emp.type || 'regular',
        hire_date: this.generateHireDate(),
        phone: this.generatePhoneNumber(),
        email: this.generateEmail(emp.first_name, emp.last_name)
      }));

      // Generate sample projects based on real MetroPower work
      this.projects = this.generateProjects();

      this.loaded = true;
      logger.info(`Loaded ${this.employees.length} employees from Excel data`);

      // Log statistics
      const stats = this.getEmployeeStatistics();
      logger.info('Employee statistics:', stats);

      return true;
    } catch (error) {
      logger.error('Error loading employee data:', error);
      return false;
    }
  }

  /**
   * Get employee statistics
   */
  getEmployeeStatistics() {
    const stats = {
      total: this.employees.length,
      active: this.employees.filter(e => e.is_active).length,
      byTrade: {},
      byType: {}
    };

    this.employees.forEach(emp => {
      // Count by trade
      if (!stats.byTrade[emp.trade]) {
        stats.byTrade[emp.trade] = 0;
      }
      stats.byTrade[emp.trade]++;

      // Count by type
      if (!stats.byType[emp.type]) {
        stats.byType[emp.type] = 0;
      }
      stats.byType[emp.type]++;
    });

    return stats;
  }

  /**
   * Estimate hourly rate based on trade and level
   */
  estimateHourlyRate(trade, level) {
    const rates = {
      'Apprentice': {
        '40%': 18.50,
        '45%': 20.00,
        '60%': 22.50,
        '80%': 25.00,
        '85%': 26.50,
        'default': 20.00
      },
      'Electrician': {
        'Level 1': 28.00,
        'Level 2': 32.00,
        'Level 3': 35.00,
        'default': 30.00
      },
      'Field Supervisor': {
        'Foreman': 38.00,
        'Superintendent': 45.00,
        'default': 40.00
      },
      'Service Technician': {
        'default': 32.00
      },
      'Temp Labor': {
        'default': 16.00
      }
    };

    const tradeRates = rates[trade] || { default: 25.00 };
    return tradeRates[level] || tradeRates.default;
  }

  /**
   * Generate realistic hire date
   */
  generateHireDate() {
    const now = new Date();
    const yearsBack = Math.random() * 5; // 0-5 years ago
    const hireDate = new Date(now.getTime() - (yearsBack * 365 * 24 * 60 * 60 * 1000));
    return hireDate.toISOString().split('T')[0];
  }

  /**
   * Generate phone number
   */
  generatePhoneNumber() {
    const area = '770'; // Atlanta area code
    const exchange = Math.floor(Math.random() * 900) + 100;
    const number = Math.floor(Math.random() * 9000) + 1000;
    return `${area}-${exchange}-${number}`;
  }

  /**
   * Generate email address
   */
  generateEmail(firstName, lastName) {
    if (!firstName || !lastName) return 'employee@metropower.com';

    const first = firstName.toLowerCase().replace(/[^a-z]/g, '');
    const last = lastName.toLowerCase().replace(/[^a-z]/g, '');
    return `${first}.${last}@metropower.com`;
  }

  /**
   * Generate realistic projects
   */
  generateProjects() {
    return [
      {
        project_id: 1,
        project_name: 'Tucker Mall Renovation - Phase 2',
        project_code: 'TM-2025-001',
        client_name: 'Tucker Development Corp',
        start_date: '2025-01-15',
        end_date: '2025-08-30',
        status: 'Active',
        project_manager: 'Antoine Harrell',
        estimated_hours: 3200,
        actual_hours: 800
      },
      {
        project_id: 2,
        project_name: 'Northlake Office Complex',
        project_code: 'NOC-2025-002',
        client_name: 'Northlake Business Park',
        start_date: '2025-02-01',
        end_date: '2025-07-15',
        status: 'Active',
        project_manager: 'Antoine Harrell',
        estimated_hours: 2800,
        actual_hours: 600
      },
      {
        project_id: 3,
        project_name: 'Stone Mountain Residential',
        project_code: 'SMR-2025-003',
        client_name: 'Stone Mountain Homes LLC',
        start_date: '2025-03-01',
        end_date: '2025-10-31',
        status: 'Active',
        project_manager: 'Antoine Harrell',
        estimated_hours: 4200,
        actual_hours: 400
      },
      {
        project_id: 4,
        project_name: 'Decatur Hospital Upgrade',
        project_code: 'DHU-2025-004',
        client_name: 'Decatur Medical Center',
        start_date: '2025-04-01',
        end_date: '2025-09-30',
        status: 'Active',
        project_manager: 'Antoine Harrell',
        estimated_hours: 2400,
        actual_hours: 200
      }
    ];
  }

  /**
   * Get all employees
   */
  getEmployees() {
    return [...this.employees];
  }

  /**
   * Get employees by trade
   */
  getEmployeesByTrade(trade) {
    return this.employees.filter(emp => emp.trade === trade && emp.is_active);
  }

  /**
   * Get all projects
   */
  getProjects() {
    return [...this.projects];
  }

  /**
   * Get active projects
   */
  getActiveProjects() {
    return this.projects.filter(p => p.status === 'Active');
  }

  /**
   * Check if data is loaded
   */
  isLoaded() {
    return this.loaded;
  }
}

// Create singleton instance
const employeeDataService = new EmployeeDataService();

module.exports = employeeDataService;
