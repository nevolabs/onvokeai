"""
MCP Atlassian integration for fetching Confluence content dynamically.
"""
import asyncio
import json
from typing import List, Dict, Optional
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from app.config.logging import get_logger

# Initialize logger for this module
logger = get_logger(__name__)

class AtlassianMCPClient:
    """Client for interacting with MCP Atlassian server."""
    
    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.server_params = StdioServerParameters(
            command="npx",
            args=["-y", "@sooperset/mcp-atlassian"]
        )
    
    async def __aenter__(self):
        """Async context manager entry."""
        try:
            self.session = await stdio_client(self.server_params).__aenter__()
            logger.info("MCP Atlassian client connected successfully")
            return self
        except Exception as e:
            logger.error(f"Failed to connect to MCP Atlassian server: {e}")
            raise
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.__aexit__(exc_type, exc_val, exc_tb)
            logger.info("MCP Atlassian client disconnected")
    
    async def search_confluence(self, query: str, space_key: Optional[str] = None, limit: int = 5) -> List[Dict]:
        """
        Search Confluence for relevant content based on query.
        
        Args:
            query: Search query for Confluence
            space_key: Optional Confluence space to search in
            limit: Maximum number of results to return
            
        Returns:
            List of relevant Confluence pages/content
        """
        if not self.session:
            raise RuntimeError("MCP client not connected")
        
        try:
            # Use MCP tools to search Confluence
            search_args = {
                "query": query,
                "limit": limit
            }
            
            if space_key:
                search_args["space_key"] = space_key
            
            logger.debug(f"Searching Confluence with query: '{query}', space: {space_key}")
            
            # Call the MCP search tool
            result = await self.session.call_tool("confluence_search", search_args)
            
            if result.content:
                content_data = json.loads(result.content[0].text)
                logger.info(f"Found {len(content_data)} Confluence results for query: '{query}'")
                return content_data
            else:
                logger.warning(f"No Confluence content found for query: '{query}'")
                return []
                
        except Exception as e:
            logger.error(f"Error searching Confluence: {e}")
            return []
    
    async def get_page_content(self, page_id: str) -> Optional[Dict]:
        """
        Get full content of a specific Confluence page.
        
        Args:
            page_id: Confluence page ID
            
        Returns:
            Page content dictionary or None if not found
        """
        if not self.session:
            raise RuntimeError("MCP client not connected")
        
        try:
            logger.debug(f"Fetching Confluence page content for ID: {page_id}")
            
            result = await self.session.call_tool("confluence_get_page", {"page_id": page_id})
            
            if result.content:
                content_data = json.loads(result.content[0].text)
                logger.info(f"Retrieved Confluence page: {content_data.get('title', 'Unknown')}")
                return content_data
            else:
                logger.warning(f"No content found for Confluence page ID: {page_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching Confluence page {page_id}: {e}")
            return None
    
    async def search_jira(self, jql: str, limit: int = 5) -> List[Dict]:
        """
        Search Jira issues using JQL.
        
        Args:
            jql: JQL query string
            limit: Maximum number of results to return
            
        Returns:
            List of relevant Jira issues
        """
        if not self.session:
            raise RuntimeError("MCP client not connected")
        
        try:
            logger.debug(f"Searching Jira with JQL: '{jql}'")
            
            result = await self.session.call_tool("jira_search", {
                "jql": jql,
                "limit": limit
            })
            
            if result.content:
                content_data = json.loads(result.content[0].text)
                logger.info(f"Found {len(content_data)} Jira issues for JQL: '{jql}'")
                return content_data
            else:
                logger.warning(f"No Jira issues found for JQL: '{jql}'")
                return []
                
        except Exception as e:
            logger.error(f"Error searching Jira: {e}")
            return []


async def fetch_confluence_context(query: str, space_key: Optional[str] = None) -> str:
    """
    Fetch relevant Confluence content for SOP generation.
    
    Args:
        query: User's query/description for SOP
        space_key: Optional Confluence space to search in
        
    Returns:
        Formatted string containing relevant Confluence content
    """
    try:
        async with AtlassianMCPClient() as mcp_client:
            # Search for relevant Confluence pages
            confluence_results = await mcp_client.search_confluence(
                query=query, 
                space_key=space_key, 
                limit=5
            )
            
            if not confluence_results:
                logger.info("No relevant Confluence content found")
                return "No relevant Confluence documentation found for this query."
            
            # Format the results for SOP generation
            context_parts = []
            context_parts.append("=== RELEVANT CONFLUENCE DOCUMENTATION ===\n")
            
            for idx, page in enumerate(confluence_results[:3], 1):  # Limit to top 3 results
                title = page.get('title', 'Unknown Title')
                content = page.get('content', '')
                url = page.get('url', '')
                
                context_parts.append(f"Document {idx}: {title}")
                if url:
                    context_parts.append(f"URL: {url}")
                context_parts.append(f"Content: {content[:1000]}...")  # Truncate for context
                context_parts.append("-" * 50)
            
            confluence_context = "\n".join(context_parts)
            logger.info(f"Successfully compiled Confluence context from {len(confluence_results)} documents")
            return confluence_context
            
    except Exception as e:
        logger.error(f"Failed to fetch Confluence context: {e}")
        return f"Error fetching Confluence documentation: {str(e)}"


async def fetch_jira_context(query: str, project_key: Optional[str] = None) -> str:
    """
    Fetch relevant Jira issues for SOP generation.
    
    Args:
        query: User's query/description for SOP
        project_key: Optional Jira project key to search in
        
    Returns:
        Formatted string containing relevant Jira issues
    """
    try:
        async with AtlassianMCPClient() as mcp_client:
            # Build JQL query based on user input
            jql_parts = []
            
            if project_key:
                jql_parts.append(f"project = {project_key}")
            
            # Add text search
            jql_parts.append(f'text ~ "{query}"')
            
            # Combine with AND
            jql = " AND ".join(jql_parts)
            
            # Search for relevant Jira issues
            jira_results = await mcp_client.search_jira(jql=jql, limit=5)
            
            if not jira_results:
                logger.info("No relevant Jira issues found")
                return "No relevant Jira issues found for this query."
            
            # Format the results for SOP generation
            context_parts = []
            context_parts.append("=== RELEVANT JIRA ISSUES ===\n")
            
            for idx, issue in enumerate(jira_results[:3], 1):  # Limit to top 3 results
                key = issue.get('key', 'Unknown Key')
                summary = issue.get('summary', 'No Summary')
                description = issue.get('description', '')
                status = issue.get('status', 'Unknown Status')
                
                context_parts.append(f"Issue {idx}: {key} - {summary}")
                context_parts.append(f"Status: {status}")
                context_parts.append(f"Description: {description[:500]}...")  # Truncate for context
                context_parts.append("-" * 50)
            
            jira_context = "\n".join(context_parts)
            logger.info(f"Successfully compiled Jira context from {len(jira_results)} issues")
            return jira_context
            
    except Exception as e:
        logger.error(f"Failed to fetch Jira context: {e}")
        return f"Error fetching Jira issues: {str(e)}"
