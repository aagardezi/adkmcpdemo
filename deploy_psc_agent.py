from typing import Optional
import vertexai
from vertexai.preview import reasoning_engines
import os

PROJECT_ID = "genaillentsearch"
LOCATION = "us-central1"
ATTACHMENT = f"projects/{PROJECT_ID}/regions/{LOCATION}/networkAttachments/agent-engine-attachment"

vertexai.init(project=PROJECT_ID, location=LOCATION)

# Since we already have the ADK app in the folder, we can load it
from testagent.agent import root_agent

print(f"Deploying Agent Engine with Network Attachment: {ATTACHMENT}")

remote_agent = reasoning_engines.ReasoningEngine.create(
    root_agent,
    requirements=[
        "google-adk",
        "mcp",
        "google-auth",
        "google-genai",
        "google-cloud-aiplatform",
        "requests",
        "beautifulsoup4",
        "google-cloud-secret-manager"
    ],
    display_name="TimeAgent (PSC Connected)",
    description="Agent connected securely to time-mcp-vm via PSC",
    sys_version="3.10",
    sys_network_attachment=ATTACHMENT
)

print("Deployment complete!")
print(f"Agent Engine ID: {remote_agent.resource_name}")
