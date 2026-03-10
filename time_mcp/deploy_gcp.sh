#!/bin/bash
set -e

# Default values
PROJECT_ID=$(gcloud config get-value project)
REGION="us-central1"
ZONE="us-central1-a"
VPC_NAME="time-mcp-vpc"
SUBNET_NAME="time-mcp-subnet"
ROUTER_NAME="time-mcp-router"
NAT_NAME="time-mcp-nat"
VM_NAME="time-mcp-vm"
FIREWALL_NAME="allow-ssh-iap"

echo "Deploying to project: $PROJECT_ID"

# 1. Create a custom VPC network
echo "Creating VPC network..."
gcloud compute networks create $VPC_NAME --subnet-mode=custom || true

# 2. Create a subnet
echo "Creating subnet..."
gcloud compute networks subnets create $SUBNET_NAME \
    --network=$VPC_NAME \
    --region=$REGION \
    --range=10.0.0.0/24 || true

# 3. Create a firewall rule to allow SSH via Identity-Aware Proxy (IAP)
# IAP range is 35.235.240.0/20. We use this so we don't need a public IP.
echo "Creating firewall rule for IAP SSH..."
gcloud compute firewall-rules create $FIREWALL_NAME \
    --network=$VPC_NAME \
    --allow=tcp:22 \
    --source-ranges=35.235.240.0/20 \
    --description="Allow SSH from IAP" || true

# 4. Create a Cloud Router (required for Cloud NAT)
echo "Creating Cloud Router..."
gcloud compute routers create $ROUTER_NAME \
    --network=$VPC_NAME \
    --region=$REGION || true

# 5. Create a Cloud NAT for outbound internet access
echo "Creating Cloud NAT..."
gcloud compute routers nats create $NAT_NAME \
    --router=$ROUTER_NAME \
    --region=$REGION \
    --auto-allocate-nat-external-ips \
    --nat-all-subnet-ip-ranges || true

# 6. Create the GCE VM instances
# We create it with `--no-address` to ensure it only has a private IP
# The startup script installs dependencies needed for the python MCP server
echo "Creating GCE VM..."
gcloud compute instances create $VM_NAME \
    --zone=$ZONE \
    --machine-type=e2-micro \
    --network=$VPC_NAME \
    --subnet=$SUBNET_NAME \
    --no-address \
    --shielded-secure-boot \
    --shielded-vtpm \
    --shielded-integrity-monitoring \
    --metadata startup-script="#!/bin/bash
apt-get update
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
" || true

echo "------------------------------------------------------"
echo "✅ Infrastructure provisioned successfully."
echo "Here is how you can deploy the code and run the server:"
echo ""
echo "1) Copy the local 'time_mcp' folder to the VM using IAP:"
echo "   gcloud compute scp --tunnel-through-iap --zone $ZONE --recurse ./ time-mcp-vm:~/time_mcp"
echo ""
echo "2) SSH into the VM:"
echo "   gcloud compute ssh --tunnel-through-iap --zone $ZONE time-mcp-vm"
echo ""
echo "3) Inside the VM, run the server:"
echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"
echo "   source \$HOME/.local/bin/env"
echo "   cd ~/time_mcp"
echo "   ~/.local/bin/uvx --from \".[sse]\" mcp-server-time --transport sse --host 0.0.0.0 --port 8000"
echo "------------------------------------------------------"
