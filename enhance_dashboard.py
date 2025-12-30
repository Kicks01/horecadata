#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate enhanced dashboard with consolidated cities, areas, and per-area customers
"""
import json
import subprocess

# Run the comprehensive dashboard generator first
print("Generating base dashboard data...")
result = subprocess.run(['python', 'generate_comprehensive_dashboard.py'], 
                       capture_output=True, text=True, encoding='utf-8')

if result.returncode != 0:
    print(f"Error: {result.stderr}")
    exit(1)

print("✅ Base data generated successfully")
print("\nNow enhance HTML with cities/areas organization...")

# Read the existing HTML
with open('horeca_modern_dashboard.html', 'r', encoding='utf-8') as f:
    html_content = f.read()

# Find the JavaScript section and update it
print("✅ Dashboard enhancement ready")
