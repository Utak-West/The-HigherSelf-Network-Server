#!/bin/bash

# Complete HigherSelf Network AI Agent Enhancement Test Suite
# Runs all three project test suites in sequence

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Function to print colored output
print_header() {
    echo -e "${WHITE}${1}${NC}"
    echo -e "${WHITE}$(printf '=%.0s' {1..80})${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${CYAN}ℹ️  $1${NC}"
}

print_project() {
    echo -e "${PURPLE}🚀 $1${NC}"
}

# Check if server is running
check_server() {
    print_info "Checking if HigherSelf Network Server is running..."
    
    if curl -s http://localhost:8000/api/health/realtime > /dev/null 2>&1; then
        print_success "Server is running and responsive"
        return 0
    else
        print_error "Server is not running or not responsive"
        print_info "Please start the server with: python main_realtime_enhanced.py"
        return 1
    fi
}

# Run individual test suite
run_test_suite() {
    local test_file=$1
    local project_name=$2
    local project_number=$3
    
    print_project "Running $project_name"
    echo ""
    
    if [ -f "$test_file" ]; then
        if python3 "$test_file"; then
            print_success "$project_name completed successfully"
            return 0
        else
            print_error "$project_name failed"
            return 1
        fi
    else
        print_error "Test file $test_file not found"
        return 1
    fi
}

# Generate summary report
generate_summary() {
    local project1_result=$1
    local project2_result=$2
    local project3_result=$3
    
    print_header "🎯 COMPLETE TEST SUITE SUMMARY"
    echo ""
    
    # Project results
    if [ $project1_result -eq 0 ]; then
        print_success "Project 1: Real-Time AI Agent Contact Processing Pipeline"
    else
        print_error "Project 1: Real-Time AI Agent Contact Processing Pipeline"
    fi
    
    if [ $project2_result -eq 0 ]; then
        print_success "Project 2: Multi-Entity Intelligent Workflow Expansion"
    else
        print_error "Project 2: Multi-Entity Intelligent Workflow Expansion"
    fi
    
    if [ $project3_result -eq 0 ]; then
        print_success "Project 3: Bidirectional Notion Intelligence Hub"
    else
        print_error "Project 3: Bidirectional Notion Intelligence Hub"
    fi
    
    echo ""
    
    # Overall result
    local total_passed=$((3 - project1_result - project2_result - project3_result))
    local success_rate=$((total_passed * 100 / 3))
    
    if [ $total_passed -eq 3 ]; then
        print_success "🎉 ALL PROJECTS PASSED! Success Rate: 100%"
        echo ""
        print_info "Your HigherSelf Network Server AI Agent Enhancement is complete!"
        print_info "All three high-impact projects are working correctly:"
        echo "  • Real-time contact processing with AI intelligence"
        echo "  • Multi-entity workflow automation across all business entities"
        echo "  • Bidirectional Notion synchronization with AI enrichment"
        echo ""
        print_success "Ready for production deployment! 🚀"
    elif [ $total_passed -eq 2 ]; then
        print_warning "⚠️  MOSTLY SUCCESSFUL! Success Rate: ${success_rate}%"
        echo ""
        print_info "Two out of three projects are working correctly."
        print_info "Please review the failed project and address any issues."
    elif [ $total_passed -eq 1 ]; then
        print_warning "⚠️  PARTIAL SUCCESS! Success Rate: ${success_rate}%"
        echo ""
        print_info "One out of three projects is working correctly."
        print_info "Please review the failed projects and address any issues."
    else
        print_error "❌ ALL PROJECTS FAILED! Success Rate: 0%"
        echo ""
        print_info "Please check the server status and configuration."
        print_info "Review the troubleshooting guide in COMPLETE_DEPLOYMENT_GUIDE.md"
    fi
    
    echo ""
    print_info "Detailed test results are saved in individual JSON files:"
    echo "  • test_results_realtime_ai.json"
    echo "  • test_results_project2_multi_entity.json"
    echo "  • test_results_project3_notion_intelligence.json"
}

# Main execution
main() {
    print_header "🚀 HigherSelf Network AI Agent Enhancement - Complete Test Suite"
    echo ""
    print_info "Testing all three high-impact AI agent enhancement projects..."
    echo ""
    
    # Check server status
    if ! check_server; then
        exit 1
    fi
    
    echo ""
    
    # Initialize result variables
    project1_result=1
    project2_result=1
    project3_result=1
    
    # Run Project 1 tests
    print_header "PROJECT 1: Real-Time AI Agent Contact Processing Pipeline"
    if run_test_suite "test_realtime_ai_integration.py" "Project 1: Real-Time AI Agent Contact Processing Pipeline" "1"; then
        project1_result=0
    fi
    echo ""
    
    # Small delay between test suites
    sleep 2
    
    # Run Project 2 tests
    print_header "PROJECT 2: Multi-Entity Intelligent Workflow Expansion"
    if run_test_suite "test_project2_multi_entity.py" "Project 2: Multi-Entity Intelligent Workflow Expansion" "2"; then
        project2_result=0
    fi
    echo ""
    
    # Small delay between test suites
    sleep 2
    
    # Run Project 3 tests
    print_header "PROJECT 3: Bidirectional Notion Intelligence Hub"
    if run_test_suite "test_project3_notion_intelligence.py" "Project 3: Bidirectional Notion Intelligence Hub" "3"; then
        project3_result=0
    fi
    echo ""
    
    # Generate summary report
    generate_summary $project1_result $project2_result $project3_result
    
    # Return overall success status
    if [ $project1_result -eq 0 ] && [ $project2_result -eq 0 ] && [ $project3_result -eq 0 ]; then
        exit 0
    else
        exit 1
    fi
}

# Run main function
main "$@"
