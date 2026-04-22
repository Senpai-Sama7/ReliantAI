#!/bin/bash

# Monitor deployments and send alerts

MONITORING_INTERVAL=300  # 5 minutes
ALERT_EMAIL=$1

if [ -z "$ALERT_EMAIL" ]; then
    echo "Usage: ./monitor.sh <alert-email>"
    exit 1
fi

echo "🔍 Starting deployment monitoring..."

while true; do
    DEPLOYMENTS=$(curl -s http://localhost:5000/api/deployments?status=live)

    echo $DEPLOYMENTS | jq -r '.data[] | .id' | while read DEPLOYMENT_ID; do
        # Check performance
        ANALYTICS=$(curl -s http://localhost:5000/api/deployments/$DEPLOYMENT_ID/analytics)

        # Check SSL certificate
        DOMAIN=$(echo $DEPLOYMENTS | jq -r ".data[] | select(.id == \"$DEPLOYMENT_ID\") | .domain")
        SSL_EXPIRY=$(echo | openssl s_client -servername $DOMAIN -connect $DOMAIN:443 2>/dev/null | openssl x509 -noout -dates 2>/dev/null | grep notAfter)

        # Alert if issues found
        if [[ $ANALYTICS == *"error"* ]]; then
            echo "⚠️  Alert: Analytics error for $DEPLOYMENT_ID"
            # Send email alert
        fi
    done

    sleep $MONITORING_INTERVAL
done
