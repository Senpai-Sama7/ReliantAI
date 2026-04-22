#!/bin/bash

# HVAC Template Library Deployment Script

set -e

echo "🚀 Starting HVAC Template Deployment..."

# Configuration
TEMPLATE_ID=$1
COMPANY_ID=$2
DOMAIN=$3
ENVIRONMENT=${4:-production}

if [ -z "$TEMPLATE_ID" ] || [ -z "$COMPANY_ID" ] || [ -z "$DOMAIN" ]; then
    echo "Usage: ./deploy.sh <template-id> <company-id> <domain> [environment]"
    exit 1
fi

echo "📋 Deployment Configuration:"
echo "  Template: $TEMPLATE_ID"
echo "  Company: $COMPANY_ID"
echo "  Domain: $DOMAIN"
echo "  Environment: $ENVIRONMENT"

# Step 1: Create deployment record
echo "📝 Creating deployment record..."
DEPLOYMENT_ID=$(curl -s -X POST http://localhost:5000/api/deployments \
  -H "Content-Type: application/json" \
  -d "{
    \"template_id\": \"$TEMPLATE_ID\",
    \"company_id\": \"$COMPANY_ID\",
    \"domain\": \"$DOMAIN\"
  }" | jq -r '.data.id')

echo "✅ Deployment ID: $DEPLOYMENT_ID"

# Step 2: Clone template repositories
echo "🔄 Cloning template repositories..."
TEMP_DIR=$(mktemp -d)
cd $TEMP_DIR

git clone https://github.com/yourusername/hvac-templates.git
cd hvac-templates/templates/$TEMPLATE_ID

# Step 3: Install dependencies
echo "📦 Installing dependencies..."
npm install
cd ../backend && npm install && cd ..

# Step 4: Build frontend
echo "🏗️  Building frontend..."
npm run build

# Step 5: Setup environment variables
echo "⚙️  Setting up environment variables..."
cat > .env.production << EOF
NEXT_PUBLIC_API_URL=https://api.$DOMAIN
NEXT_PUBLIC_DEPLOYMENT_ID=$DEPLOYMENT_ID
COMPANY_ID=$COMPANY_ID
EOF

# Step 6: Deploy to Vercel
echo "☁️  Deploying to Vercel..."
npx vercel --prod --token $VERCEL_TOKEN --name $COMPANY_ID

# Step 7: Setup custom domain
echo "🌐 Configuring domain..."
# Add DNS records via DNS provider API

# Step 8: Run health checks
echo "🏥 Running health checks..."
sleep 5
HEALTH_CHECK=$(curl -s -o /dev/null -w "%{http_code}" https://$DOMAIN)

if [ $HEALTH_CHECK -eq 200 ]; then
    echo "✅ Site is live!"

    # Update deployment status
    curl -s -X POST http://localhost:5000/api/deployments/$DEPLOYMENT_ID/deploy \
      -H "Content-Type: application/json"
else
    echo "❌ Health check failed (HTTP $HEALTH_CHECK)"
    exit 1
fi

# Step 9: Run performance tests
echo "📊 Running performance tests..."
npx lighthouse https://$DOMAIN --output json > lighthouse-report.json
SCORE=$(jq '.lighthouseResult.categories.performance.score' lighthouse-report.json | awk '{print int($1 * 100)}')
echo "📈 Performance Score: $SCORE"

# Cleanup
cd /
rm -rf $TEMP_DIR

echo "✨ Deployment Complete!"
echo "🎉 Your site is live at https://$DOMAIN"
