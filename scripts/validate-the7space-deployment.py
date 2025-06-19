#!/usr/bin/env python3
"""
The 7 Space Deployment Validation Script

Comprehensive validation script for The 7 Space Art Gallery & Wellness Center
production deployment. Validates all services, integrations, and business logic.
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
import requests
import subprocess
from dataclasses import dataclass, asdict

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f'logs/the7space-validation-{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """Validation result data structure"""
    test_name: str
    status: str  # "PASS", "FAIL", "WARNING"
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

class The7SpaceDeploymentValidator:
    """
    Comprehensive deployment validator for The 7 Space production environment.
    """
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.results: List[ValidationResult] = []
        self.docker_compose_file = "docker-compose.the7space.prod.yml"
        
        # Load environment configuration
        self.load_environment_config()
    
    def load_environment_config(self):
        """Load environment configuration from .env file"""
        env_file = ".env.the7space.production"
        if os.path.exists(env_file):
            with open(env_file, 'r') as f:
                for line in f:
                    if '=' in line and not line.strip().startswith('#'):
                        key, value = line.strip().split('=', 1)
                        os.environ[key] = value
    
    def add_result(self, test_name: str, status: str, message: str, details: Optional[Dict] = None):
        """Add validation result"""
        result = ValidationResult(test_name, status, message, details)
        self.results.append(result)
        
        # Log result
        if status == "PASS":
            logger.info(f"✅ {test_name}: {message}")
        elif status == "WARNING":
            logger.warning(f"⚠️  {test_name}: {message}")
        else:
            logger.error(f"❌ {test_name}: {message}")
    
    def validate_docker_services(self) -> bool:
        """Validate Docker services are running and healthy"""
        logger.info("🐳 Validating Docker services...")
        
        try:
            # Check if Docker Compose file exists
            if not os.path.exists(self.docker_compose_file):
                self.add_result(
                    "Docker Compose File",
                    "FAIL",
                    f"Docker Compose file not found: {self.docker_compose_file}"
                )
                return False
            
            # Get service status
            result = subprocess.run(
                ["docker-compose", "-f", self.docker_compose_file, "ps", "--format", "json"],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                self.add_result(
                    "Docker Services Status",
                    "FAIL",
                    f"Failed to get service status: {result.stderr}"
                )
                return False
            
            # Parse service status
            services = []
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    try:
                        service = json.loads(line)
                        services.append(service)
                    except json.JSONDecodeError:
                        continue
            
            if not services:
                self.add_result(
                    "Docker Services",
                    "FAIL",
                    "No services found running"
                )
                return False
            
            # Check each service
            all_healthy = True
            service_details = {}
            
            for service in services:
                service_name = service.get('Service', 'Unknown')
                state = service.get('State', 'Unknown')
                health = service.get('Health', 'Unknown')
                
                service_details[service_name] = {
                    'state': state,
                    'health': health
                }
                
                if state != 'running':
                    self.add_result(
                        f"Service {service_name}",
                        "FAIL",
                        f"Service not running: {state}"
                    )
                    all_healthy = False
                elif health == 'unhealthy':
                    self.add_result(
                        f"Service {service_name}",
                        "FAIL",
                        f"Service unhealthy: {health}"
                    )
                    all_healthy = False
                else:
                    self.add_result(
                        f"Service {service_name}",
                        "PASS",
                        f"Service running and healthy"
                    )
            
            self.add_result(
                "Docker Services Overall",
                "PASS" if all_healthy else "FAIL",
                f"Services status: {len([s for s in services if s.get('State') == 'running'])}/{len(services)} running",
                service_details
            )
            
            return all_healthy
            
        except Exception as e:
            self.add_result(
                "Docker Services Validation",
                "FAIL",
                f"Exception during validation: {str(e)}"
            )
            return False
    
    def validate_application_health(self) -> bool:
        """Validate main application health endpoints"""
        logger.info("🏥 Validating application health...")
        
        try:
            # Test main health endpoint
            response = requests.get(f"{self.base_url}/health", timeout=30)
            
            if response.status_code == 200:
                health_data = response.json()
                self.add_result(
                    "Application Health",
                    "PASS",
                    "Main health endpoint responding",
                    health_data
                )
            else:
                self.add_result(
                    "Application Health",
                    "FAIL",
                    f"Health endpoint returned status {response.status_code}"
                )
                return False
            
            # Test database health
            try:
                db_response = requests.get(f"{self.base_url}/health/database", timeout=15)
                if db_response.status_code == 200:
                    self.add_result(
                        "Database Health",
                        "PASS",
                        "Database connectivity healthy"
                    )
                else:
                    self.add_result(
                        "Database Health",
                        "WARNING",
                        f"Database health check returned status {db_response.status_code}"
                    )
            except requests.RequestException as e:
                self.add_result(
                    "Database Health",
                    "WARNING",
                    f"Database health check failed: {str(e)}"
                )
            
            # Test external services health
            try:
                ext_response = requests.get(f"{self.base_url}/health/external", timeout=20)
                if ext_response.status_code == 200:
                    self.add_result(
                        "External Services Health",
                        "PASS",
                        "External services connectivity healthy"
                    )
                else:
                    self.add_result(
                        "External Services Health",
                        "WARNING",
                        f"External services health check returned status {ext_response.status_code}"
                    )
            except requests.RequestException as e:
                self.add_result(
                    "External Services Health",
                    "WARNING",
                    f"External services health check failed: {str(e)}"
                )
            
            return True
            
        except requests.RequestException as e:
            self.add_result(
                "Application Health",
                "FAIL",
                f"Failed to connect to application: {str(e)}"
            )
            return False
    
    def validate_the7space_functionality(self) -> bool:
        """Validate The 7 Space specific functionality"""
        logger.info("🎨 Validating The 7 Space specific functionality...")
        
        try:
            # Test contact management endpoint
            try:
                contact_response = requests.get(
                    f"{self.base_url}/api/the7space/contacts/health",
                    timeout=15
                )
                if contact_response.status_code == 200:
                    self.add_result(
                        "Contact Management",
                        "PASS",
                        "Contact management system operational"
                    )
                else:
                    self.add_result(
                        "Contact Management",
                        "WARNING",
                        f"Contact management returned status {contact_response.status_code}"
                    )
            except requests.RequestException as e:
                self.add_result(
                    "Contact Management",
                    "WARNING",
                    f"Contact management check failed: {str(e)}"
                )
            
            # Test workflow automation endpoint
            try:
                workflow_response = requests.get(
                    f"{self.base_url}/api/the7space/workflows/health",
                    timeout=15
                )
                if workflow_response.status_code == 200:
                    self.add_result(
                        "Workflow Automation",
                        "PASS",
                        "Workflow automation system operational"
                    )
                else:
                    self.add_result(
                        "Workflow Automation",
                        "WARNING",
                        f"Workflow automation returned status {workflow_response.status_code}"
                    )
            except requests.RequestException as e:
                self.add_result(
                    "Workflow Automation",
                    "WARNING",
                    f"Workflow automation check failed: {str(e)}"
                )
            
            # Test gallery management endpoint
            try:
                gallery_response = requests.get(
                    f"{self.base_url}/api/the7space/gallery/health",
                    timeout=15
                )
                if gallery_response.status_code == 200:
                    self.add_result(
                        "Gallery Management",
                        "PASS",
                        "Gallery management system operational"
                    )
                else:
                    self.add_result(
                        "Gallery Management",
                        "WARNING",
                        f"Gallery management returned status {gallery_response.status_code}"
                    )
            except requests.RequestException as e:
                self.add_result(
                    "Gallery Management",
                    "WARNING",
                    f"Gallery management check failed: {str(e)}"
                )
            
            # Test wellness center endpoint
            try:
                wellness_response = requests.get(
                    f"{self.base_url}/api/the7space/wellness/health",
                    timeout=15
                )
                if wellness_response.status_code == 200:
                    self.add_result(
                        "Wellness Center",
                        "PASS",
                        "Wellness center system operational"
                    )
                else:
                    self.add_result(
                        "Wellness Center",
                        "WARNING",
                        f"Wellness center returned status {wellness_response.status_code}"
                    )
            except requests.RequestException as e:
                self.add_result(
                    "Wellness Center",
                    "WARNING",
                    f"Wellness center check failed: {str(e)}"
                )
            
            return True
            
        except Exception as e:
            self.add_result(
                "The 7 Space Functionality",
                "FAIL",
                f"Exception during functionality validation: {str(e)}"
            )
            return False
    
    def validate_integrations(self) -> bool:
        """Validate external integrations"""
        logger.info("🔗 Validating external integrations...")
        
        try:
            # Test Notion integration
            notion_token = os.getenv('NOTION_API_TOKEN')
            if notion_token and notion_token != 'CHANGE_IN_PRODUCTION_NOTION_TOKEN':
                try:
                    notion_response = requests.get(
                        f"{self.base_url}/api/integrations/notion/health",
                        timeout=20
                    )
                    if notion_response.status_code == 200:
                        self.add_result(
                            "Notion Integration",
                            "PASS",
                            "Notion integration operational"
                        )
                    else:
                        self.add_result(
                            "Notion Integration",
                            "WARNING",
                            f"Notion integration returned status {notion_response.status_code}"
                        )
                except requests.RequestException as e:
                    self.add_result(
                        "Notion Integration",
                        "WARNING",
                        f"Notion integration check failed: {str(e)}"
                    )
            else:
                self.add_result(
                    "Notion Integration",
                    "WARNING",
                    "Notion API token not configured"
                )
            
            # Test WordPress integration
            wp_url = os.getenv('THE_7_SPACE_WORDPRESS_URL')
            if wp_url and wp_url != 'https://the7space.com':
                try:
                    wp_response = requests.get(
                        f"{self.base_url}/api/integrations/wordpress/health",
                        timeout=20
                    )
                    if wp_response.status_code == 200:
                        self.add_result(
                            "WordPress Integration",
                            "PASS",
                            "WordPress integration operational"
                        )
                    else:
                        self.add_result(
                            "WordPress Integration",
                            "WARNING",
                            f"WordPress integration returned status {wp_response.status_code}"
                        )
                except requests.RequestException as e:
                    self.add_result(
                        "WordPress Integration",
                        "WARNING",
                        f"WordPress integration check failed: {str(e)}"
                    )
            else:
                self.add_result(
                    "WordPress Integration",
                    "WARNING",
                    "WordPress URL not configured or using default"
                )
            
            # Test OpenAI integration
            openai_key = os.getenv('OPENAI_API_KEY')
            if openai_key and openai_key != 'CHANGE_IN_PRODUCTION_OPENAI_KEY':
                try:
                    openai_response = requests.get(
                        f"{self.base_url}/api/integrations/openai/health",
                        timeout=15
                    )
                    if openai_response.status_code == 200:
                        self.add_result(
                            "OpenAI Integration",
                            "PASS",
                            "OpenAI integration operational"
                        )
                    else:
                        self.add_result(
                            "OpenAI Integration",
                            "WARNING",
                            f"OpenAI integration returned status {openai_response.status_code}"
                        )
                except requests.RequestException as e:
                    self.add_result(
                        "OpenAI Integration",
                        "WARNING",
                        f"OpenAI integration check failed: {str(e)}"
                    )
            else:
                self.add_result(
                    "OpenAI Integration",
                    "WARNING",
                    "OpenAI API key not configured"
                )
            
            return True
            
        except Exception as e:
            self.add_result(
                "Integration Validation",
                "FAIL",
                f"Exception during integration validation: {str(e)}"
            )
            return False
    
    def validate_performance(self) -> bool:
        """Validate performance metrics"""
        logger.info("⚡ Validating performance metrics...")
        
        try:
            # Test response time
            start_time = time.time()
            response = requests.get(f"{self.base_url}/health", timeout=30)
            response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            if response_time < 500:
                self.add_result(
                    "Response Time",
                    "PASS",
                    f"Response time: {response_time:.2f}ms (target: <500ms)"
                )
            elif response_time < 1000:
                self.add_result(
                    "Response Time",
                    "WARNING",
                    f"Response time: {response_time:.2f}ms (target: <500ms)"
                )
            else:
                self.add_result(
                    "Response Time",
                    "FAIL",
                    f"Response time: {response_time:.2f}ms (target: <500ms)"
                )
            
            # Test concurrent requests (simple load test)
            logger.info("Testing concurrent request handling...")
            concurrent_requests = 10
            start_time = time.time()
            
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_requests) as executor:
                futures = [
                    executor.submit(requests.get, f"{self.base_url}/health", timeout=30)
                    for _ in range(concurrent_requests)
                ]
                
                successful_requests = 0
                for future in concurrent.futures.as_completed(futures):
                    try:
                        response = future.result()
                        if response.status_code == 200:
                            successful_requests += 1
                    except Exception:
                        pass
            
            total_time = time.time() - start_time
            success_rate = (successful_requests / concurrent_requests) * 100
            
            if success_rate >= 95:
                self.add_result(
                    "Concurrent Request Handling",
                    "PASS",
                    f"Success rate: {success_rate:.1f}% ({successful_requests}/{concurrent_requests})"
                )
            elif success_rate >= 80:
                self.add_result(
                    "Concurrent Request Handling",
                    "WARNING",
                    f"Success rate: {success_rate:.1f}% ({successful_requests}/{concurrent_requests})"
                )
            else:
                self.add_result(
                    "Concurrent Request Handling",
                    "FAIL",
                    f"Success rate: {success_rate:.1f}% ({successful_requests}/{concurrent_requests})"
                )
            
            return True
            
        except Exception as e:
            self.add_result(
                "Performance Validation",
                "FAIL",
                f"Exception during performance validation: {str(e)}"
            )
            return False
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive validation report"""
        logger.info("📊 Generating validation report...")
        
        # Count results by status
        pass_count = len([r for r in self.results if r.status == "PASS"])
        warning_count = len([r for r in self.results if r.status == "WARNING"])
        fail_count = len([r for r in self.results if r.status == "FAIL"])
        total_count = len(self.results)
        
        # Calculate overall status
        if fail_count > 0:
            overall_status = "FAIL"
        elif warning_count > 0:
            overall_status = "WARNING"
        else:
            overall_status = "PASS"
        
        # Generate report
        report = {
            "validation_timestamp": datetime.now().isoformat(),
            "overall_status": overall_status,
            "summary": {
                "total_tests": total_count,
                "passed": pass_count,
                "warnings": warning_count,
                "failed": fail_count,
                "success_rate": f"{(pass_count / total_count * 100):.1f}%" if total_count > 0 else "0%"
            },
            "results": [asdict(result) for result in self.results],
            "recommendations": self.generate_recommendations()
        }
        
        return report
    
    def generate_recommendations(self) -> List[str]:
        """Generate recommendations based on validation results"""
        recommendations = []
        
        # Check for failed tests
        failed_tests = [r for r in self.results if r.status == "FAIL"]
        if failed_tests:
            recommendations.append("Address all failed tests before proceeding to production")
            for test in failed_tests:
                recommendations.append(f"- Fix {test.test_name}: {test.message}")
        
        # Check for warnings
        warning_tests = [r for r in self.results if r.status == "WARNING"]
        if warning_tests:
            recommendations.append("Review and address warning conditions:")
            for test in warning_tests:
                recommendations.append(f"- Review {test.test_name}: {test.message}")
        
        # General recommendations
        if not failed_tests and not warning_tests:
            recommendations.append("All tests passed! The 7 Space deployment is ready for production use.")
            recommendations.append("Continue monitoring system performance and health.")
            recommendations.append("Set up regular automated health checks and monitoring.")
        
        return recommendations
    
    async def run_validation(self) -> Dict[str, Any]:
        """Run complete validation suite"""
        logger.info("🚀 Starting The 7 Space deployment validation...")
        
        # Run validation steps
        docker_ok = self.validate_docker_services()
        
        if docker_ok:
            # Wait a moment for services to fully initialize
            logger.info("⏳ Waiting for services to fully initialize...")
            time.sleep(10)
            
            app_ok = self.validate_application_health()
            
            if app_ok:
                self.validate_the7space_functionality()
                self.validate_integrations()
                self.validate_performance()
        
        # Generate and return report
        report = self.generate_report()
        
        # Save report to file
        report_file = f"logs/the7space-validation-report-{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs(os.path.dirname(report_file), exist_ok=True)
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"📄 Validation report saved to: {report_file}")
        
        return report

def main():
    """Main validation function"""
    print("🎨 The 7 Space Deployment Validation")
    print("=" * 50)
    
    validator = The7SpaceDeploymentValidator()
    
    try:
        # Run validation
        report = asyncio.run(validator.run_validation())
        
        # Print summary
        print("\n📊 Validation Summary:")
        print(f"Overall Status: {report['overall_status']}")
        print(f"Total Tests: {report['summary']['total_tests']}")
        print(f"Passed: {report['summary']['passed']}")
        print(f"Warnings: {report['summary']['warnings']}")
        print(f"Failed: {report['summary']['failed']}")
        print(f"Success Rate: {report['summary']['success_rate']}")
        
        # Print recommendations
        if report['recommendations']:
            print("\n💡 Recommendations:")
            for rec in report['recommendations']:
                print(f"  {rec}")
        
        # Exit with appropriate code
        if report['overall_status'] == "FAIL":
            print("\n❌ Validation failed. Please address the issues above.")
            sys.exit(1)
        elif report['overall_status'] == "WARNING":
            print("\n⚠️  Validation completed with warnings. Review recommendations.")
            sys.exit(0)
        else:
            print("\n✅ Validation passed successfully!")
            sys.exit(0)
            
    except Exception as e:
        logger.error(f"Validation failed with exception: {str(e)}")
        print(f"\n❌ Validation failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
