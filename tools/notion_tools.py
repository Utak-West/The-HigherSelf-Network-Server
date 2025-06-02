"""
Notion integration tools for LangChain agents.
"""

from langchain.tools import BaseTool
from typing import Optional, Type, Dict, Any, List
from pydantic import BaseModel, Field
import json
from datetime import datetime

from services.notion_service import NotionService
from loguru import logger

class NotionQueryInput(BaseModel):
    database_id: str = Field(description="Notion database ID")
    query: str = Field(description="Natural language query")
    limit: int = Field(default=5, description="Maximum number of results to return")

class NotionQueryTool(BaseTool):
    name = "notion_query"
    description = "Query Notion databases using natural language. Useful for finding existing records, checking status, or retrieving information."
    args_schema: Type[BaseModel] = NotionQueryInput
    
    def __init__(self, notion_service: NotionService):
        super().__init__()
        self.notion_service = notion_service
    
    def _run(self, database_id: str, query: str, limit: int = 5) -> str:
        """Execute the query against Notion."""
        try:
            # Convert natural language to Notion filter
            filter_dict = self._parse_query_to_filter(query)
            results = self.notion_service.query_database(database_id, filter_dict)
            return self._format_results(results, limit)
        except Exception as e:
            logger.error(f"Error querying Notion: {e}")
            return f"Error querying Notion: {str(e)}"
    
    async def _arun(self, database_id: str, query: str, limit: int = 5) -> str:
        """Async version."""
        return self._run(database_id, query, limit)
    
    def _parse_query_to_filter(self, query: str) -> Dict[str, Any]:
        """Convert natural language query to Notion filter."""
        filter_dict = {}
        query_lower = query.lower()
        
        # Status filters
        if "status" in query_lower:
            if "active" in query_lower or "open" in query_lower:
                filter_dict["Status"] = {"select": {"equals": "Active"}}
            elif "completed" in query_lower or "done" in query_lower:
                filter_dict["Status"] = {"select": {"equals": "Completed"}}
            elif "pending" in query_lower or "waiting" in query_lower:
                filter_dict["Status"] = {"select": {"equals": "Pending"}}
        
        # Priority filters
        if "priority" in query_lower:
            if "high" in query_lower:
                filter_dict["Priority"] = {"select": {"equals": "High"}}
            elif "medium" in query_lower:
                filter_dict["Priority"] = {"select": {"equals": "Medium"}}
            elif "low" in query_lower:
                filter_dict["Priority"] = {"select": {"equals": "Low"}}
        
        # Date filters
        if "today" in query_lower:
            today = datetime.now().date().isoformat()
            filter_dict["Date"] = {"date": {"equals": today}}
        elif "this week" in query_lower:
            # This would need more sophisticated date handling
            pass
        
        # Business type filters
        if "art gallery" in query_lower or "gallery" in query_lower:
            filter_dict["Business Type"] = {"select": {"equals": "Art Gallery"}}
        elif "wellness" in query_lower or "wellness center" in query_lower:
            filter_dict["Business Type"] = {"select": {"equals": "Wellness Center"}}
        elif "consultancy" in query_lower or "consulting" in query_lower:
            filter_dict["Business Type"] = {"select": {"equals": "Consultancy"}}
        
        return filter_dict
    
    def _format_results(self, results: Dict[str, Any], limit: int) -> str:
        """Format Notion results for LLM consumption."""
        if not results.get("results"):
            return "No results found."
        
        formatted = []
        for item in results["results"][:limit]:
            title = "Untitled"
            properties_summary = []
            
            # Extract title
            if item.get("properties", {}).get("Name"):
                title_prop = item["properties"]["Name"]
                if title_prop.get("title") and title_prop["title"]:
                    title = title_prop["title"][0]["text"]["content"]
            
            # Extract key properties
            for prop_name, prop_data in item.get("properties", {}).items():
                if prop_name == "Name":
                    continue
                
                prop_value = self._extract_property_value(prop_data)
                if prop_value:
                    properties_summary.append(f"{prop_name}: {prop_value}")
            
            # Format the item
            item_summary = f"• {title}"
            if properties_summary:
                item_summary += f" ({', '.join(properties_summary[:3])})"  # Limit to 3 properties
            item_summary += f" [ID: {item['id'][:8]}...]"
            
            formatted.append(item_summary)
        
        return "\n".join(formatted)
    
    def _extract_property_value(self, prop_data: Dict[str, Any]) -> str:
        """Extract value from Notion property data."""
        prop_type = prop_data.get("type")
        
        if prop_type == "select" and prop_data.get("select"):
            return prop_data["select"]["name"]
        elif prop_type == "multi_select" and prop_data.get("multi_select"):
            return ", ".join([item["name"] for item in prop_data["multi_select"]])
        elif prop_type == "rich_text" and prop_data.get("rich_text"):
            return prop_data["rich_text"][0]["text"]["content"] if prop_data["rich_text"] else ""
        elif prop_type == "number" and prop_data.get("number") is not None:
            return str(prop_data["number"])
        elif prop_type == "date" and prop_data.get("date"):
            return prop_data["date"]["start"]
        elif prop_type == "email" and prop_data.get("email"):
            return prop_data["email"]
        elif prop_type == "phone_number" and prop_data.get("phone_number"):
            return prop_data["phone_number"]
        
        return ""

class NotionCreatePageInput(BaseModel):
    database_id: str = Field(description="Notion database ID")
    title: str = Field(description="Page title")
    properties: Dict[str, Any] = Field(description="Page properties as JSON")

class NotionCreatePageTool(BaseTool):
    name = "notion_create_page"
    description = "Create a new page in a Notion database. Useful for creating contacts, tasks, workflows, or other records."
    args_schema: Type[BaseModel] = NotionCreatePageInput
    
    def __init__(self, notion_service: NotionService):
        super().__init__()
        self.notion_service = notion_service
    
    def _run(self, database_id: str, title: str, properties: Dict[str, Any]) -> str:
        """Create a new page in Notion."""
        try:
            # Ensure title is in properties
            if "Name" not in properties:
                properties["Name"] = {"title": [{"text": {"content": title}}]}
            
            result = self.notion_service.create_page(database_id, properties)
            return f"Created page: {title} (ID: {result['id'][:8]}...)"
        except Exception as e:
            logger.error(f"Error creating Notion page: {e}")
            return f"Error creating page: {str(e)}"
    
    async def _arun(self, database_id: str, title: str, properties: Dict[str, Any]) -> str:
        """Async version."""
        return self._run(database_id, title, properties)

class NotionUpdatePageInput(BaseModel):
    page_id: str = Field(description="Notion page ID to update")
    properties: Dict[str, Any] = Field(description="Properties to update as JSON")

class NotionUpdatePageTool(BaseTool):
    name = "notion_update_page"
    description = "Update an existing page in Notion. Useful for updating status, adding notes, or modifying existing records."
    args_schema: Type[BaseModel] = NotionUpdatePageInput
    
    def __init__(self, notion_service: NotionService):
        super().__init__()
        self.notion_service = notion_service
    
    def _run(self, page_id: str, properties: Dict[str, Any]) -> str:
        """Update an existing page in Notion."""
        try:
            result = self.notion_service.update_page(page_id, properties)
            return f"Updated page (ID: {page_id[:8]}...)"
        except Exception as e:
            logger.error(f"Error updating Notion page: {e}")
            return f"Error updating page: {str(e)}"
    
    async def _arun(self, page_id: str, properties: Dict[str, Any]) -> str:
        """Async version."""
        return self._run(page_id, properties)

class NotionSearchInput(BaseModel):
    query: str = Field(description="Search query")
    filter_type: str = Field(default="page", description="Type of content to search: page or database")

class NotionSearchTool(BaseTool):
    name = "notion_search"
    description = "Search across all Notion content. Useful for finding pages, databases, or content by text."
    args_schema: Type[BaseModel] = NotionSearchInput
    
    def __init__(self, notion_service: NotionService):
        super().__init__()
        self.notion_service = notion_service
    
    def _run(self, query: str, filter_type: str = "page") -> str:
        """Search Notion content."""
        try:
            # This would use the Notion search API
            # For now, return a placeholder
            return f"Search functionality for '{query}' not yet implemented"
        except Exception as e:
            logger.error(f"Error searching Notion: {e}")
            return f"Error searching: {str(e)}"
    
    async def _arun(self, query: str, filter_type: str = "page") -> str:
        """Async version."""
        return self._run(query, filter_type)
