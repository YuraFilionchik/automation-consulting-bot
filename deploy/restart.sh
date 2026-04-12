#!/bin/bash
# Restart bot service - used by /update_app command
# This script is called from Python subprocess

echo "Restarting automation-bot service..."

# Check if running under systemd
if systemctl is-active --quiet automation-bot.service 2>/dev/null; then
    systemctl restart automation-bot.service
    sleep 2
    
    if systemctl is-active --quiet automation-bot.service; then
        echo "SUCCESS: Service restarted via systemd"
    else
        echo "ERROR: Service failed to restart"
        journalctl -u automation-bot.service -n 10 --no-pager
        exit 1
    fi
elif systemctl is-active --quiet bot.service 2>/dev/null; then
    systemctl restart bot.service
    sleep 2
    
    if systemctl is-active --quiet bot.service; then
        echo "SUCCESS: Service restarted via systemd (bot.service)"
    else
        echo "ERROR: bot.service failed to restart"
        journalctl -u bot.service -n 10 --no-pager
        exit 1
    fi
else
    echo "WARNING: No systemd service found. Bot is not managed by systemd."
    echo "If running manually, please restart it yourself."
    exit 0
fi
