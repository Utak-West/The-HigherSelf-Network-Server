/**
 * Excel File Analysis Script
 *
 * Analyzes the MetroPower employee Excel file to understand its structure
 * and extract employee data for integration into the dashboard
 *
 * Copyright 2025 The HigherSelf Network
 */

const ExcelJS = require('exceljs');
const path = require('path');

async function analyzeExcelFile() {
    try {
        const filePath = path.join(__dirname, '../data/MB Week 6.16.25-6.22.25.xlsx');
        console.log('Analyzing Excel file:', filePath);

        const workbook = new ExcelJS.Workbook();
        await workbook.xlsx.readFile(filePath);

        console.log('\n=== WORKBOOK ANALYSIS ===');
        console.log('Number of worksheets:', workbook.worksheets.length);

        // Analyze each worksheet
        workbook.worksheets.forEach((worksheet, index) => {
            console.log(`\n--- Worksheet ${index + 1}: "${worksheet.name}" ---`);
            console.log('Dimensions:', worksheet.dimensions);
            console.log('Row count:', worksheet.rowCount);
            console.log('Column count:', worksheet.columnCount);

            // Show first few rows to understand structure
            console.log('\nFirst 10 rows:');
            for (let rowNumber = 1; rowNumber <= Math.min(10, worksheet.rowCount); rowNumber++) {
                const row = worksheet.getRow(rowNumber);
                const values = [];

                for (let colNumber = 1; colNumber <= Math.min(10, worksheet.columnCount); colNumber++) {
                    const cell = row.getCell(colNumber);
                    values.push(cell.value || '');
                }

                console.log(`Row ${rowNumber}:`, values);
            }

            // Analyze column headers (assuming first row contains headers)
            if (worksheet.rowCount > 0) {
                console.log('\nColumn Headers Analysis:');
                const headerRow = worksheet.getRow(1);
                for (let colNumber = 1; colNumber <= worksheet.columnCount; colNumber++) {
                    const cell = headerRow.getCell(colNumber);
                    if (cell.value) {
                        console.log(`Column ${colNumber}: "${cell.value}"`);
                    }
                }
            }
        });

        // Extract employee data from the Master List worksheet
        const masterListWorksheet = workbook.worksheets.find(ws => ws.name === 'Master List ') || workbook.worksheets[1];
        const employees = extractEmployeeData(masterListWorksheet);

        // Also extract temp labor data
        const tempLaborWorksheet = workbook.worksheets.find(ws => ws.name === 'Temp Labor');
        const tempEmployees = tempLaborWorksheet ? extractTempLaborData(tempLaborWorksheet) : [];

        // Combine all employees
        const allEmployees = [...employees, ...tempEmployees];

        console.log('\n=== EXTRACTED EMPLOYEE DATA ===');
        console.log('Regular employees found:', employees.length);
        console.log('Temp employees found:', tempEmployees.length);
        console.log('Total employees found:', allEmployees.length);

        if (allEmployees.length > 0) {
            console.log('\nSample employee records:');
            allEmployees.slice(0, 5).forEach((employee, index) => {
                console.log(`Employee ${index + 1}:`, JSON.stringify(employee, null, 2));
            });
        }

        // Save extracted data as JSON for easy integration
        const fs = require('fs');
        const outputPath = path.join(__dirname, '../data/extracted-employees.json');
        fs.writeFileSync(outputPath, JSON.stringify(allEmployees, null, 2));
        console.log(`\nExtracted data saved to: ${outputPath}`);

        return allEmployees;

    } catch (error) {
        console.error('Error analyzing Excel file:', error);
        throw error;
    }
}

function extractEmployeeData(worksheet) {
    const employees = [];

    if (!worksheet || worksheet.rowCount < 2) {
        console.log('No data rows found in worksheet');
        return employees;
    }

    // Get headers from first row
    const headerRow = worksheet.getRow(1);
    const headers = [];
    for (let colNumber = 1; colNumber <= worksheet.columnCount; colNumber++) {
        const cell = headerRow.getCell(colNumber);
        headers.push(cell.value ? String(cell.value).trim() : '');
    }

    console.log('Headers found:', headers);

    // Extract data from subsequent rows
    for (let rowNumber = 2; rowNumber <= worksheet.rowCount; rowNumber++) {
        const row = worksheet.getRow(rowNumber);
        const employee = {};
        let hasData = false;

        for (let colNumber = 1; colNumber <= headers.length; colNumber++) {
            const cell = row.getCell(colNumber);
            const header = headers[colNumber - 1];
            let value = cell.value;

            // Handle different cell value types
            if (value !== null && value !== undefined && value !== '') {
                if (typeof value === 'object' && value.formula) {
                    value = value.result || value.formula;
                }
                employee[header] = String(value).trim();
                hasData = true;
            }
        }

        // Only add employee if row has meaningful data and has a name
        if (hasData && (employee['Name'] || employee['name'])) {
            // Standardize employee data structure for Master List format
            const standardizedEmployee = standardizeMasterListEmployee(employee);
            if (standardizedEmployee) {
                employees.push(standardizedEmployee);
            }
        }
    }

    return employees;
}

function extractTempLaborData(worksheet) {
    const employees = [];

    if (!worksheet || worksheet.rowCount < 2) {
        console.log('No temp labor data found');
        return employees;
    }

    // Extract temp employees (Name and Title columns)
    for (let rowNumber = 2; rowNumber <= worksheet.rowCount; rowNumber++) {
        const row = worksheet.getRow(rowNumber);
        const nameCell = row.getCell(1);
        const titleCell = row.getCell(2);

        if (nameCell.value && titleCell.value) {
            const employee = {
                id: `temp_${rowNumber}`,
                employee_id: `TEMP${String(rowNumber).padStart(3, '0')}`,
                name: String(nameCell.value).trim(),
                first_name: String(nameCell.value).trim().split(' ')[0],
                last_name: String(nameCell.value).trim().split(' ').slice(1).join(' '),
                position: String(titleCell.value).trim(),
                trade: 'Temp Labor',
                level: 'Temporary',
                status: 'Active',
                hourly_rate: null,
                supervisor: null,
                type: 'temp'
            };

            employees.push(employee);
        }
    }

    return employees;
}

function standardizeMasterListEmployee(rawEmployee) {
    // Master List format: Name, Employee #, Reports To, Title, List Name
    const name = rawEmployee['Name'] || rawEmployee['name'] || '';
    const employeeId = rawEmployee['Employee #'] || rawEmployee['employee #'] || '';
    const supervisor = rawEmployee['Reports To'] || rawEmployee['reports to'] || '';
    const title = rawEmployee['Title'] || rawEmployee['title'] || '';
    const listName = rawEmployee['List Name'] || rawEmployee['list name'] || '';

    if (!name) return null;

    // Parse name (Last, First format)
    const nameParts = name.split(',').map(part => part.trim());
    const lastName = nameParts[0] || '';
    const firstName = nameParts[1] || '';

    // Determine trade/position from title
    let trade = 'General';
    let level = '';

    if (title.toLowerCase().includes('apprentice')) {
        trade = 'Apprentice';
        const percentMatch = title.match(/(\d+)%/);
        level = percentMatch ? `${percentMatch[1]}%` : '';
    } else if (title.toLowerCase().includes('electrician')) {
        trade = 'Electrician';
        level = title.includes('2') ? 'Level 2' : 'Level 1';
    } else if (title.toLowerCase().includes('foreman')) {
        trade = 'Field Supervisor';
        level = 'Foreman';
    } else if (title.toLowerCase().includes('superintendent')) {
        trade = 'Field Supervisor';
        level = 'Superintendent';
    } else {
        trade = title;
    }

    return {
        id: `emp_${employeeId}`,
        employee_id: String(employeeId),
        name: name,
        first_name: firstName,
        last_name: lastName,
        position: title,
        trade: trade,
        level: level,
        status: 'Active',
        hourly_rate: null,
        supervisor: supervisor,
        list_name: listName,
        type: 'regular'
    };
}

function standardizeEmployeeData(rawEmployee) {
    // Try to identify common field patterns and standardize them
    const standardized = {
        id: null,
        employee_id: null,
        name: null,
        first_name: null,
        last_name: null,
        position: null,
        trade: null,
        level: null,
        status: 'Active',
        hourly_rate: null,
        assignments: {},
        raw_data: rawEmployee
    };

    // Map common field variations to standard fields
    const fieldMappings = {
        // ID fields
        'id': ['id', 'employee_id', 'emp_id', 'number', 'employee number'],
        'employee_id': ['employee_id', 'emp_id', 'id', 'number', 'employee number'],

        // Name fields
        'name': ['name', 'full_name', 'employee_name', 'employee name'],
        'first_name': ['first_name', 'first name', 'fname'],
        'last_name': ['last_name', 'last name', 'lname'],

        // Position/Trade fields
        'position': ['position', 'job_title', 'title', 'role'],
        'trade': ['trade', 'craft', 'specialty', 'type'],
        'level': ['level', 'grade', 'classification'],

        // Rate fields
        'hourly_rate': ['hourly_rate', 'rate', 'wage', 'pay_rate', 'hourly wage']
    };

    // Apply field mappings
    Object.keys(fieldMappings).forEach(standardField => {
        const possibleFields = fieldMappings[standardField];

        for (const field of possibleFields) {
            const value = findFieldValue(rawEmployee, field);
            if (value) {
                standardized[standardField] = value;
                break;
            }
        }
    });

    // Extract assignment data (days of the week)
    const dayFields = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'];
    dayFields.forEach(day => {
        const value = findFieldValue(rawEmployee, day);
        if (value) {
            standardized.assignments[day] = value;
        }
    });

    // Only return if we have at least a name or ID
    if (standardized.name || standardized.employee_id || standardized.first_name) {
        return standardized;
    }

    return null;
}

function findFieldValue(obj, searchField) {
    const searchLower = searchField.toLowerCase();

    for (const [key, value] of Object.entries(obj)) {
        if (key.toLowerCase().includes(searchLower) || searchLower.includes(key.toLowerCase())) {
            return value;
        }
    }

    return null;
}

// Run the analysis if this script is executed directly
if (require.main === module) {
    analyzeExcelFile()
        .then(() => {
            console.log('\nAnalysis complete!');
            process.exit(0);
        })
        .catch((error) => {
            console.error('Analysis failed:', error);
            process.exit(1);
        });
}

module.exports = { analyzeExcelFile, extractEmployeeData };
