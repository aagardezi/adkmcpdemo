#!/bin/bash
set -e

PROJECT_ID=$(gcloud config get-value project)
REGION="us-central1"
VPC_NAME="time-mcp-vpc"
SUBNET_NAME="time-mcp-subnet"
FIREWALL_NAME="allow-agent-engine-psc"
ATTACHMENT_NAME="agent-engine-attachment"

echo "Deploying Agent Engine infrastructure to project: $PROJECT_ID"

# 1. Create firewall rule to allow PSC ingress to our VM on port 8000
# The source block 10.0.0.0/24 covers our subnet, where the PSC-I traffic will originate
echo "Creating firewall rule for PSC..."
gcloud compute firewall-rules create $FIREWALL_NAME \
    --network=$VPC_NAME \
    --allow=tcp:8000 \
    --source-ranges=10.0.0.0/24 \
    --description="Allow Agent Engine PSC traffic to reach MCP server" || true

# 2. Create the Network Attachment for Agent Engine Private Service Connect
echo "Creating Network Attachment..."
gcloud compute network-attachments create $ATTACHMENT_NAME \
    --region=$REGION \
    --connection-preference=ACCEPT_AUTOMATIC \
    --subnets=$SUBNET_NAME || true

echo "------------------------------------------------------"
echo "✅ PSC Infrastructure provisioned."
echo ""
echo "Note: Google Agent Engine is currently in Private Preview and is accessed"
echo "via the \`gcloud alpha ai agents create\` command or the python SDK."
echo ""
echo "To deploy the agent, you must run the deployment command that specifies"
echo "the network attachment. For example:"
echo "gcloud alpha ai agents create TimeAgent \\"
echo "    --project=$PROJECT_ID \\"
echo "    --region=$REGION \\"
echo "    --network-attachment=projects/$PROJECT_ID/regions/$REGION/networkAttachments/$ATTACHMENT_NAME"
echo ""
echo "If your preview SDK uses Python, you pass the network attachment URI"
echo "to the Agent deployment method."
echo "------------------------------------------------------"
