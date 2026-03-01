#!/bin/bash
echo "Starting Tuya GUI server on port 5001..."
docker exec -d homeassistant python3 /config/tuya_gui.py
echo "Server started in background. Access it at http://<machine-ip>:5001"
