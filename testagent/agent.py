import datetime
from zoneinfo import ZoneInfo
from google.adk.agents import Agent, ParallelAgent, SequentialAgent, LlmAgent
from google.adk.tools import agent_tool, AgentTool
from google.adk.tools import google_search

from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams, SseConnectionParams
from mcp import StdioServerParameters

from .config import config
import google.auth

from google import genai

from .helpercode import get_project_id

import vertexai

import os

from google.adk.tools.bigquery import BigQueryCredentialsConfig
from google.adk.tools.bigquery import BigQueryToolset
from google.adk.tools.bigquery.config import BigQueryToolConfig
from google.adk.tools.bigquery.config import WriteMode
from google.adk.models import google_llm

os.environ['GOOGLE_CLOUD_LOCATION'] ="global"

from google import genai

api_client = genai.Client(
    vertexai=True,
    project=get_project_id(),
    location="global"
)
model = google_llm.Gemini(model=config.gemini_model)
model.api_client= api_client 







# Use the Private Service Connect internal IP address of the Time MCP server
mcp_toolset = McpToolset(
    connection_params=SseConnectionParams(
        url="http://10.0.0.2:8000/sse"
    )
)

root_agent = LlmAgent(
    name="TimeAgent",
    # model="gemini-2.5-flash",
    # model=config.gemini_model,
    model= model,
    tools=[mcp_toolset],
    description=(
        "You are an agent helping with time related queries"
    ),
    instruction=(
        """You are an agent that helps with time related queries 
                        """
    ),

)