# Deploying Time MCP Server to GCP

This guide explains how to deploy the Model Context Protocol (MCP) time server onto a secure Google Compute Engine (GCE) Virtual Machine within a Virtual Private Cloud (VPC).

The architecture provisions a **private VM** without any external IP address for superior security. Outbound internet access is provided via **Cloud NAT**, and SSH access is enabled securely via **Identity-Aware Proxy (IAP)**.

## Prerequisites

1. Initialize Google Cloud SDK and authenticate:
   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```
2. Make sure the Compute Engine API and IAP APIs are enabled in your project:
   ```bash
   gcloud services enable compute.googleapis.com
   gcloud services enable iap.googleapis.com
   ```

## Infrastructure Setup

A deployment script `deploy_gcp.sh` is provided in this directory. 

Make the deployment script executable and run it:
```bash
cd time_mcp
chmod +x deploy_gcp.sh
./deploy_gcp.sh
```

This script will automatically create:
- A custom VPC (`time-mcp-vpc`) and Subnet (`time-mcp-subnet`)
- A Cloud Router (`time-mcp-router`) and Cloud NAT (`time-mcp-nat`) for outbound internet access.
- A Firewall rule (`allow-ssh-iap`) to explicitly allow SSH traffic only from Google's IAP identity proxy range.
- An `e2-micro` GCE VM instance (`time-mcp-vm`) with a startup script that installs python dependencies and `uv`.

## Deploying Code to the VM

After the infrastructure finishes provisioning, you will use `gcloud compute scp` to copy the source code to the server using the IAP tunnel.

```bash
# Assuming you are in the adkmcpdemo/time_mcp directory
gcloud compute scp --tunnel-through-iap --zone us-central1-a --recurse ./ time-mcp-vm:~/time_mcp
```

## Running the Server

Log into the VM instance securely via SSH (this relies on the IAP tunnel, so no public keys or public IPs are required!):

```bash
gcloud compute ssh --tunnel-through-iap --zone us-central1-a time-mcp-vm
```

Once inside the SSH session, navigate to the code directory and execute the server using `uvx` directly from the source code:

```bash
cd ~/time_mcp

# Install uv for your user account
curl -LsSf https://astral.sh/uv/install.sh | sh
# Start the MCP server as an HTTP SSE server listening on all interfaces (port 8000)
~/.local/bin/uvx --from ".[sse]" mcp-server-time --transport sse --host 0.0.0.0 --port 8000
```

The server will start listening on port 8000. You can now securely connect Vertex AI Agent Engine or other services inside the VPC via Private Service Connect (PSC-I)!

## Connecting an external MCP Client

If you want to use this remote MCP server from a local client (like Claude Desktop or another LLM window), you can configure your MCP client to invoke the command over SSH. 

For instance, your MCP client's connection configuration would look something like this:

```json
{
  "mcpServers": {
    "remote-time": {
      "command": "gcloud",
      "args": [
        "compute",
        "ssh",
        "--tunnel-through-iap",
        "--zone=us-central1-a",
        "time-mcp-vm",
        "--",
        "curl -LsSf https://astral.sh/uv/install.sh | sh && source ~/.local/bin/env && cd ~/time_mcp && ~/.local/bin/uvx --from . mcp-server-time"
      ]
    }
  }
}
```
*Note: Make sure your local credentials are valid when the client attempts to execute `gcloud compute ssh`.*
