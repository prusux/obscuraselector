# Obscura Selector 🧭

**Obscura Selector** is an offline explorer, spatial polygon region scraper, and Google My Maps exporter for **Atlas Obscura** destinations.

It allows travelers to search destinations, visually select trip areas on an interactive map using custom polygon shapes or bounding boxes, download 100% offline self-contained HTML cards with embedded photo galleries, interactively review places (Mark Interested / Skip), and export selected places directly to a `.csv` file ready for import into **Google My Maps**.

---

## 🌟 Key Features

- 🌍 **Master 32,000+ Worldwide Dataset**: Instant, 100% accurate spatial filtering against Atlas Obscura's master map database of 32,015 places worldwide.
- 🔷 **Interactive Polygon & Bounding Box Selector**: Draw custom multi-point polygons or rectangles directly on an interactive Leaflet map to isolate your trip itinerary.
- 🛡️ **Polite & Safe Scraping Engine**: Includes configurable request delays (`1.2s` polite default, `1.8s` ultra-safe mode) with rate-limit protection.
- 📄 **100% Offline HTML Cards & Collection Dashboard**: Downloads place descriptions and Base64-embedded cover photos for complete usability in remote areas without internet coverage.
- 🗺️ **Google My Maps CSV Exporter**: Generates a properly formatted CSV (`Name, Latitude, Longitude, Description, Url, Location`) for 1-click import into custom Google My Maps layers.
- 💻 **Zero Dependencies (Python Standard Library)**: Runs out-of-the-box using standard Python 3. No external `pip` packages required.
- 🚀 **Windows Batch Launchers**: One-click double-clickable `run_explorer.bat` to launch the server and open the Web UI automatically.

---

## 🛠️ Project Architecture

```
obscuraselector/
├── atlas_scraper.py      # Core scraper & 32,000+ worldwide places spatial query engine
├── html_builder.py       # Offline HTML card & interactive master dashboard builder
├── csv_exporter.py       # Google My Maps CSV export formatter
├── server.py             # Web application server (Python http.server) & Leaflet Draw UI
├── main.py               # CLI entry point for command-line search & export
├── run_explorer.bat      # Windows 1-click launcher for Web Explorer UI
├── run_cli.bat           # Windows 1-click launcher for CLI mode
└── README.md
```

---

## 🚀 Usage Guide

### Option 1: Web UI (Recommended)

1. Double-click **`run_explorer.bat`** (or run `python server.py`).
2. Open **`http://localhost:8000`** in your web browser.
3. Type a destination (e.g. `Spain`, `France`, `Latvia`).
4. *(Optional)* Click **"🔷 Draw Polygon"** or **"⬛ Draw Rectangle"** on the map to define your trip area.
5. Click **"🔍 1. Check Count in Area"** to preview matching places.
6. Click **"📥 2. Download Offline Bundle"** to download your offline collection!

### Option 2: Command Line (CLI)

```bash
# Basic region search
python main.py search "Spain" --max 30

# Search using Bounding Box (min_lat, min_lon, max_lat, max_lon)
python main.py search "Latvia" --bbox 56.9,24.0,57.1,24.3 --max 15
```

---

## 🗺️ Importing into Google My Maps

1. Go to [Google My Maps](https://www.google.com/maps/d/).
2. Create a **New Map** and click **Import** under a layer.
3. Select your exported `.csv` file (e.g., `google_my_maps_spain.csv`).
4. Choose **Latitude** and **Longitude** for place placement columns, and **Name** for pin titles.
5. All your interested Atlas Obscura places will now appear as custom pins on your map!

---

## 📄 License

MIT License. Designed for personal travel planning and offline research.
