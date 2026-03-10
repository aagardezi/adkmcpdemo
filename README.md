# Agent Engine MCP Private Service Connect Deployment Guide

This project demonstrates how to securely deploy a Google Agent Development Kit (ADK) Agent to **Vertex AI Agent Engine**, empowering it to connect to a private Model Context Protocol (MCP) server hosted on a Google Compute Engine (GCE) VM within an isolated Virtual Private Cloud (VPC) network. 

To bridge the private isolated server space with the Google-managed Agent Engine service, we use **Private Service Connect Interfaces (PSC-I)**.

## Architecture Highlights
* **Time MCP Server**: A custom Python application using the MCP standard to expose timezone data. It is run as a persistent `systemd`-managed ASGI service via `uvicorn` on port 8000 using Server-Sent Events (SSE).
* **Vertex AI Agent Engine**: The serverless orchestrator hosting the ADK Reasoning Engine (`testagent`).
* **Private Service Connect (PSC)**: A robust Network Attachment that allows Vertex AI to route requests directly into `10.0.0.0/24` (the VPC subnet) without traversing the public internet.

---

## Deployment Steps

### Step 1: Provision the Base GCP Infrastructure
A bash script (`deploy_gcp.sh`) is provided in the `time_mcp` folder to automate the deployment of the isolated networking and the GCE instance.

1. Ensure the correct project is targeted:
   ```bash
   gcloud config set project YOUR_PROJECT_ID
   export GOOGLE_CLOUD_PROJECT="YOUR_PROJECT_ID"
   export GOOGLE_CLOUD_LOCATION="global"
   ```
2. Run the deployment script to create the Custom VPC, Subnetworks, Cloud Router, Cloud NAT, and the VM itself (`time-mcp-vm`):
   ```bash
   cd time_mcp
   ./deploy_gcp.sh
   ```

### Step 2: Configure Private Service Connect (PSC-I)
To grant Agent Engine access into the newly created VPC, you must establish a bridge:

1. **Create the Network Attachment**
   This attachment links the Agent Engine deployment natively to your private `time-mcp-subnet`.
   ```bash
   gcloud compute network-attachments create agent-engine-attachment \
       --region=us-central1 \
       --connection-preference=ACCEPT_AUTOMATIC \
       --subnets=time-mcp-subnet
   ```
2. **Setup Ingress Firewall**
   Agent Engine dynamically reserves IP addresses from the attached subnet (e.g., `10.0.0.3`, `10.0.0.4`). Ensure traffic is allowed from this subnet block (`10.0.0.0/24`) to reach your VM on port 8000.
   ```bash
   gcloud compute firewall-rules create allow-agent-engine-psc \
       --network=time-mcp-vpc \
       --allow=tcp:8000 \
       --source-ranges=10.0.0.0/24 \
       --description="Allow Agent Engine PSC traffic to reach MCP server"
   ```
3. **Grant Vertex IAM Permissions**
   The Google-managed Vertex AI Service Agent needs authorization to utilize the Network Attachment you just created:
   ```bash
   # Retrieve your Numeric Project ID:
   PROJECT_NUM=$(gcloud projects describe $(gcloud config get-value project) --format="value(projectNumber)")
   
   # Grant it the required network privileges:
   gcloud projects add-iam-policy-binding $(gcloud config get-value project) \
       --member="serviceAccount:service-${PROJECT_NUM}@gcp-sa-aiplatform.iam.gserviceaccount.com" \
       --role="roles/compute.admin"
   ```

### Step 3: Run the Remote MCP Server via SSE
The MCP Python SDK uses standard ASGI frameworks (like Starlette). We will package the server application, transfer it to the VM via Identity-Aware Proxy (IAP), and install it as a Linux service.

1. **Copy the code to the VM securely:**
   ```bash
   gcloud compute scp --tunnel-through-iap --zone us-central1-a --recurse ./ time-mcp-vm:~/time_mcp
   ```

2. **SSH into the VM:**
   ```bash
   gcloud compute ssh --tunnel-through-iap --zone us-central1-a time-mcp-vm
   ```

3. **Install the dependencies and Service Configuration (On the VM):**
   ```bash
   source $HOME/.local/bin/env
   cd ~/time_mcp
   uv sync
   
   # Run the server daemon 
   sudo cat << 'EOF' > /etc/systemd/system/mcp-time.service
   [Unit]
   Description=Time MCP SSE Server
   After=network.target
   
   [Service]
   User=aagardezi_sgardezi_altostrat_com
   WorkingDirectory=/home/aagardezi_sgardezi_altostrat_com/time_mcp
   ExecStart=/home/aagardezi_sgardezi_altostrat_com/time_mcp/.venv/bin/python3 -m uvicorn mcp_server_time.__init__:serve_sse --host 0.0.0.0 --port 8000
   Restart=always
   RestartSec=3
   
   [Install]
   WantedBy=multi-user.target
   EOF
   
   sudo systemctl daemon-reload
   sudo systemctl enable mcp-time.service
   sudo systemctl start mcp-time.service
   ```

### Step 4: Connect the ADK testagent and Deploy
Using the `google-adk` Python library, the reasoning engine logic must be configured to point at the private PSC network bridge. 

1. **The Component Configuration (`testagent/.agent_engine_config.json`)**
   Create/Edit this file directly in the `testagent` folder so the ADK build engine injects the backend networking at execution time:
   ```json
   {
     "reasoning_engine_kwargs": {
       "psc_interface_config": {
         "network_attachment": "projects/YOUR_PROJECT_ID/regions/us-central1/networkAttachments/agent-engine-attachment"
       }
     }
   }
   ```
2. **The Code Modifications (`testagent/agent.py`)**
   Add the internal VM IP (`10.0.0.2`) directly into the `SseConnectionParams` block of your Toolset:
   ```python
   # The Agent is executing directly inside the VPC!
   mcp_toolset = McpToolset(
       connection_params=SseConnectionParams(
           url="http://10.0.0.2:8000/sse"
       )
   )
   ```
3. **Deploy the updated Agent**
   Use standard Python ADK framework bindings to compile and deploy the Reasoning Engine.
   ```bash
   source .venv/bin/activate
   adk deploy agent_engine \
       --project=$(gcloud config get-value project) \
       --region=us-central1 \
       --display_name=timeagent \
       ./testagent
   ```

### Step 5: Verify the Deployment
With the components bridged together:
1. Navigate to your Google Cloud Console.
2. Search for **Vertex AI Agent Builder > Reasoning Engines**.
3. Select the `timeagent` application.
4. Execute your test prompts. For this MCP server, use: **"What time is it in Tokyo right now?"**

The Agent Engine natively communicates over PSC to retrieve the schema from the MCP Server and formulate an execution plan completely detached from the public internet.

---

## Crucial Troubleshooting & Fixes Made

If you choose to write custom ASGI Python servers utilizing the `mcp.server.sse` modules alongside `SseConnectionParams`, observe the two following strict caveats resolved in this deployment:

* **Sse URL Parity:**
  The `SseConnectionParams` configuration demands exactly `http://HOST:PORT/sse`. Attempting to register the bare HOST domain will force the initial `mcp.client.sse` loop to crash with an `HTTP 404 Data Error` as the transport fails to negotiate the Event Source headers.
* **ASGI `Mount` vs `Route` Syntax in Starlette:**
  When passing `SseServerTransport.handle_post_message` inside Starlette, you **must use `Mount("/messages")`**, not `Route("/messages", methods=["POST"])`. ASGI stream apps finish their processes natively, bypassing typical Starlette REST requirements. Misconfiguring it as a `Route` forces a violent server-side closure socket execution loop (`RemoteProtocolError: Server disconnected without sending a response`). 
