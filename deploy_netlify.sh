#!/bin/bash

# Netlify Deployment Script
# This script helps you deploy the dashboard to Netlify

echo "🚀 Netlify Deployment Helper"
echo "=============================="
echo ""
echo "Choose deployment method:"
echo "1. Deploy via Netlify CLI (requires netlify-cli installed)"
echo "2. Show manual deployment instructions"
echo "3. Create deployment package (zip file)"
echo ""
read -p "Enter choice (1-3): " choice

case $choice in
  1)
    echo ""
    echo "📦 Deploying via Netlify CLI..."
    if ! command -v netlify &> /dev/null; then
      echo "❌ Netlify CLI not found. Install it with: npm install -g netlify-cli"
      exit 1
    fi
    
    echo "Checking if logged in..."
    netlify status || netlify login
    
    echo ""
    echo "Initializing deployment..."
    netlify deploy --prod
    ;;
    
  2)
    echo ""
    echo "📋 Manual Deployment Instructions:"
    echo "===================================="
    echo ""
    echo "1. Go to https://app.netlify.com"
    echo "2. Click 'Add new site' → 'Deploy manually'"
    echo "3. Drag and drop your project folder"
    echo "4. Make sure these files are included:"
    echo "   - horeca_optimized_dashboard.html"
    echo "   - dashboard_data.json"
    echo "   - netlify.toml"
    echo "   - _redirects"
    echo ""
    echo "Or zip the folder and upload the zip file."
    ;;
    
  3)
    echo ""
    echo "📦 Creating deployment package..."
    ZIP_NAME="horeca-dashboard-$(date +%Y%m%d-%H%M%S).zip"
    
    # Create zip with required files
    zip -r "$ZIP_NAME" \
      horeca_optimized_dashboard.html \
      dashboard_data.json \
      netlify.toml \
      _redirects \
      README_NETLIFY.md 2>/dev/null || \
    tar -czf "${ZIP_NAME%.zip}.tar.gz" \
      horeca_optimized_dashboard.html \
      dashboard_data.json \
      netlify.toml \
      _redirects \
      README_NETLIFY.md
    
    if [ -f "$ZIP_NAME" ] || [ -f "${ZIP_NAME%.zip}.tar.gz" ]; then
      echo "✅ Package created: $ZIP_NAME (or .tar.gz)"
      echo "   Upload this file to Netlify via their dashboard"
    else
      echo "❌ Failed to create package. Make sure zip or tar is installed."
    fi
    ;;
    
  *)
    echo "Invalid choice"
    exit 1
    ;;
esac

echo ""
echo "✅ Done!"

