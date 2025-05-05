import os
from contextlib import AsyncExitStack
from logging import getLogger

from google.adk.tools.mcp_tool.mcp_toolset import (
    MCPToolset,
    StdioServerParameters,
)

logger = getLogger(__name__)


async def get_time_tools(exit_stack: AsyncExitStack):
    """Gets tools from the File System MCP Server."""
    logger.info("Attempting to connect to MCP Filesystem server...")
    tools, exit_stack = await MCPToolset.from_server(
        connection_params=StdioServerParameters(
            command="uvx",
            args=[
                "mcp-server-time",
                "--local-timezone=Asia/Tokyo",
            ],
        ),
        async_exit_stack=exit_stack,
    )
    logger.info("MCP Toolset created successfully: ", [t.name for t in tools])
    return tools, exit_stack


async def get_notion_tools(exit_stack: AsyncExitStack):
    """Gets tools from the MCP servers."""
    logger.info("Attempting to connect to MCP Notion server...")
    tools, exit_stack = await MCPToolset.from_server(
        connection_params=StdioServerParameters(
            command="npx",
            args=[
                "github:yamitzky/mcp-notion-server",
            ],
            env={
                "NOTION_API_TOKEN": os.environ["NOTION_API_TOKEN"],
                "NOTION_MARKDOWN_CONVERSION": "true",
            },
        ),
        async_exit_stack=exit_stack,
    )
    logger.info("MCP Toolset created successfully: ", [t.name for t in tools])
    return tools, exit_stack


async def get_slack_tools(exit_stack: AsyncExitStack):
    """Gets tools from the File System MCP Server."""
    logger.info("Attempting to connect to MCP Slack server...")
    tools, exit_stack = await MCPToolset.from_server(
        connection_params=StdioServerParameters(
            command="npx",
            args=[
                "@modelcontextprotocol/server-slack",
            ],
            env={
                "SLACK_BOT_TOKEN": os.environ["SLACK_BOT_TOKEN"],
                "SLACK_TEAM_ID": os.environ["SLACK_TEAM_ID"],
            },
        ),
        async_exit_stack=exit_stack,
    )
    logger.info("MCP Toolset created successfully: ", [t.name for t in tools])
    return tools, exit_stack
