from higherself_schema import Agent  # This is higherself_schema.Agent
from higherself_schema import \
    AgentCapability  # This should be available via higherself_schema
from higherself_schema import \
    AgentPersonality  # This should be available via higherself_schema
from higherself_schema import \
    AgentRole  # This should be available via higherself_schema
from higherself_schema import (APIEndpoint, HigherSelfNetworkServer,
                               IntegrationType, NotionDatabaseType,
                               WorkflowState)

# Note: AgentPersonality, AgentRole, AgentCapability are defined in higherself_schema.py,
# attempting to import from models.base within that file.

def main():
    # Load the complete server documentation
    try:
        server_doc = HigherSelfNetworkServer.parse_file("server_documentation.json")
        print("Successfully loaded server_documentation.json")
    except Exception as e:
        print(f"Error loading server_documentation.json: {e}")
        return

    # --- Knowledge Acquisition Phase ---
    print("\n--- Knowledge Acquisition Phase ---")

    # Access specific components
    try:
        grace_fields_agent = next(agent for agent in server_doc.agents 
                                 if agent.personality == AgentPersonality.GRACE_FIELDS)
        print(f"Found Grace Fields agent: {grace_fields_agent.role}")
    except StopIteration:
        print("Grace Fields agent not found in server_documentation.json (this is expected if not added).")
    except Exception as e:
        print(f"Error accessing Grace Fields agent: {e}")

    # Example: Access Nyra agent (added in our JSON)
    try:
        nyra_agent = next(agent for agent in server_doc.agents
                         if agent.personality == AgentPersonality.NYRA)
        print(f"Found Nyra agent: Role - {nyra_agent.role}, Capabilities - {[cap.value for cap in nyra_agent.primary_capabilities]}")
    except StopIteration:
        print("Nyra agent not found.")
    except Exception as e:
        print(f"Error accessing Nyra agent: {e}")

    # Understand agent relationships
    try:
        print("Agents Nyra collaborates with:")
        for agent_personality in nyra_agent.collaborates_with:
            print(f"- {agent_personality.value}")
    except NameError: # If nyra_agent wasn't found
        print("Cannot show Nyra's collaborations as Nyra was not found.")
    except Exception as e:
        print(f"Error understanding Nyra's agent relationships: {e}")

    # --- Capability Integration Phase ---
    print("\n--- Capability Integration Phase ---")

    # Identify relevant integrations (adapted from API endpoints example)
    try:
        notion_integrations = [
            integration for integration in server_doc.integrations 
            if integration.type == IntegrationType.NOTION
        ]
        if notion_integrations:
            print(f"Found {len(notion_integrations)} Notion integration(s):")
            for ni in notion_integrations:
                print(f"- Name: {ni.name}, Description: {ni.description}")
        else:
            print("No Notion integrations found in the document.")
    except Exception as e:
        print(f"Error identifying Notion integrations: {e}")

    # Understand workflow transitions
    try:
        lead_capture_workflow_name = "Standard Lead Processing Workflow" # From our server_documentation.json
        lead_capture_workflow = next(workflow for workflow in server_doc.workflows 
                                    if workflow.name.lower() == lead_capture_workflow_name.lower())
        print(f"Found workflow: {lead_capture_workflow.name}")
        
        # Example: Print transitions from 'initiated' state
        current_state_example = WorkflowState.INITIATED 
        possible_transitions = [
            transition for transition in lead_capture_workflow.transitions
            if transition.from_state == current_state_example
        ]
        if possible_transitions:
            print(f"Possible transitions from state '{current_state_example.value}':")
            for t in possible_transitions:
                print(f"- To '{t.to_state.value}', Trigger: '{t.trigger}', Responsible: {t.responsible_agent.value if t.responsible_agent else 'N/A'}")
        else:
            print(f"No transitions found from state '{current_state_example.value}'.")
            
    except StopIteration:
        print(f"Workflow '{lead_capture_workflow_name}' not found.")
    except Exception as e:
        print(f"Error understanding workflow transitions: {e}")

    # --- Simulation and Testing Phase (Commented out as per plan) ---
    # print("\n--- Simulation and Testing Phase ---")
    # def simulate_workflow_execution(workflow_name, initial_data):
    #     # ... (requires select_transition and execute_actions)
    #     pass
    # print("Simulation examples would require external function definitions (select_transition, execute_actions).")

    # --- Domain-Specific Application Phase ---
    print("\n--- Domain-Specific Application Phase ---")
    try:
        gallery_config = configure_art_gallery_automation(server_doc)
        if gallery_config:
            print("Art Gallery Automation Configuration:")
            if gallery_config["agents"]:
                 print(f"- Relevant Agents: {[agent.role for agent in gallery_config['agents']]}")
            else:
                print("- No relevant agents found for Exhibition Management.")
            if gallery_config["databases"]:
                print(f"- Art Databases: {[db.type.value for db in gallery_config['databases']]}")
            else:
                print("- No relevant art databases found.")
            if gallery_config["workflows"]:
                print(f"- Exhibition Workflows: {[wf.name for wf in gallery_config['workflows']]}")
            else:
                print("- No exhibition workflows found (this is expected if not in JSON).")

    except Exception as e:
        print(f"Error in domain-specific application example: {e}")


def configure_art_gallery_automation(server_doc: HigherSelfNetworkServer) -> dict:
    # This function is adapted from the issue.
    # It might not find data if "Exhibition Management" or specific workflows aren't in server_documentation.json
    
    # The capability "Exhibition Management" is not in our current AgentCapability enum.
    # For demonstration, let's try a capability that IS in the enum, e.g., "CONTENT_CREATION"
    # Or, we'd need to add "Exhibition Management" to AgentCapability if it's a real requirement.
    # For now, this part will likely find no agents.
    
    # Let's assume "Exhibition Management" is a string value for a capability name for now.
    # The schema `AgentCapability` is an Enum, so direct string comparison won't work with `cap.name`.
    # The `primary_capabilities` in `higherself_schema.Agent` is `List[AgentCapability]`.
    # So, `capability` here is an `AgentCapability` enum member. We need to compare its value.
    
    relevant_agents = []
    try:
        relevant_agents = [agent for agent in server_doc.agents
                           if AgentCapability.CONTENT_CREATION in agent.primary_capabilities] # Example
                           # if any(capability.value == "Exhibition Management" # capability.value is how to get string from enum
                           #       for capability in agent.primary_capabilities)]
    except Exception as e:
        print(f"Note: Could not find agents with specific capability due to: {e}")


    art_databases = [db for db in server_doc.notion_databases 
                    if db.type in [NotionDatabaseType.PRODUCTS_SERVICES, 
                                  NotionDatabaseType.BUSINESS_ENTITIES]]
    
    # This workflow name is hypothetical for the example.
    # Our server_documentation.json has "Standard Lead Processing".
    # This part will likely not find the workflow.
    exhibition_workflow = []
    try:
        exhibition_workflow_name = "Art Exhibition Workflow" 
        exhibition_workflow = [workflow for workflow in server_doc.workflows 
                               if exhibition_workflow_name.lower() in workflow.name.lower()]
    except Exception as e:
        print(f"Note: Could not find '{exhibition_workflow_name}' due to: {e}")
        
    return {
        "agents": relevant_agents,
        "databases": art_databases,
        "workflows": exhibition_workflow
    }

if __name__ == "__main__":
    main()
```
