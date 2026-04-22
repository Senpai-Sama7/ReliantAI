#!/bin/bash

# Customize template for company

DEPLOYMENT_ID=$1
COMPANY_ID=$2

if [ -z "$DEPLOYMENT_ID" ] || [ -z "$COMPANY_ID" ]; then
    echo "Usage: ./customize.sh <deployment-id> <company-id>"
    exit 1
fi

echo "🎨 Customizing template for company $COMPANY_ID..."

# Fetch company data
COMPANY_DATA=$(curl -s http://localhost:5000/api/companies/$COMPANY_ID)
COMPANY_NAME=$(echo $COMPANY_DATA | jq -r '.data.name')
BRAND_COLOR=$(echo $COMPANY_DATA | jq -r '.data.brand_color_primary')
LOGO_URL=$(echo $COMPANY_DATA | jq -r '.data.logo_url')

echo "Company: $COMPANY_NAME"
echo "Brand Color: $BRAND_COLOR"
echo "Logo: $LOGO_URL"

# Create customization payload
CUSTOMIZATION_PAYLOAD="{
  \"customizations\": {
    \"primary_color\": \"$BRAND_COLOR\",
    \"company_name\": \"$COMPANY_NAME\",
    \"logo_url\": \"$LOGO_URL\",
    \"service_areas\": $(echo $COMPANY_DATA | jq '.data.service_areas'),
    \"business_type\": \"$(echo $COMPANY_DATA | jq -r '.data.business_type')\"
  },
  \"custom_content\": {
    \"headline\": \"Welcome to $COMPANY_NAME\",
    \"about_text\": \"Leading HVAC solutions in $(echo $COMPANY_DATA | jq -r '.data.service_areas[0].state')\",
    \"phone\": \"$(echo $COMPANY_DATA | jq -r '.data.phone)\"
  }
}"

echo "📤 Applying customizations..."
curl -s -X PATCH http://localhost:5000/api/deployments/$DEPLOYMENT_ID/customize \
  -H "Content-Type: application/json" \
  -d "$CUSTOMIZATION_PAYLOAD"

echo "✅ Customization applied!"
