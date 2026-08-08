import csv
import os
import sys
from typing import List, Dict, Any

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def export_places_to_csv(places: List[Dict[str, Any]], filepath: str) -> str:
    """
    Exports a list of place dictionaries to a CSV file formatted for Google My Maps.
    
    Expected CSV Header:
    Name, Latitude, Longitude, Description, Url, Location
    """
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    
    headers = ['Name', 'Latitude', 'Longitude', 'Description', 'Url', 'Location']
    
    with open(filepath, mode='w', newline='', encoding='utf-8') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(headers)
        
        for place in places:
            name = place.get('title') or place.get('name', 'Unknown Place')
            lat = place.get('lat') or place.get('latitude', '')
            lon = place.get('lon') or place.get('lng') or place.get('longitude', '')
            
            subtitle = place.get('subtitle', '')
            location = place.get('location', '')
            url = place.get('url', '')
            
            # Combine subtitle & location for a clean description field in Google My Maps
            desc_parts = []
            if subtitle:
                desc_parts.append(subtitle)
            if location:
                desc_parts.append(f"Location: {location}")
            if url:
                desc_parts.append(f"Atlas Obscura: {url}")
                
            description = " | ".join(desc_parts)
            
            writer.writerow([name, lat, lon, description, url, location])
            
    print(f"[CSV Exporter] Exported {len(places)} places to: {filepath}")
    return filepath
