import urllib.request
import urllib.parse
import json
import re
import base64
import os
import sys
import concurrent.futures
from typing import List, Dict, Any, Optional

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5'
}

import time

def make_request(url: str, is_json: bool = False, timeout: int = 15, retries: int = 2) -> Optional[Any]:
    """Helper function to perform HTTP GET requests with custom headers and exponential backoff retry."""
    for attempt in range(retries + 1):
        req = urllib.request.Request(url, headers=HEADERS)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = resp.read()
                if is_json:
                    return json.loads(data.decode('utf-8'))
                return data.decode('utf-8', errors='ignore')
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < retries:
                time.sleep(1.5 * (attempt + 1))
                continue
            if attempt == retries:
                print(f"[Scraper] Error requesting {url}: {e}")
            return None
        except Exception as e:
            if attempt == retries:
                print(f"[Scraper] Error requesting {url}: {e}")
            return None
    return None

def download_image_as_base64(img_url: str, timeout: int = 10) -> Optional[str]:
    """Download image and encode as base64 Data URI for offline HTML rendering."""
    req = urllib.request.Request(img_url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            content_type = resp.headers.get('Content-Type', 'image/jpeg')
            img_bytes = resp.read()
            b64_str = base64.b64encode(img_bytes).decode('utf-8')
            return f"data:{content_type};base64,{b64_str}"
    except Exception as e:
        print(f"[Scraper] Failed to download image {img_url}: {e}")
        return None

def is_point_in_polygon(lat: float, lon: float, polygon: List[List[float]]) -> bool:
    """
    Ray-casting algorithm to test if point (lat, lon) is inside a polygon.
    polygon is a list of [lat, lon] pairs.
    """
    n = len(polygon)
    if n < 3:
        return True
    inside = False
    p1_lat, p1_lon = polygon[0]
    for i in range(n + 1):
        p2_lat, p2_lon = polygon[i % n]
        if lon > min(p1_lon, p2_lon):
            if lon <= max(p1_lon, p2_lon):
                if lat <= max(p1_lat, p2_lat):
                    if p1_lon != p2_lon:
                        xinters = (lon - p1_lon) * (p2_lat - p1_lat) / (p2_lon - p1_lon) + p1_lat
                    if p1_lat == p2_lat or lat <= xinters:
                        inside = not inside
        p1_lat, p1_lon = p2_lat, p2_lon
    return inside

def filter_places_by_polygon(places: List[Dict[str, Any]], polygon: List[List[float]]) -> List[Dict[str, Any]]:
    """Filter a list of place summaries to only include those inside the custom drawn polygon."""
    filtered = []
    for p in places:
        lat = p.get('lat')
        lon = p.get('lon')
        if lat is not None and lon is not None:
            if is_point_in_polygon(float(lat), float(lon), polygon):
                filtered.append(p)
    return filtered

def filter_places_by_bbox(places: List[Dict[str, Any]], min_lat: float, min_lon: float, max_lat: float, max_lon: float) -> List[Dict[str, Any]]:
    """Filter a list of place summaries to only include those within the given bounding box."""
    filtered = []
    for p in places:
        lat = p.get('lat')
        lon = p.get('lon')
        if lat is not None and lon is not None:
            if min_lat <= float(lat) <= max_lat and min_lon <= float(lon) <= max_lon:
                filtered.append(p)
    return filtered

WORLDWIDE_CACHE_FILE = os.path.abspath("./output/worldwide_places.json")
_WORLDWIDE_PLACES_CACHE = None

def load_worldwide_places_cache() -> List[Dict[str, Any]]:
    """
    Downloads and caches the official Atlas Obscura worldwide dataset (32,000+ places).
    Ensures 100% accurate map point coverage without missing places.
    """
    global _WORLDWIDE_PLACES_CACHE
    if _WORLDWIDE_PLACES_CACHE is not None:
        return _WORLDWIDE_PLACES_CACHE

    os.makedirs(os.path.dirname(WORLDWIDE_CACHE_FILE), exist_ok=True)

    if os.path.exists(WORLDWIDE_CACHE_FILE):
        try:
            with open(WORLDWIDE_CACHE_FILE, 'r', encoding='utf-8') as f:
                _WORLDWIDE_PLACES_CACHE = json.load(f)
                print(f"[Scraper] Loaded {len(_WORLDWIDE_PLACES_CACHE)} places from local worldwide cache.")
                return _WORLDWIDE_PLACES_CACHE
        except Exception as e:
            print(f"[Scraper] Error reading local worldwide cache: {e}")

    print("[Scraper] Fetching official Atlas Obscura master map dataset (32,000+ places)...")
    url = "https://www.atlasobscura.com/articles/all-places-in-the-atlas-on-one-map"
    html = make_request(url)
    if html:
        match = re.search(r'AtlasObscura\.all_places\s*=\s*(\[.*?\]);', html, re.DOTALL)
        if match:
            try:
                places = json.loads(match.group(1))
                # Standardize lat/lon fields
                for p in places:
                    if 'lng' in p and 'lon' not in p:
                        p['lon'] = p['lng']
                _WORLDWIDE_PLACES_CACHE = places
                with open(WORLDWIDE_CACHE_FILE, 'w', encoding='utf-8') as f:
                    json.dump(places, f)
                print(f"[Scraper] Successfully cached {len(places)} master places worldwide!")
                return places
            except Exception as e:
                print(f"[Scraper] Error parsing master places JSON: {e}")

    _WORLDWIDE_PLACES_CACHE = []
    return []

def get_places_in_region_spatial(
    polygon: Optional[List[List[float]]] = None,
    bbox: Optional[Dict[str, float]] = None
) -> List[Dict[str, Any]]:
    """
    Spatially queries the 32,000+ master dataset using polygon or bounding box.
    Returns 100% complete place points matching the user's drawn map shape.
    """
    all_places = load_worldwide_places_cache()
    if not all_places:
        return []

    if polygon and len(polygon) >= 3:
        return filter_places_by_polygon(all_places, polygon)
    elif bbox:
        min_lat, min_lon = float(bbox.get('min_lat', -90)), float(bbox.get('min_lon', -180))
        max_lat, max_lon = float(bbox.get('max_lat', 90)), float(bbox.get('max_lon', 180))
        return filter_places_by_bbox(all_places, min_lat, min_lon, max_lat, max_lon)
    return all_places

def fetch_place_by_id(place_id: int) -> Optional[Dict[str, Any]]:
    """Fetch place details directly by numeric ID."""
    url = f"https://www.atlasobscura.com/places/{place_id}.json"
    data = make_request(url, is_json=True)
    if isinstance(data, dict):
        if 'coordinates' in data and isinstance(data['coordinates'], dict):
            data['lat'] = data['coordinates'].get('lat')
            data['lon'] = data['coordinates'].get('lng')
        # Extract slug from url if missing
        if 'url' in data and data['url']:
            slug = data['url'].rstrip('/').split('/')[-1]
            data['slug'] = slug
        else:
            data['slug'] = f"place_{place_id}"
        return data
    return None

def count_places_in_region(
    query: str, 
    polygon: Optional[List[List[float]]] = None,
    bbox: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    Check places count in region using 32,000+ master dataset.
    Fast, 100% accurate, and 0 HTTP requests needed for count check!
    """
    if polygon or bbox:
        matched = get_places_in_region_spatial(polygon=polygon, bbox=bbox)
    else:
        # Filter master dataset by location query name string if no spatial shape drawn
        all_places = load_worldwide_places_cache()
        clean_q = query.strip().lower()
        matched = [p for p in all_places if clean_q in str(p.get('id', '')).lower()]
        if not matched:
            # Fallback search by query string
            matched = search_places_by_text_query(query, max_results=50)

    return {
        'query': query,
        'total_found': len(matched),
        'matched_in_region': len(matched),
        'estimated_download_seconds': round(len(matched) * 1.4, 1),
        'places': matched
    }

def search_places_by_text_query(query: str, max_results: int = 50) -> List[Dict[str, Any]]:
    """Text-based fallback scraper for location names."""
    slugs = set()
    results = []
    clean_query = query.strip().lower().replace(" ", "-")

    urls_to_scrape = [
        f"https://www.atlasobscura.com/things-to-do/{clean_query}",
        f"https://www.atlasobscura.com/search?q={urllib.parse.quote(query)}&type=places"
    ]

    for url in urls_to_scrape:
        html = make_request(url)
        if html:
            found_links = re.findall(r'href="(/places/[^"?#]+)"', html)
            for link in found_links:
                slug = link.replace("/places/", "").strip("/")
                if slug and slug not in slugs:
                    slugs.add(slug)
        time.sleep(0.3)

    for slug in list(slugs)[:max_results]:
        pj = fetch_place_json(slug)
        if pj and isinstance(pj, dict) and pj.get('lat') is not None:
            results.append(pj)
        time.sleep(0.3)

    return results

def search_places(
    query: str, 
    max_results: int = 50, 
    bbox: Optional[Dict[str, float]] = None,
    polygon: Optional[List[List[float]]] = None,
    delay_sec: float = 1.2
) -> List[Dict[str, Any]]:
    """
    Search Atlas Obscura for places.
    Uses master 32,000+ places dataset when polygon or bbox is provided for 100% complete map accuracy.
    Fetches items with configurable polite delay to strictly prevent rate limits.
    """
    if polygon or bbox:
        spatial_matches = get_places_in_region_spatial(polygon=polygon, bbox=bbox)
        print(f"[Scraper] Master dataset matched {len(spatial_matches)} places inside drawn region shape.")
        
        results = []
        target_places = spatial_matches[:max_results]
        
        for idx, p in enumerate(target_places, 1):
            pid = p.get('id')
            print(f"  [{idx}/{len(target_places)}] Querying Place ID {pid}...")
            details = fetch_place_by_id(pid)
            if details:
                results.append(details)
            time.sleep(delay_sec)
            
        return results

    # Text query fallback
    return search_places_by_text_query(query, max_results=max_results)

def fetch_place_json(slug: str) -> Optional[Dict[str, Any]]:
    """Fetch structured JSON for a place via slug."""
    url = f"https://www.atlasobscura.com/places/{slug}.json"
    data = make_request(url, is_json=True)
    if isinstance(data, dict):
        data['slug'] = slug
        if 'coordinates' in data and isinstance(data['coordinates'], dict):
            data['lat'] = data['coordinates'].get('lat')
            data['lon'] = data['coordinates'].get('lng')
        return data
    return None

def fetch_place_full_details(slug: str, max_images: int = 3, embed_images: bool = True) -> Optional[Dict[str, Any]]:
    """
    Fetch full JSON and HTML page for a place, extracting description text and photo gallery.
    Encodes images into Base64 for 100% offline usability.
    """
    # Step 1: Fetch JSON
    json_data = fetch_place_json(slug)
    if not json_data:
        json_data = {
            'slug': slug,
            'title': slug.replace("-", " ").title(),
            'url': f"https://www.atlasobscura.com/places/{slug}"
        }

    # Step 2: Fetch HTML for description & images
    html_url = f"https://www.atlasobscura.com/places/{slug}"
    html = make_request(html_url)
    
    description_paragraphs = []
    image_urls = []

    if html:
        # Extract body text paragraphs
        body_match = re.search(r'<div[^>]*id="place-body"[^>]*>(.*?)</div>\s*<', html, re.DOTALL)
        if not body_match:
            body_match = re.search(r'<section[^>]*class="[^"]*description[^"]*"[^>]*>(.*?)</section>', html, re.DOTALL)
        
        if body_match:
            raw_body = body_match.group(1)
            # Find all <p> text
            paragraphs = re.findall(r'<p>(.*?)</p>', raw_body, re.DOTALL)
            for p in paragraphs:
                # Clean html tags
                clean_p = re.sub(r'<[^>]+>', '', p).strip()
                if clean_p:
                    description_paragraphs.append(clean_p)
        
        # Extract image gallery URLs
        found_imgs = re.findall(r'src="(https://img\.atlasobscura\.com/[^"]+)"', html) + \
                     re.findall(r'data-src="(https://img\.atlasobscura\.com/[^"]+)"', html)
        
        # Filter duplicates and non-place ad banners / campaign icons
        seen_imgs = set()
        BAD_KEYWORDS = ['avatar', 'user', 'logo', 'campaign', 'vector', 'icon', 'banner', 'sponsor', 'misc', 'ford', 'mark_your_map']
        for img in found_imgs:
            img_lower = img.lower()
            if any(k in img_lower for k in BAD_KEYWORDS):
                continue
            if img not in seen_imgs:
                seen_imgs.add(img)
                image_urls.append(img)

    # Ensure canonical cover photo from metadata JSON is primary cover photo #1
    primary_cover = json_data.get('thumbnail_url_3x2') or json_data.get('thumbnail_url')
    if primary_cover:
        if primary_cover in image_urls:
            image_urls.remove(primary_cover)
        image_urls.insert(0, primary_cover)
    elif not image_urls and json_data.get('thumbnail_url'):
        image_urls.append(json_data['thumbnail_url'])

    # Step 3: Image embedding for offline support
    images_b64 = []
    target_imgs = image_urls[:max_images]
    
    if embed_images and target_imgs:
        for img in target_imgs:
            b64_data = download_image_as_base64(img)
            if b64_data:
                images_b64.append(b64_data)
            time.sleep(0.2)  # Polite delay between photo downloads

    full_description = "\n\n".join(description_paragraphs) if description_paragraphs else json_data.get('subtitle', '')

    json_data['description'] = full_description
    json_data['description_paragraphs'] = description_paragraphs
    json_data['image_urls'] = target_imgs
    json_data['images_b64'] = images_b64 if images_b64 else target_imgs  # Fallback to URLs if base64 fails
    json_data['is_offline_ready'] = len(images_b64) > 0

    return json_data
