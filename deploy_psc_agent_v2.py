from typing import Optional
import vertexai
from google.cloud import aiplatform
from google.cloud.aiplatform_v1beta1 import ReasoningEngineServiceClient
from google.cloud.aiplatform_v1beta1.types import ReasoningEngine
from google.cloud.aiplatform_v1beta1.types import ReasoningEngineSpec
from google.cloud.aiplatform_v1beta1.types import CreateReasoningEngineRequest
import os

PROJECT_ID = "genaillentsearch"
LOCATION = "us-central1"

# Initialize vertex ai to package the reasoning engine locally first
vertexai.init(project=PROJECT_ID, location=LOCATION)
from vertexai.preview import reasoning_engines
from testagent.agent import root_agent

print("Staging the Reasoning Engine package to Cloud Storage...")
# Use the high level SDK just to package and upload the blob
remote_app = reasoning_engines._reasoning_engines.ReasoningEngine._create_and_upload_package(
    reasoning_engine=root_agent,
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
    project=PROJECT_ID,
    location=LOCATION,
    gcs_dir_name="reasoning_engine",
    sys_version="3.10",
    extra_packages=None
)
package_uri = remote_app

print(f"Uploaded package to {package_uri}. Creating Reasoning Engine API Resource...")

# Now use the raw GAPIC client to create the resource WITH the network attachment!
client = ReasoningEngineServiceClient(client_options={"api_endpoint": f"{LOCATION}-aiplatform.googleapis.com"})

engine_to_create = ReasoningEngine(
    display_name="TimeAgent (PSC Connected)",
    description="Agent connected securely to time-mcp-vm via PSC",
    spec=ReasoningEngineSpec(
        package_spec=ReasoningEngineSpec.PackageSpec(
            python_version="3.10",
            dependency_files_gcs_uri=package_uri,
            requirements_gcs_uri=package_uri,
        )
    )
)
# Wait, let's use the standard Python structure for PSC Interface
# Actually, vertex SDK preview ReasoningEngine.create doesn't support PSC, but aiplatform endpoints do.
# Let's check if reasoning engines natively support PSC network... no, ReasoningEngines are serverless. 

print("Ready.")
