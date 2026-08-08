import os
import json
from typing import List, Dict, Any

def generate_single_place_html(place: Dict[str, Any], output_path: str) -> str:
    """Generates a standalone offline HTML page for an individual Atlas Obscura place."""
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    
    title = place.get('title', 'Atlas Obscura Place')
    subtitle = place.get('subtitle', '')
    location = place.get('location', '')
    lat = place.get('lat', 'N/A')
    lon = place.get('lon', 'N/A')
    url = place.get('url', '#')
    description_paragraphs = place.get('description_paragraphs', [])
    images = place.get('images_b64', place.get('image_urls', []))
    
    paragraphs_html = "".join([f"<p>{p}</p>" for p in description_paragraphs]) if description_paragraphs else f"<p>{subtitle}</p>"
    
    images_html = ""
    for idx, img_src in enumerate(images):
        images_html += f'<div class="gallery-item"><img src="{img_src}" alt="{title} Image {idx+1}" /></div>'
        
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - Atlas Obscura Offline</title>
    <style>
        :root {{
            --bg-color: #0f172a;
            --card-bg: #1e293b;
            --accent-gold: #f59e0b;
            --accent-blue: #38bdf8;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --border-color: #334155;
            --success: #22c55e;
            --danger: #ef4444;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', system-ui, -apple-system, sans-serif; }}
        body {{ background-color: var(--bg-color); color: var(--text-main); line-height: 1.6; padding: 20px; display: flex; justify-content: center; }}
        .container {{ max-width: 800px; width: 100%; background-color: var(--card-bg); border-radius: 16px; border: 1px solid var(--border-color); overflow: hidden; box-shadow: 0 20px 25px -5px rgba(0,0,0,0.5); }}
        .header {{ padding: 24px; border-bottom: 1px solid var(--border-color); background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); }}
        .badge {{ display: inline-block; background: rgba(245, 158, 11, 0.15); color: var(--accent-gold); border: 1px solid var(--accent-gold); border-radius: 20px; font-size: 12px; font-weight: 600; padding: 4px 12px; margin-bottom: 12px; }}
        h1 {{ font-size: 28px; font-weight: 700; color: #fff; margin-bottom: 8px; }}
        h1 a {{ color: #fff; text-decoration: none; transition: color 0.2s; }}
        h1 a:hover {{ color: var(--accent-blue); text-decoration: underline; }}
        .subtitle {{ color: var(--accent-blue); font-size: 16px; margin-bottom: 16px; font-style: italic; }}
        .meta-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; margin-top: 16px; background: rgba(15, 23, 42, 0.6); padding: 14px; border-radius: 10px; border: 1px solid var(--border-color); }}
        .meta-item {{ font-size: 14px; color: var(--text-muted); }}
        .meta-item strong {{ color: var(--text-main); display: block; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; }}
        
        .action-bar {{ display: flex; gap: 12px; padding: 16px 24px; background-color: rgba(0,0,0,0.2); border-bottom: 1px solid var(--border-color); }}
        .btn {{ flex: 1; border: none; padding: 12px 20px; border-radius: 10px; font-weight: 600; font-size: 15px; cursor: pointer; transition: all 0.2s ease; display: flex; align-items: center; justify-content: center; gap: 8px; text-decoration: none; }}
        .btn-interested {{ background: var(--success); color: white; }}
        .btn-interested:hover {{ background: #16a34a; transform: translateY(-2px); }}
        .btn-skip {{ background: #334155; color: var(--text-muted); }}
        .btn-skip:hover {{ background: var(--danger); color: white; transform: translateY(-2px); }}
        .btn-online {{ background: rgba(56, 189, 248, 0.15); color: var(--accent-blue); border: 1px solid var(--accent-blue); }}
        .btn-online:hover {{ background: var(--accent-blue); color: #0f172a; transform: translateY(-2px); }}
        .btn.active-interested {{ outline: 3px solid #86efac; box-shadow: 0 0 15px rgba(34, 197, 94, 0.4); }}
        .btn.active-skip {{ outline: 3px solid #fca5a5; opacity: 0.7; }}
        
        .content {{ padding: 24px; }}
        .gallery {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 16px; margin-bottom: 24px; }}
        .gallery-item {{ border-radius: 12px; overflow: hidden; border: 1px solid var(--border-color); height: 220px; background: #0f172a; }}
        .gallery-item img {{ width: 100%; height: 100%; object-fit: cover; }}
        
        .description {{ font-size: 16px; color: #cbd5e1; }}
        .description p {{ margin-bottom: 16px; }}
        
        .footer {{ padding: 16px 24px; border-top: 1px solid var(--border-color); display: flex; justify-content: space-between; align-items: center; background: #0f172a; font-size: 13px; color: var(--text-muted); }}
        .footer a {{ color: var(--accent-blue); text-decoration: none; font-weight: 500; }}
        .footer a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <span class="badge">OFFLINE MAP CARD</span>
            <h1><a href="{url}" target="_blank" rel="noopener">{title} ↗</a></h1>
            <div class="subtitle">{subtitle}</div>
            <div class="meta-grid">
                <div class="meta-item"><strong>Location</strong> {location}</div>
                <div class="meta-item"><strong>Coordinates (Lat, Lon)</strong> {lat}, {lon}</div>
            </div>
        </div>

        <div class="action-bar">
            <button class="btn btn-interested" id="btnInterested" onclick="toggleStatus('interested')">
                ⭐ Mark Interested
            </button>
            <button class="btn btn-skip" id="btnSkip" onclick="toggleStatus('skip')">
                ❌ Skip Place
            </button>
            <a class="btn btn-online" href="{url}" target="_blank" rel="noopener">
                🌐 Open Online ↗
            </a>
        </div>

        <div class="content">
            <div class="gallery">
                {images_html}
            </div>
            <div class="description">
                {paragraphs_html}
            </div>
        </div>

        <div class="footer">
            <span>Offline Ready (Images Embedded)</span>
            <a href="{url}" target="_blank" rel="noopener">View on Atlas Obscura ↗</a>
        </div>
    </div>

    <script>
        const placeId = "{place.get('slug', 'place')}";
        
        function updateUI() {{
            const status = localStorage.getItem('ao_status_' + placeId);
            const btnInt = document.getElementById('btnInterested');
            const btnSkip = document.getElementById('btnSkip');
            
            btnInt.classList.remove('active-interested');
            btnSkip.classList.remove('active-skip');
            
            if (status === 'interested') {{
                btnInt.classList.add('active-interested');
                btnInt.innerText = '⭐ Interested (Selected)';
            }} else if (status === 'skip') {{
                btnSkip.classList.add('active-skip');
                btnSkip.innerText = '❌ Skipped';
            }}
        }}
        
        function toggleStatus(newStatus) {{
            const current = localStorage.getItem('ao_status_' + placeId);
            if (current === newStatus) {{
                localStorage.removeItem('ao_status_' + placeId);
            }} else {{
                localStorage.setItem('ao_status_' + placeId, newStatus);
            }}
            updateUI();
        }}
        
        document.addEventListener('DOMContentLoaded', updateUI);
    </script>
</body>
</html>
"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
        
    return output_path


def generate_master_offline_viewer(places: List[Dict[str, Any]], area_name: str, output_path: str) -> str:
    """
    Generates a master interactive offline HTML collection dashboard containing all places.
    Includes card deck review UI, filtering, offline map/images, direct URLs, and client-side Google My Maps CSV export.
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    
    places_json = json.dumps(places)
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Atlas Obscura Offline Explorer - {area_name}</title>
    <style>
        :root {{
            --bg-dark: #0f172a;
            --panel-bg: #1e293b;
            --card-bg: #1e293b;
            --accent-gold: #f59e0b;
            --accent-cyan: #38bdf8;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --border-color: #334155;
            --success-color: #22c55e;
            --danger-color: #ef4444;
        }}
        
        * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', system-ui, -apple-system, sans-serif; }}
        body {{ background-color: var(--bg-dark); color: var(--text-primary); min-height: 100vh; display: flex; flex-direction: column; }}
        
        header {{
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            border-bottom: 1px solid var(--border-color);
            padding: 20px 32px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 16px;
            position: sticky;
            top: 0;
            z-index: 100;
            backdrop-filter: blur(10px);
        }}
        
        .brand-title {{ font-size: 24px; font-weight: 800; color: #fff; display: flex; align-items: center; gap: 10px; }}
        .brand-title span {{ color: var(--accent-gold); }}
        
        .stats-bar {{ display: flex; gap: 16px; background: rgba(15, 23, 42, 0.7); padding: 8px 16px; border-radius: 12px; border: 1px solid var(--border-color); }}
        .stat-item {{ font-size: 14px; color: var(--text-secondary); }}
        .stat-item strong {{ color: #fff; font-size: 15px; margin-left: 4px; }}
        
        .controls {{ display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }}
        .filter-btn {{
            background: var(--panel-bg);
            color: var(--text-secondary);
            border: 1px solid var(--border-color);
            padding: 8px 16px;
            border-radius: 8px;
            font-weight: 600;
            font-size: 14px;
            cursor: pointer;
            transition: all 0.2s;
        }}
        .filter-btn:hover, .filter-btn.active {{ background: var(--accent-cyan); color: #0f172a; border-color: var(--accent-cyan); }}
        
        .btn-export {{
            background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            font-weight: 700;
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(34, 197, 94, 0.3);
            transition: all 0.2s;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .btn-export:hover {{ transform: translateY(-2px); box-shadow: 0 6px 16px rgba(34, 197, 94, 0.4); }}
        
        main {{ flex: 1; padding: 32px; max-width: 1400px; margin: 0 auto; width: 100%; }}
        
        .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 24px; }}
        
        .card {{
            background: var(--card-bg);
            border-radius: 16px;
            border: 1px solid var(--border-color);
            overflow: hidden;
            display: flex;
            flex-direction: column;
            transition: transform 0.2s, box-shadow 0.2s;
            position: relative;
        }}
        .card:hover {{ transform: translateY(-4px); box-shadow: 0 12px 24px rgba(0,0,0,0.4); border-color: #475569; }}
        
        .card-img-link {{ display: block; height: 200px; width: 100%; overflow: hidden; background: #0f172a; }}
        .card-img {{ width: 100%; height: 100%; object-fit: cover; transition: transform 0.3s; }}
        .card-img-link:hover .card-img {{ transform: scale(1.05); }}
        
        .card-body {{ padding: 20px; flex: 1; display: flex; flex-direction: column; }}
        
        .card-title-link {{ font-size: 18px; font-weight: 700; color: #fff; text-decoration: none; margin-bottom: 6px; line-height: 1.3; transition: color 0.2s; }}
        .card-title-link:hover {{ color: var(--accent-cyan); text-decoration: underline; }}
        
        .card-subtitle {{ font-size: 14px; color: var(--accent-cyan); font-style: italic; margin-bottom: 12px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }}
        .card-location {{ font-size: 13px; color: var(--text-secondary); margin-bottom: 12px; display: flex; align-items: center; gap: 6px; }}
        .card-coords {{ font-size: 12px; color: #64748b; font-family: monospace; background: #0f172a; padding: 4px 8px; border-radius: 6px; margin-bottom: 16px; display: inline-block; }}
        
        .card-actions {{ display: flex; gap: 8px; margin-top: auto; padding-top: 12px; border-top: 1px solid var(--border-color); flex-wrap: wrap; }}
        
        .btn-card {{
            flex: 1;
            padding: 8px 10px;
            border-radius: 8px;
            border: 1px solid var(--border-color);
            font-weight: 600;
            font-size: 12px;
            cursor: pointer;
            transition: all 0.2s;
            text-align: center;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            justify-content: center;
        }}
        .btn-interest-card {{ background: rgba(34, 197, 94, 0.1); color: var(--success-color); border-color: var(--success-color); }}
        .btn-interest-card:hover, .card.interested .btn-interest-card {{ background: var(--success-color); color: white; }}
        
        .btn-skip-card {{ background: rgba(239, 68, 68, 0.1); color: var(--danger-color); border-color: var(--danger-color); }}
        .btn-skip-card:hover, .card.skipped .btn-skip-card {{ background: var(--danger-color); color: white; }}
        
        .btn-online-card {{ background: rgba(56, 189, 248, 0.1); color: var(--accent-cyan); border-color: var(--accent-cyan); }}
        .btn-online-card:hover {{ background: var(--accent-cyan); color: #0f172a; }}
        
        .card-badge {{
            position: absolute;
            top: 12px;
            right: 12px;
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            display: none;
            z-index: 10;
        }}
        .card.interested .card-badge.interested-badge {{ display: block; background: var(--success-color); color: white; }}
        .card.skipped .card-badge.skipped-badge {{ display: block; background: var(--danger-color); color: white; }}
        
        .empty-state {{ text-align: center; padding: 60px; color: var(--text-secondary); grid-column: 1 / -1; }}
    </style>
</head>
<body>
    <header>
        <div class="brand-title">
            🧭 <span>Atlas Obscura</span> Explorer ({area_name})
        </div>
        
        <div class="stats-bar">
            <div class="stat-item">Total: <strong id="statTotal">0</strong></div>
            <div class="stat-item">Interested: <strong id="statInterested" style="color: var(--success-color);">0</strong></div>
            <div class="stat-item">Skipped: <strong id="statSkipped" style="color: var(--danger-color);">0</strong></div>
        </div>
        
        <div class="controls">
            <button class="filter-btn active" onclick="setFilter('all', this)">All</button>
            <button class="filter-btn" onclick="setFilter('interested', this)">⭐ Interested</button>
            <button class="filter-btn" onclick="setFilter('skipped', this)">❌ Skipped</button>
            <button class="filter-btn" onclick="setFilter('unreviewed', this)">⏳ Unreviewed</button>
            
            <button class="btn-export" onclick="exportCSV()">
                📥 Export Google My Maps CSV
            </button>
        </div>
    </header>

    <main>
        <div class="grid" id="placesGrid"></div>
    </main>

    <script>
        const placesData = {places_json};
        const areaKey = "{area_name.lower().replace(' ', '_')}";
        let currentFilter = 'all';

        function getStatus(slug) {{
            return localStorage.getItem('ao_status_' + slug) || 'unreviewed';
        }}

        function setStatus(slug, status) {{
            const current = getStatus(slug);
            if (current === status) {{
                localStorage.setItem('ao_status_' + slug, 'unreviewed');
            }} else {{
                localStorage.setItem('ao_status_' + slug, status);
            }}
            render();
        }}

        function updateStats() {{
            let interested = 0, skipped = 0;
            placesData.forEach(p => {{
                const st = getStatus(p.slug);
                if (st === 'interested') interested++;
                if (st === 'skip' || st === 'skipped') skipped++;
            }});
            document.getElementById('statTotal').innerText = placesData.length;
            document.getElementById('statInterested').innerText = interested;
            document.getElementById('statSkipped').innerText = skipped;
        }}

        function setFilter(filter, btn) {{
            currentFilter = filter;
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            render();
        }}

        function getCleanImage(p) {{
            // Select valid image that is not an ad banner or campaign icon
            const BAD_KEYWORDS = ['vector', 'campaign', 'logo', 'avatar', 'user', 'banner', 'sponsor', 'misc', 'ford', 'mark_your_map'];
            
            if (p.images_b64 && p.images_b64.length > 0) {{
                for (let img of p.images_b64) {{
                    let isBad = false;
                    for (let kw of BAD_KEYWORDS) {{
                        if (img.includes(kw)) {{ isBad = true; break; }}
                    }}
                    if (!isBad) return img;
                }}
                return p.images_b64[0];
            }}
            if (p.image_urls && p.image_urls.length > 0) {{
                for (let img of p.image_urls) {{
                    let isBad = false;
                    for (let kw of BAD_KEYWORDS) {{
                        if (img.includes(kw)) {{ isBad = true; break; }}
                    }}
                    if (!isBad) return img;
                }}
                return p.image_urls[0];
            }}
            return p.thumbnail_url || '';
        }}

        function render() {{
            updateStats();
            const grid = document.getElementById('placesGrid');
            grid.innerHTML = '';

            const filtered = placesData.filter(p => {{
                const st = getStatus(p.slug);
                if (currentFilter === 'interested') return st === 'interested';
                if (currentFilter === 'skipped') return st === 'skip' || st === 'skipped';
                if (currentFilter === 'unreviewed') return st === 'unreviewed';
                return true;
            }});

            if (filtered.length === 0) {{
                grid.innerHTML = '<div class="empty-state"><h2>No places found in this view.</h2><p>Try switching filters or review more places!</p></div>';
                return;
            }}

            filtered.forEach(p => {{
                const st = getStatus(p.slug);
                const isInt = st === 'interested';
                const isSkip = st === 'skip' || st === 'skipped';
                
                const imgSrc = getCleanImage(p);
                const targetUrl = p.url || `https://www.atlasobscura.com/places/${{p.slug}}`;

                const card = document.createElement('div');
                card.className = `card ${{isInt ? 'interested' : ''}} ${{isSkip ? 'skipped' : ''}}`;
                card.innerHTML = `
                    <span class="card-badge interested-badge">⭐ Interested</span>
                    <span class="card-badge skipped-badge">❌ Skipped</span>
                    <a href="${{targetUrl}}" target="_blank" rel="noopener" class="card-img-link" title="Open on Atlas Obscura Online">
                        <img class="card-img" src="${{imgSrc}}" alt="${{p.title}}" onerror="this.src='https://via.placeholder.com/400x200?text=Photo+Unavailable'" />
                    </a>
                    <div class="card-body">
                        <a href="${{targetUrl}}" target="_blank" rel="noopener" class="card-title-link">${{p.title}} ↗</a>
                        <div class="card-subtitle">${{p.subtitle || ''}}</div>
                        <div class="card-location">📍 ${{p.location || 'Unknown'}}</div>
                        <div class="card-coords">LAT: ${{p.lat || 'N/A'}}, LON: ${{p.lon || 'N/A'}}</div>
                        
                        <div class="card-actions">
                            <button class="btn-card btn-interest-card" onclick="setStatus('${{p.slug}}', 'interested')">
                                ${{isInt ? '⭐ Interested' : 'Interested'}}
                            </button>
                            <button class="btn-card btn-skip-card" onclick="setStatus('${{p.slug}}', 'skip')">
                                ${{isSkip ? '❌ Skipped' : 'Skip'}}
                            </button>
                            <a href="${{targetUrl}}" target="_blank" rel="noopener" class="btn-card btn-online-card">
                                🌐 Online ↗
                            </a>
                        </div>
                    </div>
                `;
                grid.appendChild(card);
            }});
        }}

        function exportCSV() {{
            const interestedPlaces = placesData.filter(p => getStatus(p.slug) === 'interested');
            if (interestedPlaces.length === 0) {{
                alert("Please mark at least one place as ⭐ Interested before exporting!");
                return;
            }}

            let csvContent = "Name,Latitude,Longitude,Description,Url,Location\\n";
            interestedPlaces.forEach(p => {{
                const name = `"${{(p.title || '').replace(/"/g, '""')}}"`;
                const lat = p.lat || '';
                const lon = p.lon || '';
                const subtitle = (p.subtitle || '').replace(/"/g, '""');
                const url = p.url || `https://www.atlasobscura.com/places/${{p.slug}}`;
                const loc = (p.location || '').replace(/"/g, '""');
                const desc = `"${{subtitle}} | Location: ${{loc}} | Atlas Obscura: ${{url}}"`;
                
                csvContent += `${{name}},${{lat}},${{lon}},${{desc}},"${{url}}","${{loc}}"\\n`;
            }});

            const blob = new Blob([csvContent], {{ type: 'text/csv;charset=utf-8;' }});
            const url = URL.createObjectURL(blob);
            const link = document.createElement("a");
            link.setAttribute("href", url);
            link.setAttribute("download", `atlas_obscura_${{areaKey}}_interested.csv`);
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }}

        document.addEventListener('DOMContentLoaded', render);
    </script>
</body>
</html>
"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
        
    return output_path
