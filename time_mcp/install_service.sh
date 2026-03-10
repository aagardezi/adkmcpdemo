#!/bin/bash
set -e

# Define the service file content
SERVICE_FILE="/tmp/mcp-time.service"

cat << EOF > $SERVICE_FILE
[Unit]
Description=Time MCP SSE Server
After=network.target

[Service]
User=$USER
WorkingDirectory=/home/$USER/time_mcp
ExecStart=/home/$USER/.local/bin/uv run mcp-server-time --transport sse --host 0.0.0.0 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# Move to systemd and enable
sudo mv $SERVICE_FILE /etc/systemd/system/mcp-time.service
sudo systemctl daemon-reload
sudo systemctl enable mcp-time.service
sudo systemctl restart mcp-time.service

echo "MCP Time Server systemd service installed and started!"
sudo systemctl status mcp-time.service --no-pager
