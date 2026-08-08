import http.server
import socketserver
import urllib.parse
import json
import os
import sys
import time
import threading

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from atlas_scraper import search_places, fetch_place_full_details, count_places_in_region
from html_builder import generate_master_offline_viewer, generate_single_place_html
from csv_exporter import export_places_to_csv

PORT = 8000
OUTPUT_DIR = os.path.abspath("./output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

class AtlasAppHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=OUTPUT_DIR, **kwargs)

    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path

        if path == "/":
            self.send_home_page()
            return
        elif path == "/api/check-count":
            query_params = urllib.parse.parse_qs(parsed_path.query)
            query = query_params.get('q', [''])[0]
            
            polygon_str = query_params.get('polygon', [''])[0]
            polygon = json.loads(polygon_str) if polygon_str else None

            bbox_str = query_params.get('bbox', [''])[0]
            bbox_dict = None
            if bbox_str and not polygon:
                parts = [float(x) for x in bbox_str.split(',')]
                if len(parts) == 4:
                    bbox_dict = {'min_lat': parts[0], 'min_lon': parts[1], 'max_lat': parts[2], 'max_lon': parts[3]}

            if not query:
                self.send_json({'error': 'Country/Region name required'}, status=400)
                return

            res = count_places_in_region(query, polygon=polygon, bbox=bbox_dict)
            self.send_json({'success': True, 'data': res})
            return

        elif path == "/api/search":
            query_params = urllib.parse.parse_qs(parsed_path.query)
            query = query_params.get('q', [''])[0]
            max_str = query_params.get('max', ['30'])[0]
            
            if max_str == 'all':
                max_num = 9999
                delay_sec = 1.8  # Enforce ultra-safe speed for full uncapped region
            else:
                max_num = int(max_str)
                delay_sec = float(query_params.get('delay', [1.2])[0])
            
            polygon_str = query_params.get('polygon', [''])[0]
            polygon = json.loads(polygon_str) if polygon_str else None

            bbox_str = query_params.get('bbox', [''])[0]
            bbox_dict = None
            if bbox_str and not polygon:
                parts = [float(x) for x in bbox_str.split(',')]
                if len(parts) == 4:
                    bbox_dict = {'min_lat': parts[0], 'min_lon': parts[1], 'max_lat': parts[2], 'max_lon': parts[3]}
            
            if not query:
                self.send_json({'error': 'Country/Region name required'}, status=400)
                return

            print(f"[Web App] Starting polite download ({delay_sec}s delay) for '{query}' (Max: {max_str}, Polygon: {len(polygon) if polygon else 0} pts)...")
            places = search_places(query, max_results=max_num, bbox=bbox_dict, polygon=polygon, delay_sec=delay_sec)
            
            full_places = []
            cards_dir = os.path.join(OUTPUT_DIR, "cards")
            os.makedirs(cards_dir, exist_ok=True)
            
            for idx, p in enumerate(places, 1):
                slug = p.get('slug')
                print(f"  [{idx}/{len(places)}] Downloading details & photos: {p.get('title')}")
                detail = fetch_place_full_details(slug, max_images=3, embed_images=True)
                if detail:
                    full_places.append(detail)
                    card_filename = os.path.join(cards_dir, f"{slug}.html")
                    generate_single_place_html(detail, card_filename)
                time.sleep(delay_sec)  # Polite delay between full place downloads
            
            area_key = query.lower().replace(" ", "_")
            master_file = f"offline_viewer_{area_key}.html"
            master_path = os.path.join(OUTPUT_DIR, master_file)
            generate_master_offline_viewer(full_places, query, master_path)
            
            self.send_json({
                'success': True,
                'query': query,
                'count': len(full_places),
                'viewer_url': f"/{master_file}",
                'places': full_places
            })
            return

        super().do_GET()

    def do_POST(self):
        parsed_path = urllib.parse.urlparse(self.path)
        if parsed_path.path == "/api/export-csv":
            content_len = int(self.headers.get('Content-Length', 0))
            post_body = self.rfile.read(content_len)
            data = json.loads(post_body.decode('utf-8'))
            
            places = data.get('places', [])
            filename = data.get('filename', 'interested_places.csv')
            
            csv_path = os.path.join(OUTPUT_DIR, filename)
            export_places_to_csv(places, csv_path)
            
            self.send_json({
                'success': True,
                'csv_url': f"/{filename}",
                'path': csv_path
            })
            return

    def send_json(self, data, status=200):
        body = json.dumps(data).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_home_page(self):
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Atlas Obscura Polite Offline Explorer</title>
    <!-- Leaflet CSS & JS -->
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    
    <!-- Leaflet Draw CSS & JS -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet.draw/1.0.4/leaflet.draw.css" />
    <script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet.draw/1.0.4/leaflet.draw.js"></script>

    <style>
        :root {{
            --bg: #0f172a;
            --panel: #1e293b;
            --accent: #f59e0b;
            --cyan: #38bdf8;
            --text: #f8fafc;
            --muted: #94a3b8;
            --border: #334155;
            --success: #22c55e;
            --danger: #ef4444;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', system-ui, -apple-system, sans-serif; }}
        body {{ background: var(--bg); color: var(--text); padding: 20px; display: flex; flex-direction: column; align-items: center; min-height: 100vh; }}
        .main-container {{ display: flex; flex-direction: column; max-width: 1150px; width: 100%; gap: 20px; }}
        
        .header-box {{ background: var(--panel); border: 1px solid var(--border); border-radius: 16px; padding: 24px 32px; box-shadow: 0 10px 25px rgba(0,0,0,0.4); }}
        h1 {{ font-size: 26px; color: #fff; margin-bottom: 6px; display: flex; align-items: center; gap: 10px; }}
        h1 span {{ color: var(--accent); }}
        p.subtitle {{ color: var(--muted); font-size: 14px; margin-bottom: 20px; line-height: 1.5; }}
        
        .workflow-banner {{ background: rgba(56, 189, 248, 0.1); border-left: 4px solid var(--cyan); padding: 14px 18px; border-radius: 8px; margin-bottom: 20px; font-size: 14px; color: #e0f2fe; line-height: 1.6; }}
        
        .form-row {{ display: flex; gap: 12px; flex-wrap: wrap; align-items: center; margin-bottom: 12px; }}
        input[type="text"] {{ flex: 1; min-width: 240px; padding: 12px 16px; border-radius: 10px; border: 1px solid var(--border); background: #0f172a; color: #fff; font-size: 15px; outline: none; }}
        input[type="text"]:focus {{ border-color: var(--cyan); }}
        select {{ padding: 12px 14px; border-radius: 10px; border: 1px solid var(--border); background: #0f172a; color: #fff; font-size: 14px; outline: none; }}
        
        .btn {{ background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); color: white; border: none; padding: 12px 20px; border-radius: 10px; font-weight: 700; font-size: 14px; cursor: pointer; transition: all 0.2s; display: inline-flex; align-items: center; gap: 8px; }}
        .btn:hover {{ transform: translateY(-2px); box-shadow: 0 4px 12px rgba(245, 158, 11, 0.4); }}
        .btn-cyan {{ background: linear-gradient(135deg, #38bdf8 0%, #0284c7 100%); }}
        .btn-success {{ background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%); }}
        .btn-danger {{ background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); }}
        
        .map-section {{ background: var(--panel); border: 1px solid var(--border); border-radius: 16px; overflow: hidden; display: flex; flex-direction: column; height: 520px; box-shadow: 0 10px 25px rgba(0,0,0,0.4); }}
        .map-toolbar {{ padding: 12px 20px; background: rgba(15, 23, 42, 0.85); border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px; font-size: 14px; }}
        #map {{ width: 100%; height: 100%; background: #0f172a; }}
        
        .draw-actions {{ display: flex; gap: 8px; align-items: center; }}
        .badge-info {{ background: #0f172a; padding: 6px 12px; border-radius: 8px; border: 1px solid var(--border); font-size: 13px; color: var(--accent); font-weight: 600; }}
        
        .status-box {{ padding: 16px; background: rgba(15, 23, 42, 0.6); border-radius: 10px; border: 1px solid var(--border); font-size: 14px; margin-top: 10px; display: none; line-height: 1.5; }}
        .loading {{ display: none; text-align: center; margin: 12px 0; color: var(--cyan); font-weight: 600; line-height: 1.6; }}
    </style>
</head>
<body>
    <div class="main-container">
        <div class="header-box">
            <h1>🧭 <span>Atlas Obscura</span> Polite Offline Explorer</h1>
            <p class="subtitle">Download offline HTML cards with photos & Google My Maps CSV. Rate-limit safe with custom polygon shapes.</p>
            
            <div class="workflow-banner">
                <strong>🛡️ Safe Scraping Workflow:</strong><br/>
                1. Type Country/City name and draw your optional <strong>Polygon</strong> shape on the map.<br/>
                2. Click <strong>"🔍 Check Places Count"</strong> to see how many places exist in your target shape.<br/>
                3. Click <strong>"📥 Download Offline Bundle"</strong> to fetch politely (1.2s delay between requests).
            </div>
            
            <div class="form-row">
                <input type="text" id="queryInput" placeholder="Enter Country or Region (e.g. Spain, France, Latvia)..." value="Spain" />
                
                <select id="maxSelect" onchange="handleMaxChange()">
                    <option value="15">Max 15 Places</option>
                    <option value="30" selected>Max 30 Places</option>
                    <option value="50">Max 50 Places</option>
                    <option value="100">Max 100 Places</option>
                    <option value="all">🌟 All Places in Region (Uncapped)</option>
                </select>

                <select id="delaySelect" title="Request delay to prevent website rate limits">
                    <option value="1.2" selected>⏱️ Polite (1.2s delay)</option>
                    <option value="1.8">🛡️ Ultra-Safe (1.8s delay)</option>
                    <option value="0.6">⚡ Fast (0.6s delay)</option>
                </select>

                <button class="btn btn-cyan" onclick="checkPlaceCount()">
                    🔍 1. Check Count in Area
                </button>
                <button class="btn btn-success" onclick="startDownload()">
                    📥 2. Download Offline Bundle
                </button>
            </div>
            <div id="safetyNotice" style="font-size: 13px; color: var(--accent); margin-top: 4px; display: none; font-weight: 600;">
                🛡️ Ultra-Safe mode (1.8s delay per place) automatically enforced for 'All Places' download.
            </div>
            
            <div class="status-box" id="statusBox"></div>
            <div class="loading" id="loadingState">
                ⏳ Politely downloading place details & high-res photos for your selected shape...<br/>
                <span style="font-size: 13px; color: var(--muted);" id="loadingSubtext">Downloading slowly with delay to prevent rate limits...</span>
            </div>
        </div>

        <div class="map-section">
            <div class="map-toolbar">
                <div class="badge-info" id="shapeBadge">
                    📌 Map Filter: Whole Country/Region (No shape drawn)
                </div>
                
                <div class="draw-actions">
                    <button class="btn btn-cyan" style="padding: 6px 12px; font-size: 13px;" onclick="enableDrawPolygon()">🔷 Draw Polygon</button>
                    <button class="btn btn-cyan" style="padding: 6px 12px; font-size: 13px;" onclick="enableDrawRectangle()">⬛ Draw Rectangle</button>
                    <button class="btn btn-danger" style="padding: 6px 12px; font-size: 13px;" onclick="clearDrawnShape()">🗑️ Clear Shape</button>
                </div>
            </div>
            <div id="map"></div>
        </div>
    </div>

    <script>
        let map = L.map('map').setView([40.4168, -3.7038], 5);
        L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
            attribution: '&copy; OpenStreetMap contributors'
        }}).addTo(map);

        let drawnItems = new L.FeatureGroup();
        map.addLayer(drawnItems);

        let drawPolygonHandler = new L.Draw.Polygon(map, {{
            shapeOptions: {{ color: '#f59e0b', weight: 3, fillColor: '#f59e0b', fillOpacity: 0.2 }}
        }});

        let drawRectangleHandler = new L.Draw.Rectangle(map, {{
            shapeOptions: {{ color: '#38bdf8', weight: 3, fillColor: '#38bdf8', fillOpacity: 0.2 }}
        }});

        let currentShapeLayer = null;
        let selectedPolygonCoords = null; // List of [lat, lon]

        map.on(L.Draw.Event.CREATED, function (e) {{
            clearDrawnShape();
            currentShapeLayer = e.layer;
            drawnItems.addLayer(currentShapeLayer);

            if (e.layerType === 'polygon' || e.layerType === 'rectangle') {{
                const latLngs = currentShapeLayer.getLatLngs()[0];
                selectedPolygonCoords = latLngs.map(pt => [pt.lat, pt.lng]);
                document.getElementById('shapeBadge').innerText = '🔷 Custom ' + e.layerType.toUpperCase() + ' Filter Active (' + selectedPolygonCoords.length + ' points)';
                document.getElementById('shapeBadge').style.color = '#38bdf8';
            }}
        }});

        function enableDrawPolygon() {{
            drawRectangleHandler.disable();
            drawPolygonHandler.enable();
            updateStatus("Click points on map to draw custom polygon. Click first point to finish shape.");
        }}

        function enableDrawRectangle() {{
            drawPolygonHandler.disable();
            drawRectangleHandler.enable();
            updateStatus("Click & drag on map to draw a custom selection rectangle.");
        }}

        function clearDrawnShape() {{
            drawnItems.clearLayers();
            currentShapeLayer = null;
            selectedPolygonCoords = null;
            document.getElementById('shapeBadge').innerText = '📌 Map Filter: Whole Country/Region (No shape drawn)';
            document.getElementById('shapeBadge').style.color = '#f59e0b';
        }}

        function handleMaxChange() {{
            const maxVal = document.getElementById('maxSelect').value;
            const delaySelect = document.getElementById('delaySelect');
            const safetyNotice = document.getElementById('safetyNotice');

            if (maxVal === 'all') {{
                delaySelect.value = "1.8";
                delaySelect.disabled = true;
                safetyNotice.style.display = 'block';
            }} else {{
                delaySelect.disabled = false;
                safetyNotice.style.display = 'none';
            }}
        }}

        function formatTime(totalSec) {{
            if (totalSec < 60) return '~' + Math.round(totalSec) + ' seconds';
            const mins = Math.floor(totalSec / 60);
            const secs = Math.round(totalSec % 60);
            return '~' + mins + ' min ' + (secs > 0 ? secs + 's' : '');
        }}

        function checkPlaceCount() {{
            const query = document.getElementById('queryInput').value.trim();
            const maxVal = document.getElementById('maxSelect').value;
            if (!query) {{
                alert("Please enter a country or region name!");
                return;
            }}

            document.getElementById('loadingState').style.display = 'block';
            document.getElementById('loadingSubtext').innerText = "Checking available place count in region...";
            document.getElementById('statusBox').style.display = 'none';

            let url = `/api/check-count?q=${{encodeURIComponent(query)}}`;
            if (selectedPolygonCoords && selectedPolygonCoords.length >= 3) {{
                url += `&polygon=${{encodeURIComponent(JSON.stringify(selectedPolygonCoords))}}`;
            }}

            fetch(url)
                .then(r => r.json())
                .then(res => {{
                    document.getElementById('loadingState').style.display = 'none';
                    if (res.success) {{
                        const data = res.data;
                        const count = data.matched_in_region;
                        const isAll = maxVal === 'all';
                        const delaySec = isAll ? 1.8 : parseFloat(document.getElementById('delaySelect').value);
                        const downloadCount = isAll ? count : Math.min(count, parseInt(maxVal));
                        const estSeconds = downloadCount * (delaySec + 0.3);
                        
                        const statusBox = document.getElementById('statusBox');
                        statusBox.style.display = 'block';
                        statusBox.innerHTML = `
                            <h3 style="color: var(--cyan); margin-bottom: 6px;">📊 Place Count Check Results:</h3>
                            <p style="margin-bottom: 6px;">
                                Found <strong>${{count}}</strong> places inside your drawn shape (out of ${{data.total_found}} total in ${{data.query}}).
                            </p>
                            <p style="color: var(--accent); font-size: 13px; font-weight: 600;">
                                ⏱️ Selected Download: <strong>${{downloadCount}} places</strong> at ${{delaySec}}s delay per place &rarr; Estimated time: <strong>${{formatTime(estSeconds)}}</strong>.
                            </p>
                        `;
                        plotDownloadedPlaces(data.places);
                    }}
                }})
                .catch(err => {{
                    document.getElementById('loadingState').style.display = 'none';
                    alert("Count check failed: " + err);
                }});
        }}

        function startDownload() {{
            const query = document.getElementById('queryInput').value.trim();
            const maxNum = document.getElementById('maxSelect').value;
            const delaySec = document.getElementById('delaySelect').value;

            if (!query) {{
                alert("Please enter a country or region name!");
                return;
            }}

            document.getElementById('loadingState').style.display = 'block';
            document.getElementById('loadingSubtext').innerText = `Downloading up to ${{maxNum}} places with ${{delaySec}}s polite delay to prevent website rate limits...`;
            document.getElementById('statusBox').style.display = 'none';

            let url = `/api/search?q=${{encodeURIComponent(query)}}&max=${{maxNum}}&delay=${{delaySec}}`;
            if (selectedPolygonCoords && selectedPolygonCoords.length >= 3) {{
                url += `&polygon=${{encodeURIComponent(JSON.stringify(selectedPolygonCoords))}}`;
            }}

            fetch(url)
                .then(r => r.json())
                .then(data => {{
                    document.getElementById('loadingState').style.display = 'none';
                    if (data.success) {{
                        const statusBox = document.getElementById('statusBox');
                        statusBox.style.display = 'block';
                        statusBox.innerHTML = `
                            <h3 style="color: var(--success); margin-bottom: 8px;">✅ Offline Bundle Created Successfully!</h3>
                            <p style="margin-bottom: 12px;">Downloaded <strong>${{data.count}}</strong> places with offline photos for '${{query}}'.</p>
                            <a href="${{data.viewer_url}}" target="_blank" style="display: inline-block; background: var(--success); color: white; padding: 12px 20px; border-radius: 8px; font-weight: 700; text-decoration: none;">
                                Open Master Offline Viewer ↗
                            </a>
                        `;
                        plotDownloadedPlaces(data.places);
                    }} else {{
                        alert('Error: ' + (data.error || 'Failed to download area'));
                    }}
                }})
                .catch(err => {{
                    document.getElementById('loadingState').style.display = 'none';
                    alert('Download failed: ' + err);
                }});
        }}

        let resultMarkersLayer = L.layerGroup().addTo(map);
        function plotDownloadedPlaces(places) {{
            resultMarkersLayer.clearLayers();
            if (!places || places.length === 0) return;
            
            let bounds = L.latLngBounds();
            places.forEach(p => {{
                if (p.lat && p.lon) {{
                    const pt = [p.lat, p.lon];
                    bounds.extend(pt);
                    L.marker(pt).bindPopup(`<b>${{p.title}}</b><br>${{p.location || ''}}`).addTo(resultMarkersLayer);
                }}
            }});
            if (bounds.isValid()) {{
                map.fitBounds(bounds, {{ padding: [30, 30] }});
            }}
        }}

        function updateStatus(msg) {{
            const statusBox = document.getElementById('statusBox');
            statusBox.style.display = 'block';
            statusBox.innerHTML = `<span style="color: var(--cyan);">${{msg}}</span>`;
        }}
    </script>
</body>
</html>
"""
        body = html.encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

def start_server():
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), AtlasAppHandler) as httpd:
        print(f"🚀 Atlas Obscura Explorer Web App running at: http://localhost:{PORT}")
        httpd.serve_forever()

if __name__ == "__main__":
    start_server()
