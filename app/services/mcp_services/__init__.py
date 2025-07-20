"""
MCP (Model Context Protocol) services for external integrations.
"""

from .atlassian_mcp import AtlassianMCPClient, fetch_confluence_context, fetch_jira_context
from .langchain_mcp_agent import AtlassianMCPAgent, fetch_intelligent_context, get_mcp_agent

__all__ = [
    "AtlassianMCPClient",
    "fetch_confluence_context", 
    "fetch_jira_context",
    "AtlassianMCPAgent",
    "fetch_intelligent_context",
    "get_mcp_agent"
]
