#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhance the dashboard HTML with cities and areas tables
Adds sections for cities first, then areas, then per-area customers
All with toggleable rows like the current customer table
"""
import json
import re

# Read the current data
with open('dashboard_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Extract cities and areas data from the JSON
cities = {}  # city -> {customers_count, total_gmv, customers_list}
areas = {}   # area -> {customers_count, total_gmv, customers_list}

# Process city groups
city_groups = data.get('city_groups', [])
for city_group in city_groups:
    city_name = city_group.get('name', 'غير محدد')
    customers = city_group.get('customers', [])
    total_gmv = sum(c.get('total_gmv', 0) for c in customers)
    
    cities[city_name] = {
        'count': len(customers),
        'gmv': total_gmv,
        'customers': customers
    }

# Process area groups
area_groups = data.get('area_groups', [])
for area_group in area_groups:
    area_name = area_group.get('name', 'غير محدد')
    customers = area_group.get('customers', [])
    total_gmv = sum(c.get('total_gmv', 0) for c in customers)
    
    areas[area_name] = {
        'count': len(customers),
        'gmv': total_gmv,
        'customers': customers
    }

# Sort by GMV
cities_sorted = sorted(cities.items(), key=lambda x: x[1]['gmv'], reverse=True)
areas_sorted = sorted(areas.items(), key=lambda x: x[1]['gmv'], reverse=True)

# Generate JavaScript code for cities table
cities_js = "const citiesData = " + json.dumps([{'name': city, 'count': data['count'], 'gmv': data['gmv'], 'customers': data['customers']} for city, data in cities_sorted], ensure_ascii=False, indent=2) + ";\n"

# Generate JavaScript code for areas table
areas_js = "const areasData = " + json.dumps([{'name': area, 'count': data['count'], 'gmv': data['gmv'], 'customers': data['customers']} for area, data in areas_sorted], ensure_ascii=False, indent=2) + ";\n"

# Save to a new JS file
with open('cities_areas_data.js', 'w', encoding='utf-8') as f:
    f.write(cities_js)
    f.write("\n")
    f.write(areas_js)
    f.write("""
    // Initialize cities and areas tables
    function initializeCitiesTable() {
        const tbody = document.getElementById('citiesTableBody');
        if (!tbody) return;
        
        citiesData.forEach((city, index) => {
            const row = document.createElement('tr');
            row.className = 'city-row';
            row.innerHTML = `
                <td>${city.name}</td>
                <td>${city.count}</td>
                <td>${Number(city.gmv).toLocaleString('ar')} EGP</td>
                <td>${(city.gmv / city.count).toLocaleString('ar')} EGP</td>
                <td>
                    <button class="toggle-details" onclick="toggleCity(${index})">عرض</button>
                </td>
            `;
            tbody.appendChild(row);
            
            // Add detail row
            const detailRow = document.createElement('tr');
            detailRow.className = 'city-detail-row hidden';
            detailRow.id = `city-${index}`;
            detailRow.innerHTML = `
                <td colspan="5">
                    <div class="customers-table-container">
                        <table class="customers-table">
                            <thead>
                                <tr>
                                    <th>اسم العميل</th>
                                    <th>النوع</th>
                                    <th>إجمالي GMV</th>
                                    <th>الطلبات الفريدة</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${city.customers.slice(0, 20).map(c => `
                                    <tr>
                                        <td>${c.name}</td>
                                        <td>${c.type}</td>
                                        <td>${Number(c.total_gmv).toLocaleString('ar')} EGP</td>
                                        <td>${c.unique_orders}</td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                </td>
            `;
            tbody.appendChild(detailRow);
        });
    }
    
    function toggleCity(index) {
        const row = document.getElementById(`city-${index}`);
        if (row) {
            row.classList.toggle('hidden');
        }
    }
    
    function initializeAreasTable() {
        const tbody = document.getElementById('areasTableBody');
        if (!tbody) return;
        
        areasData.forEach((area, index) => {
            const row = document.createElement('tr');
            row.className = 'area-row';
            row.innerHTML = `
                <td>${area.name}</td>
                <td>${area.count}</td>
                <td>${Number(area.gmv).toLocaleString('ar')} EGP</td>
                <td>${(area.gmv / area.count).toLocaleString('ar')} EGP</td>
                <td>
                    <button class="toggle-details" onclick="toggleArea(${index})">عرض</button>
                </td>
            `;
            tbody.appendChild(row);
            
            // Add detail row
            const detailRow = document.createElement('tr');
            detailRow.className = 'area-detail-row hidden';
            detailRow.id = `area-${index}`;
            detailRow.innerHTML = `
                <td colspan="5">
                    <div class="customers-table-container">
                        <table class="customers-table">
                            <thead>
                                <tr>
                                    <th>اسم العميل</th>
                                    <th>النوع</th>
                                    <th>إجمالي GMV</th>
                                    <th>الطلبات الفريدة</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${area.customers.slice(0, 20).map(c => `
                                    <tr>
                                        <td>${c.name}</td>
                                        <td>${c.type}</td>
                                        <td>${Number(c.total_gmv).toLocaleString('ar')} EGP</td>
                                        <td>${c.unique_orders}</td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                </td>
            `;
            tbody.appendChild(detailRow);
        });
    }
    
    function toggleArea(index) {
        const row = document.getElementById(`area-${index}`);
        if (row) {
            row.classList.toggle('hidden');
        }
    }
    
    // Initialize on page load
    document.addEventListener('DOMContentLoaded', function() {
        initializeCitiesTable();
        initializeAreasTable();
    });
""")

print("✅ Cities and areas data extracted and JavaScript generated!")
print(f"   Total cities: {len(cities_sorted)}")
print(f"   Total areas: {len(areas_sorted)}")
