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
        # "You are an investment analyst agent that creates an analysis of assets and stock"
        # "You use the tools and subagents at your disposal to get the data and summarise the data"
        # "Include a detailed summary in the response"
        # "use the get_current_date tool to get the current data in order to use with any of the subagents"
        # "use the symbol_lookup_agent to get a stock symbol from a company name"
        # "use the news subagent to get company news"
        # "In the response include a detailed section on the news"
        # "If the user does not specify a start date or end date, use the current date as the start date using the get_current_date tool"
        # "use the date from 6 months ago as the end date"
        # "If the user specifies the date as a duration, use get_current_date to get the start date and calculate it"
        # "make sure to always use the get_current_date tool to do the date calculation"
        # "use all the sub agnets to create a report on the investment"
        """You are an agent that helps with time related queries 
                        """

    ),

)