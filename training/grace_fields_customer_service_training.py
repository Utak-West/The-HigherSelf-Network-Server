#!/usr/bin/env python3
"""
Grace Fields Customer Service Training Module

This module provides comprehensive training scenarios and evaluation
for the enhanced Grace Fields customer service orchestration system.
"""

import asyncio
import json
import random
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger

from agents.grace_fields_enhanced import EnhancedGraceFields
from models.customer_service_models import (
    BusinessEntity,
    IssueCategory,
    SeverityLevel,
    CustomerSentiment,
    CustomerServiceRequest
)
from services.escalation_service import EscalationService
from services.notion_service import NotionService


class CustomerServiceTrainingScenario:
    """Training scenario for customer service situations."""
    
    def __init__(
        self,
        scenario_id: str,
        name: str,
        description: str,
        customer_email: str,
        customer_name: str,
        business_entity: BusinessEntity,
        issue_description: str,
        expected_category: IssueCategory,
        expected_severity: SeverityLevel,
        expected_agents: List[str],
        success_criteria: List[str],
        customer_sentiment: CustomerSentiment = CustomerSentiment.NEUTRAL,
        priority: str = "medium"
    ):
        self.scenario_id = scenario_id
        self.name = name
        self.description = description
        self.customer_email = customer_email
        self.customer_name = customer_name
        self.business_entity = business_entity
        self.issue_description = issue_description
        self.expected_category = expected_category
        self.expected_severity = expected_severity
        self.expected_agents = expected_agents
        self.success_criteria = success_criteria
        self.customer_sentiment = customer_sentiment
        self.priority = priority


class GraceFieldsCustomerServiceTrainer:
    """Trainer for Grace Fields customer service capabilities."""
    
    def __init__(self, enhanced_grace: EnhancedGraceFields):
        self.enhanced_grace = enhanced_grace
        self.training_scenarios = self._create_training_scenarios()
        self.training_results = []
        
    def _create_training_scenarios(self) -> List[CustomerServiceTrainingScenario]:
        """Create comprehensive training scenarios."""
        scenarios = [
            # Level 1 - Standard Delegation Scenarios
            CustomerServiceTrainingScenario(
                scenario_id="L1-001",
                name="Simple Booking Change",
                description="Customer wants to reschedule their wellness appointment",
                customer_email="sarah.wellness@example.com",
                customer_name="Sarah Johnson",
                business_entity=BusinessEntity.WELLNESS_CENTER,
                issue_description="I need to reschedule my massage appointment from Tuesday to Thursday",
                expected_category=IssueCategory.BILLING_ORDER,
                expected_severity=SeverityLevel.LEVEL_1,
                expected_agents=["Solari"],
                success_criteria=["Single agent delegation", "Appropriate response time", "Professional tone"]
            ),
            
            CustomerServiceTrainingScenario(
                scenario_id="L1-002",
                name="General Inquiry",
                description="New customer asking about art gallery services",
                customer_email="art.lover@example.com",
                customer_name="Michael Chen",
                business_entity=BusinessEntity.ART_GALLERY,
                issue_description="I'm interested in learning about your art collection and viewing appointments",
                expected_category=IssueCategory.LEAD_MANAGEMENT,
                expected_severity=SeverityLevel.LEVEL_1,
                expected_agents=["Nyra"],
                success_criteria=["Lead qualification", "Appropriate follow-up", "Business entity awareness"]
            ),
            
            # Level 2 - Multi-Agent Coordination Scenarios
            CustomerServiceTrainingScenario(
                scenario_id="L2-001",
                name="Complex Service Package",
                description="Customer wants multiple coordinated services",
                customer_email="executive@company.com",
                customer_name="Jennifer Rodriguez",
                business_entity=BusinessEntity.CONSULTANCY,
                issue_description="I need a comprehensive package including strategic consulting, team wellness programs, and executive coaching",
                expected_category=IssueCategory.TASK_COORDINATION,
                expected_severity=SeverityLevel.LEVEL_2,
                expected_agents=["Ruvo", "Solari", "Nyra"],
                success_criteria=["Multi-agent coordination", "Workflow creation", "Clear communication"]
            ),
            
            CustomerServiceTrainingScenario(
                scenario_id="L2-002",
                name="Marketing Campaign Request",
                description="Client wants comprehensive marketing support",
                customer_email="gallery.owner@artworld.com",
                customer_name="David Kim",
                business_entity=BusinessEntity.ART_GALLERY,
                issue_description="We're launching a new exhibition and need marketing strategy, content creation, and audience analysis",
                expected_category=IssueCategory.MARKETING_CAMPAIGN,
                expected_severity=SeverityLevel.LEVEL_2,
                expected_agents=["Liora", "Zevi", "Elan", "Nyra"],
                success_criteria=["Strategic coordination", "Content planning", "Analytics integration"]
            ),
            
            # Level 3 - Full Network Response Scenarios
            CustomerServiceTrainingScenario(
                scenario_id="L3-001",
                name="VIP Client Onboarding",
                description="High-value client needs comprehensive onboarding",
                customer_email="vip.client@luxury.com",
                customer_name="Elizabeth Thornton",
                business_entity=BusinessEntity.LUXURY_RENOVATIONS,
                issue_description="As a VIP client, I need white-glove service for my luxury home renovation project including design, project management, and premium materials sourcing",
                expected_category=IssueCategory.VIP_SERVICE,
                expected_severity=SeverityLevel.LEVEL_3,
                expected_agents=["Nyra", "Zevi", "Liora", "Solari", "Ruvo", "Sage", "Elan"],
                success_criteria=["Full network activation", "VIP treatment", "Comprehensive coordination"],
                priority="high"
            ),
            
            CustomerServiceTrainingScenario(
                scenario_id="L3-002",
                name="Service Recovery",
                description="Dissatisfied customer needs service recovery",
                customer_email="disappointed@client.com",
                customer_name="Robert Martinez",
                business_entity=BusinessEntity.WELLNESS_CENTER,
                issue_description="I'm extremely disappointed with my recent retreat experience. The accommodations were subpar, the schedule was disorganized, and I feel like I wasted my money",
                expected_category=IssueCategory.CUSTOMER_FEEDBACK,
                expected_severity=SeverityLevel.LEVEL_3,
                expected_agents=["Sage", "Grace", "Solari", "Ruvo", "Elan"],
                success_criteria=["Service recovery protocol", "Empathetic response", "Comprehensive resolution"],
                customer_sentiment=CustomerSentiment.FRUSTRATED,
                priority="high"
            ),
            
            # Level 4 - Human Escalation Scenarios
            CustomerServiceTrainingScenario(
                scenario_id="L4-001",
                name="Legal Compliance Issue",
                description="Customer has legal compliance questions",
                customer_email="legal@corporation.com",
                customer_name="Amanda Foster",
                business_entity=BusinessEntity.CONSULTANCY,
                issue_description="We need to discuss GDPR compliance requirements for our data handling practices and potential liability issues",
                expected_category=IssueCategory.LEGAL_COMPLIANCE,
                expected_severity=SeverityLevel.LEVEL_4,
                expected_agents=[],
                success_criteria=["Immediate escalation", "Legal recognition", "Human specialist notification"],
                priority="urgent"
            ),
            
            CustomerServiceTrainingScenario(
                scenario_id="L4-002",
                name="High-Value Refund",
                description="Customer requesting large refund",
                customer_email="collector@artworld.com",
                customer_name="Charles Wellington",
                business_entity=BusinessEntity.ART_GALLERY,
                issue_description="I need to return this $15,000 sculpture due to authenticity concerns and require a full refund immediately",
                expected_category=IssueCategory.BILLING_ORDER,
                expected_severity=SeverityLevel.LEVEL_4,
                expected_agents=[],
                success_criteria=["Human escalation", "High-value recognition", "Urgent handling"],
                priority="urgent"
            )
        ]
        
        return scenarios
    
    async def run_training_scenario(self, scenario: CustomerServiceTrainingScenario) -> Dict[str, Any]:
        """Run a single training scenario and evaluate results."""
        logger.info(f"Running training scenario: {scenario.name}")
        
        start_time = datetime.now()
        
        try:
            # Process the customer service request
            result = await self.enhanced_grace.process_customer_service_request(
                customer_email=scenario.customer_email,
                description=scenario.issue_description,
                business_entity=scenario.business_entity,
                customer_name=scenario.customer_name,
                priority=scenario.priority
            )
            
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            # Evaluate the result
            evaluation = self._evaluate_scenario_result(scenario, result, processing_time)
            
            return {
                "scenario_id": scenario.scenario_id,
                "scenario_name": scenario.name,
                "result": result,
                "evaluation": evaluation,
                "processing_time_seconds": processing_time,
                "timestamp": start_time.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in training scenario {scenario.scenario_id}: {e}")
            return {
                "scenario_id": scenario.scenario_id,
                "scenario_name": scenario.name,
                "error": str(e),
                "evaluation": {"overall_score": 0, "passed": False},
                "processing_time_seconds": 0,
                "timestamp": start_time.isoformat()
            }
    
    def _evaluate_scenario_result(
        self,
        scenario: CustomerServiceTrainingScenario,
        result: Dict[str, Any],
        processing_time: float
    ) -> Dict[str, Any]:
        """Evaluate the result of a training scenario."""
        evaluation = {
            "overall_score": 0,
            "max_score": 100,
            "passed": False,
            "criteria_scores": {},
            "feedback": []
        }
        
        # Check severity level handling (20 points)
        if scenario.expected_severity == SeverityLevel.LEVEL_1:
            if result.get("status") == "delegated":
                evaluation["criteria_scores"]["severity_handling"] = 20
                evaluation["feedback"].append("✓ Correctly identified as Level 1 - Standard Delegation")
            else:
                evaluation["criteria_scores"]["severity_handling"] = 0
                evaluation["feedback"].append("✗ Failed to handle as Level 1 standard delegation")
        
        elif scenario.expected_severity == SeverityLevel.LEVEL_2:
            if result.get("status") == "coordinating":
                evaluation["criteria_scores"]["severity_handling"] = 20
                evaluation["feedback"].append("✓ Correctly identified as Level 2 - Multi-Agent Coordination")
            else:
                evaluation["criteria_scores"]["severity_handling"] = 0
                evaluation["feedback"].append("✗ Failed to handle as Level 2 coordination")
        
        elif scenario.expected_severity == SeverityLevel.LEVEL_3:
            if result.get("status") == "full_network_activated":
                evaluation["criteria_scores"]["severity_handling"] = 20
                evaluation["feedback"].append("✓ Correctly identified as Level 3 - Full Network Response")
            else:
                evaluation["criteria_scores"]["severity_handling"] = 0
                evaluation["feedback"].append("✗ Failed to handle as Level 3 full network response")
        
        elif scenario.expected_severity == SeverityLevel.LEVEL_4:
            if result.get("status") == "escalated":
                evaluation["criteria_scores"]["severity_handling"] = 20
                evaluation["feedback"].append("✓ Correctly escalated to human specialist")
            else:
                evaluation["criteria_scores"]["severity_handling"] = 0
                evaluation["feedback"].append("✗ Failed to escalate to human specialist")
        
        # Check agent assignment (20 points)
        assigned_agents = result.get("assigned_agents", [])
        if scenario.expected_agents:
            correct_agents = set(scenario.expected_agents).intersection(set(assigned_agents))
            agent_score = (len(correct_agents) / len(scenario.expected_agents)) * 20
            evaluation["criteria_scores"]["agent_assignment"] = agent_score
            
            if agent_score >= 15:
                evaluation["feedback"].append(f"✓ Good agent assignment: {', '.join(assigned_agents)}")
            else:
                evaluation["feedback"].append(f"✗ Suboptimal agent assignment: expected {scenario.expected_agents}, got {assigned_agents}")
        else:
            # For escalation scenarios, no agents should be assigned
            if not assigned_agents:
                evaluation["criteria_scores"]["agent_assignment"] = 20
                evaluation["feedback"].append("✓ Correctly no agents assigned for escalation")
            else:
                evaluation["criteria_scores"]["agent_assignment"] = 0
                evaluation["feedback"].append("✗ Agents assigned when escalation was expected")
        
        # Check response quality (20 points)
        message = result.get("message", "")
        if message and len(message) > 50:
            evaluation["criteria_scores"]["response_quality"] = 20
            evaluation["feedback"].append("✓ Comprehensive response message provided")
        else:
            evaluation["criteria_scores"]["response_quality"] = 10
            evaluation["feedback"].append("⚠ Response message could be more comprehensive")
        
        # Check processing time (20 points)
        if processing_time < 2.0:
            evaluation["criteria_scores"]["processing_time"] = 20
            evaluation["feedback"].append(f"✓ Fast processing time: {processing_time:.2f}s")
        elif processing_time < 5.0:
            evaluation["criteria_scores"]["processing_time"] = 15
            evaluation["feedback"].append(f"⚠ Acceptable processing time: {processing_time:.2f}s")
        else:
            evaluation["criteria_scores"]["processing_time"] = 5
            evaluation["feedback"].append(f"✗ Slow processing time: {processing_time:.2f}s")
        
        # Check error handling (20 points)
        if result.get("status") != "error":
            evaluation["criteria_scores"]["error_handling"] = 20
            evaluation["feedback"].append("✓ No errors encountered")
        else:
            evaluation["criteria_scores"]["error_handling"] = 0
            evaluation["feedback"].append("✗ Error occurred during processing")
        
        # Calculate overall score
        evaluation["overall_score"] = sum(evaluation["criteria_scores"].values())
        evaluation["passed"] = evaluation["overall_score"] >= 70
        
        return evaluation
    
    async def run_full_training_suite(self) -> Dict[str, Any]:
        """Run the complete training suite and generate report."""
        logger.info("Starting Grace Fields customer service training suite")
        
        suite_start_time = datetime.now()
        results = []
        
        for scenario in self.training_scenarios:
            result = await self.run_training_scenario(scenario)
            results.append(result)
            
            # Brief pause between scenarios
            await asyncio.sleep(0.1)
        
        suite_end_time = datetime.now()
        total_time = (suite_end_time - suite_start_time).total_seconds()
        
        # Generate summary report
        report = self._generate_training_report(results, total_time)
        
        logger.info(f"Training suite completed in {total_time:.2f}s")
        logger.info(f"Overall success rate: {report['success_rate']:.1f}%")
        
        return report
    
    def _generate_training_report(self, results: List[Dict[str, Any]], total_time: float) -> Dict[str, Any]:
        """Generate comprehensive training report."""
        total_scenarios = len(results)
        passed_scenarios = len([r for r in results if r.get("evaluation", {}).get("passed", False)])
        
        # Calculate average scores by criteria
        criteria_averages = {}
        all_criteria = set()
        for result in results:
            if "evaluation" in result and "criteria_scores" in result["evaluation"]:
                all_criteria.update(result["evaluation"]["criteria_scores"].keys())
        
        for criterion in all_criteria:
            scores = [
                r.get("evaluation", {}).get("criteria_scores", {}).get(criterion, 0)
                for r in results
            ]
            criteria_averages[criterion] = sum(scores) / len(scores) if scores else 0
        
        # Identify areas for improvement
        improvement_areas = []
        for criterion, avg_score in criteria_averages.items():
            if avg_score < 15:  # Less than 75% of max score
                improvement_areas.append(f"{criterion}: {avg_score:.1f}/20")
        
        # Generate recommendations
        recommendations = []
        if criteria_averages.get("severity_handling", 0) < 15:
            recommendations.append("Review severity level classification logic")
        if criteria_averages.get("agent_assignment", 0) < 15:
            recommendations.append("Improve agent selection algorithms")
        if criteria_averages.get("processing_time", 0) < 15:
            recommendations.append("Optimize processing performance")
        
        report = {
            "training_summary": {
                "total_scenarios": total_scenarios,
                "passed_scenarios": passed_scenarios,
                "success_rate": (passed_scenarios / total_scenarios * 100) if total_scenarios > 0 else 0,
                "total_time_seconds": total_time,
                "average_time_per_scenario": total_time / total_scenarios if total_scenarios > 0 else 0
            },
            "criteria_performance": criteria_averages,
            "improvement_areas": improvement_areas,
            "recommendations": recommendations,
            "detailed_results": results,
            "generated_at": datetime.now().isoformat()
        }
        
        return report
    
    async def save_training_report(self, report: Dict[str, Any], filename: Optional[str] = None) -> str:
        """Save training report to file."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"grace_fields_training_report_{timestamp}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            logger.info(f"Training report saved to {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"Error saving training report: {e}")
            return ""


async def main():
    """Main function for running training."""
    # This would typically be called with a real Enhanced Grace Fields instance
    logger.info("Grace Fields Customer Service Training Module")
    logger.info("This module provides comprehensive training scenarios for customer service capabilities")


if __name__ == "__main__":
    asyncio.run(main())
