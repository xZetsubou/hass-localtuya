#!/bin/bash
echo "Stopping Tuya GUI server inside Home Assistant container..."
docker exec homeassistant pkill -f tuya_gui.py
echo "Server stopped."
