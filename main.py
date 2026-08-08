import argparse
import os
import sys
import json

# Ensure UTF-8 printing on Windows console
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from atlas_scraper import search_places, fetch_place_full_details
from html_builder import generate_single_place_html, generate_master_offline_viewer
from csv_exporter import export_places_to_csv

def run_search_and_build(
    query: str, 
    max_places: int = 15, 
    output_dir: str = "./output", 
    bbox: Optional[Dict[str, float]] = None,
    polygon: Optional[List[List[float]]] = None
):
    """
    Search for places in an area, download full details and images for offline use,
    generate master offline viewer + individual place cards, and export CSV.
    """
    print(f"\n==================================================")
    print(f"🧭 Atlas Obscura Offline Explorer")
    print(f"Searching area/location: '{query}'")
    if polygon:
        print(f"Polygon Filter: {len(polygon)} vertices")
    elif bbox:
        print(f"Bounding Box Filter: Lat [{bbox['min_lat']} to {bbox['max_lat']}], Lon [{bbox['min_lon']} to {bbox['max_lon']}]")
    print(f"==================================================\n")
    
    os.makedirs(output_dir, exist_ok=True)
    cards_dir = os.path.join(output_dir, "cards")
    os.makedirs(cards_dir, exist_ok=True)

    # 1. Search places with optional bbox/polygon
    place_summaries = search_places(query, max_results=max_places, bbox=bbox, polygon=polygon)
    if not place_summaries:
        print(f"❌ No places found for '{query}' matching specified bounds.")
        return

    print(f"📥 Downloading full offline details and photos for {len(place_summaries)} places...")

    full_places = []
    for idx, place in enumerate(place_summaries, 1):
        slug = place.get('slug')
        title = place.get('title', slug)
        print(f"  [{idx}/{len(place_summaries)}] Fetching: {title} ({slug})")
        
        full_detail = fetch_place_full_details(slug, max_images=3, embed_images=True)
        if full_detail:
            full_places.append(full_detail)
            # Generate standalone card HTML
            card_filename = os.path.join(cards_dir, f"{slug}.html")
            generate_single_place_html(full_detail, card_filename)

    # Save collection JSON data locally
    json_path = os.path.join(output_dir, f"{query.lower().replace(' ', '_')}_places.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(full_places, f, indent=2)

    # Generate master offline viewer HTML
    master_html_path = os.path.join(output_dir, f"offline_viewer_{query.lower().replace(' ', '_')}.html")
    generate_master_offline_viewer(full_places, query, master_html_path)

    # Initial export of all fetched places to CSV
    csv_path = os.path.join(output_dir, f"google_my_maps_{query.lower().replace(' ', '_')}.csv")
    export_places_to_csv(full_places, csv_path)

    print(f"\n==================================================")
    print(f"✅ Success! Offline bundle created.")
    print(f"  📄 Master Offline Viewer: {os.path.abspath(master_html_path)}")
    print(f"  🗂️  Standalone Place Cards: {os.path.abspath(cards_dir)}")
    print(f"  🗺️  Google My Maps CSV: {os.path.abspath(csv_path)}")
    print(f"==================================================\n")

def main():
    parser = argparse.ArgumentParser(description="Atlas Obscura Offline Explorer & Google My Maps CSV Exporter")
    subparsers = parser.add_subparsers(dest="command")

    search_parser = subparsers.add_parser("search", help="Search location/area and build offline bundle")
    search_parser.add_argument("query", help="Location or area query (e.g. Latvia, Paris, Riga)")
    search_parser.add_argument("--max", type=int, default=15, help="Maximum number of places to download")
    search_parser.add_argument("--output", default="./output", help="Directory to save offline files")
    search_parser.add_argument("--bbox", help="Bounding box as 'min_lat,min_lon,max_lat,max_lon' (e.g. 56.5,23.5,57.5,25.5)")

    args = parser.parse_args()

    if args.command == "search":
        bbox_dict = None
        if args.bbox:
            parts = [float(x.strip()) for x in args.bbox.split(',')]
            if len(parts) == 4:
                bbox_dict = {
                    'min_lat': parts[0],
                    'min_lon': parts[1],
                    'max_lat': parts[2],
                    'max_lon': parts[3]
                }
        run_search_and_build(args.query, max_places=args.max, output_dir=args.output, bbox=bbox_dict)
    else:
        # Default interactive run if no subcommand specified
        query = input("Enter location/area to explore on Atlas Obscura (e.g., 'Latvia'): ").strip()
        if query:
            run_search_and_build(query, max_places=10)

if __name__ == "__main__":
    main()
