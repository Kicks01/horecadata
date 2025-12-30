# Netlify Deployment Guide

This dashboard can be deployed to Netlify easily. Follow these steps:

## Option 1: Deploy via Netlify CLI

1. Install Netlify CLI:
   ```bash
   npm install -g netlify-cli
   ```

2. Login to Netlify:
   ```bash
   netlify login
   ```

3. Initialize and deploy:
   ```bash
   netlify init
   netlify deploy --prod
   ```

## Option 2: Deploy via Netlify Dashboard

1. Go to [Netlify](https://app.netlify.com)
2. Click "Add new site" → "Deploy manually"
3. Drag and drop your project folder (or zip it first)
4. Make sure these files are included:
   - `horeca_optimized_dashboard.html`
   - `dashboard_data.json`
   - `netlify.toml`
   - `_redirects`

## Option 3: Deploy via Git

1. Push your code to GitHub/GitLab/Bitbucket
2. Go to Netlify Dashboard
3. Click "Add new site" → "Import an existing project"
4. Connect your repository
5. Build settings:
   - Build command: (leave empty or use `echo 'No build step'`)
   - Publish directory: `.` (root)
6. Click "Deploy site"

## Required Files

Make sure these files are in your deployment:
- `horeca_optimized_dashboard.html` - Main dashboard file
- `dashboard_data.json` - Data file (must be in same directory)
- `netlify.toml` - Netlify configuration
- `_redirects` - URL redirects configuration

## Notes

- The dashboard expects `dashboard_data.json` to be in the same directory
- If your JSON file has a different name or location, update the fetch URL in the HTML file
- The site will be available at `https://your-site-name.netlify.app`

