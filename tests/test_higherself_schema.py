import os
import sys
from datetime import datetime  # Import datetime
from pathlib import Path

import pytest

# Add the root directory to sys.path to allow importing higherself_schema
# This assumes the test will be run from the root directory or the worker handles paths.
# For local testing from within tests/ directory, this path adjustment is often needed.
# ROOT_DIR = Path(__file__).resolve().parent.parent
# sys.path.append(str(ROOT_DIR))

try:
    # Import the example script to test its execution
    import schema_usage_example
    from higherself_schema import (
        ServerComponent,  # Ensure all relevant sub-models are imported for isinstance checks
    )
    from higherself_schema import (
        Agent,
        AgentCapability,
        AgentPersonality,
        AgentRole,
        APIEndpoint,
        DeploymentConfiguration,
        HigherSelfNetworkServer,
        Integration,
        IntegrationType,
        LearningModule,
        NotionDatabase,
        NotionDatabaseType,
        RAGComponent,
        Workflow,
        WorkflowState,
    )
except ModuleNotFoundError as e:
    # Fallback for environments where sys.path manipulation might not work as expected in the test runner
    # This indicates a potential issue with how tests are discovered/run if higherself_schema isn't found.
    print(f"Initial import failed: {e}. Attempting to adjust sys.path for testing context.")
    # Determine project root based on a known file/directory, assuming tests/ is one level down.
    # This is a common pattern for tests.
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    import schema_usage_example
    from higherself_schema import (
        Agent,
        AgentCapability,
        AgentPersonality,
        AgentRole,
        APIEndpoint,
        DeploymentConfiguration,
        HigherSelfNetworkServer,
        Integration,
        IntegrationType,
        LearningModule,
        NotionDatabase,
        NotionDatabaseType,
        RAGComponent,
        ServerComponent,
        Workflow,
        WorkflowState,
    )


JSON_FILE_PATH = Path(__file__).parent.parent / "server_documentation.json"

@pytest.fixture(scope="module")
def server_doc() -> HigherSelfNetworkServer:
    if not JSON_FILE_PATH.exists():
        pytest.fail(f"{JSON_FILE_PATH} not found. Make sure it's created in the root directory.")
    try:
        doc = HigherSelfNetworkServer.parse_file(JSON_FILE_PATH)
        return doc
    except Exception as e:
        pytest.fail(f"Failed to parse {JSON_FILE_PATH}: {e}")

def test_server_documentation_loading(server_doc: HigherSelfNetworkServer):
    assert server_doc is not None
    assert server_doc.version == "1.0.0"

    # Check that lists are populated (as per our JSON, they should have at least one item)
    assert len(server_doc.components) > 0
    assert isinstance(server_doc.components[0], ServerComponent)

    assert len(server_doc.api_endpoints) > 0
    assert isinstance(server_doc.api_endpoints[0], APIEndpoint)

    assert len(server_doc.integrations) > 0
    assert isinstance(server_doc.integrations[0], Integration)
    assert server_doc.integrations[0].type == IntegrationType.NOTION # Check enum value

    assert len(server_doc.agents) > 0
    assert isinstance(server_doc.agents[0], Agent)
    assert server_doc.agents[0].personality == AgentPersonality.NYRA # Check enum value

    assert len(server_doc.notion_databases) > 0
    assert isinstance(server_doc.notion_databases[0], NotionDatabase)
    assert server_doc.notion_databases[0].type == NotionDatabaseType.CONTACTS_PROFILES

    assert len(server_doc.workflows) > 0
    assert isinstance(server_doc.workflows[0], Workflow)
    # Correcting workflow name to match JSON
    assert server_doc.workflows[0].name == "Standard Lead Processing Workflow"

    assert len(server_doc.rag_components) > 0
    assert isinstance(server_doc.rag_components[0], RAGComponent)

    assert len(server_doc.deployment_options) > 0
    assert isinstance(server_doc.deployment_options[0], DeploymentConfiguration)

    assert len(server_doc.learning_modules) > 0
    assert isinstance(server_doc.learning_modules[0], LearningModule)

    # The field was `last_updated` in higherself_schema.py, ensure it exists and is datetime
    assert hasattr(server_doc, 'last_updated')
    assert isinstance(server_doc.last_updated, datetime)


def test_agent_details(server_doc: HigherSelfNetworkServer):
    nyra_agent = next((agent for agent in server_doc.agents if agent.personality == AgentPersonality.NYRA), None)
    assert nyra_agent is not None
    assert nyra_agent.role == AgentRole.LEAD_CAPTURE
    assert AgentCapability.LEAD_PROCESSING in nyra_agent.primary_capabilities
    assert AgentPersonality.SOLARI in nyra_agent.collaborates_with

def test_workflow_details(server_doc: HigherSelfNetworkServer):
    # Correcting workflow name to match JSON
    lead_workflow = next((wf for wf in server_doc.workflows if wf.name == "Standard Lead Processing Workflow"), None)
    assert lead_workflow is not None
    assert WorkflowState.INITIATED in lead_workflow.states
    assert len(lead_workflow.transitions) > 0
    assert lead_workflow.transitions[0].from_state == WorkflowState.INITIATED
    assert lead_workflow.transitions[0].responsible_agent == AgentPersonality.NYRA

def test_schema_usage_example_script(capsys):
    # Test that the example script runs without raising exceptions
    try:
        schema_usage_example.main()
        captured = capsys.readouterr() # Capture print statements
        assert "Successfully loaded server_documentation.json" in captured.out
        assert "Found Nyra agent:" in captured.out
        # Add more assertions based on expected output of the script if necessary
    except Exception as e:
        pytest.fail(f"schema_usage_example.main() raised an exception: {e}")

```
