"""
Configuration for MCP Atlassian integration.
"""
import os
from typing import Optional

# MCP Atlassian Configuration
class AtlassianMCPConfig:
    """Configuration settings for MCP Atlassian integration."""
    
    # Confluence settings
    CONFLUENCE_BASE_URL: Optional[str] = os.getenv("CONFLUENCE_BASE_URL")
    CONFLUENCE_USERNAME: Optional[str] = os.getenv("CONFLUENCE_USERNAME") 
    CONFLUENCE_API_TOKEN: Optional[str] = os.getenv("CONFLUENCE_API_TOKEN")
    CONFLUENCE_SPACE_KEY: Optional[str] = os.getenv("CONFLUENCE_SPACE_KEY")  # Optional default space
    
    # Jira settings
    JIRA_BASE_URL: Optional[str] = os.getenv("JIRA_BASE_URL")
    JIRA_USERNAME: Optional[str] = os.getenv("JIRA_USERNAME")
    JIRA_API_TOKEN: Optional[str] = os.getenv("JIRA_API_TOKEN") 
    JIRA_PROJECT_KEY: Optional[str] = os.getenv("JIRA_PROJECT_KEY")  # Optional default project
    
    # MCP Server settings
    MCP_SERVER_COMMAND: str = "npx"
    MCP_SERVER_ARGS: list = ["-y", "@sooperset/mcp-atlassian"]
    
    @classmethod
    def is_confluence_configured(cls) -> bool:
        """Check if Confluence is properly configured."""
        return all([
            cls.CONFLUENCE_BASE_URL,
            cls.CONFLUENCE_USERNAME, 
            cls.CONFLUENCE_API_TOKEN
        ])
    
    @classmethod
    def is_jira_configured(cls) -> bool:
        """Check if Jira is properly configured."""
        return all([
            cls.JIRA_BASE_URL,
            cls.JIRA_USERNAME,
            cls.JIRA_API_TOKEN
        ])
    
    @classmethod
    def get_confluence_config(cls) -> dict:
        """Get Confluence configuration for MCP server."""
        return {
            "CONFLUENCE_BASE_URL": cls.CONFLUENCE_BASE_URL,
            "CONFLUENCE_USERNAME": cls.CONFLUENCE_USERNAME,
            "CONFLUENCE_API_TOKEN": cls.CONFLUENCE_API_TOKEN
        }
    
    @classmethod
    def get_jira_config(cls) -> dict:
        """Get Jira configuration for MCP server."""
        return {
            "JIRA_BASE_URL": cls.JIRA_BASE_URL,
            "JIRA_USERNAME": cls.JIRA_USERNAME,
            "JIRA_API_TOKEN": cls.JIRA_API_TOKEN
        }
