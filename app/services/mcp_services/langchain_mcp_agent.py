"""
LangChain MCP Agent for intelligent Atlassian content retrieval.
Uses ReAct agent pattern with MCP tools for dynamic search and reasoning.
"""
import asyncio
import os
from typing import List, Dict, Optional, Any
from langchain.agents import create_react_agent, AgentExecutor
from langchain.prompts import PromptTemplate
from langchain_core.tools import Tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from app.config.logging import get_logger
from app.config.mcp_config import AtlassianMCPConfig

# Initialize logger
logger = get_logger(__name__)

class AtlassianMCPAgent:
    """
    LangChain-based MCP agent for intelligent Atlassian content retrieval.
    Uses ReAct pattern to intelligently search and combine Confluence/Jira data.
    """
    
    def __init__(self):
        self.llm = None
        self.tools = None
        self.agent = None
        self.server_params = None
        self._setup_server_params()
    
    def _setup_server_params(self):
        """Setup MCP server parameters."""
        self.server_params = StdioServerParameters(
            command="npx",
            args=["-y", "@sooperset/mcp-atlassian"],
            env=self._get_mcp_environment()
        )
        
        # Initialize LLM
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")
        
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            temperature=0.1,
            google_api_key=api_key
        )
        logger.info("Setup MCP agent parameters and LLM")
    
    def _get_mcp_environment(self) -> Dict[str, str]:
        """Get environment variables for MCP server."""
        env = os.environ.copy()
        
        # Add Atlassian configuration
        if AtlassianMCPConfig.is_confluence_configured():
            env.update(AtlassianMCPConfig.get_confluence_config())
        
        if AtlassianMCPConfig.is_jira_configured():
            env.update(AtlassianMCPConfig.get_jira_config())
        
        return env
    
    async def search_for_sop_context(self, user_query: str, space_key: Optional[str] = None, project_key: Optional[str] = None) -> str:
        """
        Use the ReAct agent to intelligently search for SOP-relevant context.
        
        Args:
            user_query: The user's query for SOP generation
            space_key: Optional Confluence space to focus on
            project_key: Optional Jira project to focus on
            
        Returns:
            Comprehensive context string for SOP generation
        """
        try:
            # Enhanced query with context
            enhanced_query = f"""
            Find comprehensive information to help generate an SOP for: "{user_query}"
            
            Please search for:
            1. Existing documentation, procedures, or best practices
            2. Historical issues or incidents related to this topic
            3. Step-by-step processes or workflows
            4. Common problems and their solutions
            5. Prerequisites, requirements, or dependencies
            
            Focus areas:
            - Confluence space: {space_key or 'any relevant space'}
            - Jira project: {project_key or 'any relevant project'}
            """
            
            logger.info(f"Starting intelligent search for SOP context: '{user_query}'")
            
            # Initialize agent session
            async with stdio_client(self.server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    # Initialize the MCP connection
                    await session.initialize()
                    
                    # Get tools from MCP session
                    tools = await load_mcp_tools(session)
                    
                    # Create ReAct agent
                    agent = create_react_agent(
                        model=self.llm,
                        tools=tools
                    )
                    
                    # Execute the agent
                    logger.debug("Executing ReAct agent for intelligent search...")
                    result = await agent.ainvoke({
                        "messages": [{"role": "user", "content": enhanced_query}]
                    })
                    
                    # Extract the final answer from agent response
                    if isinstance(result, dict) and "messages" in result:
                        final_message = result["messages"][-1]
                        context = final_message.content if hasattr(final_message, 'content') else str(final_message)
                    else:
                        context = str(result)
                    
                    logger.info(f"Successfully retrieved intelligent context ({len(context)} characters)")
                    return context
                    
        except Exception as e:
            logger.error(f"Failed to search for SOP context: {e}")
            return f"Error retrieving intelligent context: {str(e)}"
    
    async def search_confluence_intelligently(self, query: str, space_key: Optional[str] = None) -> str:
        """Use agent to intelligently search Confluence with follow-up queries."""
        try:
            confluence_query = f"""
            Search Confluence for information about: "{query}"
            {f"Focus specifically on space: {space_key}" if space_key else ""}
            
            Look for:
            - Documentation and procedures
            - Best practices and guidelines
            - Process flows and workflows
            - Troubleshooting information
            
            Provide a structured summary of the most relevant content found.
            """
            
            return await self.search_for_sop_context(confluence_query, space_key, None)
            
        except Exception as e:
            logger.error(f"Failed to search Confluence intelligently: {e}")
            return f"Error searching Confluence: {str(e)}"
    
    async def search_jira_intelligently(self, query: str, project_key: Optional[str] = None) -> str:
        """Use agent to intelligently search Jira for related issues and incidents."""
        try:
            jira_query = f"""
            Search Jira for issues related to: "{query}"
            {f"Focus specifically on project: {project_key}" if project_key else ""}
            
            Look for:
            - Past incidents and their resolutions
            - Feature requests and implementations
            - Bug reports and fixes
            - Process improvements and changes
            
            Provide a structured summary of relevant issues and their lessons learned.
            """
            
            return await self.search_for_sop_context(jira_query, None, project_key)
            
        except Exception as e:
            logger.error(f"Failed to search Jira intelligently: {e}")
            return f"Error searching Jira: {str(e)}"


# Singleton instance
_agent_instance: Optional[AtlassianMCPAgent] = None

def get_mcp_agent() -> AtlassianMCPAgent:
    """Get singleton instance of the MCP agent."""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = AtlassianMCPAgent()
    return _agent_instance


async def fetch_intelligent_context(user_query: str, space_key: Optional[str] = None, project_key: Optional[str] = None) -> str:
    """
    Fetch intelligent context using ReAct agent for SOP generation.
    This replaces the simple direct MCP calls with intelligent reasoning.
    
    Args:
        user_query: The user's query for SOP generation
        space_key: Optional Confluence space to focus on
        project_key: Optional Jira project to focus on
        
    Returns:
        Comprehensive context string for SOP generation
    """
    try:
        agent = get_mcp_agent()
        context = await agent.search_for_sop_context(
            user_query=user_query,
            space_key=space_key,
            project_key=project_key
        )
        
        return f"""
=== INTELLIGENT ATLASSIAN CONTEXT ===
Generated using ReAct agent with MCP tools

Query: {user_query}
{f"Confluence Space: {space_key}" if space_key else ""}
{f"Jira Project: {project_key}" if project_key else ""}

{context}

=== END CONTEXT ===
"""
        
    except Exception as e:
        logger.error(f"Failed to fetch intelligent context: {e}")
        return f"Error retrieving intelligent context: {str(e)}"
