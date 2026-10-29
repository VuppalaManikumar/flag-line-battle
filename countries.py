import os
import urllib.request
from PIL import Image, ImageDraw

# Comprehensive list of popular countries for battles
# Each country has: name, iso code (for FlagCDN), neon laser color (HEX and RGB), and text color
COUNTRY_DATABASE = {
    "Germany": {
        "code": "de",
        "laser_color": (255, 60, 180),    # Neon Magenta/Pink (as seen in screenshot)
        "hex": "#FF3CB4",
        "bg_color": (255, 204, 0)
    },
    "Austria": {
        "code": "at",
        "laser_color": (255, 50, 50),     # Bright Crimson Red (as in screenshot)
        "hex": "#FF3232",
        "bg_color": (237, 41, 57)
    },
    "Ireland": {
        "code": "ie",
        "laser_color": (0, 255, 128),     # Neon Emerald Green (as in screenshot)
        "hex": "#00FF80",
        "bg_color": (22, 155, 98)
    },
    "Netherlands": {
        "code": "nl",
        "laser_color": (255, 130, 0),     # Neon Orange
        "hex": "#FF8200",
        "bg_color": (255, 102, 0)
    },
    "Greece": {
        "code": "gr",
        "laser_color": (0, 200, 255),     # Electric Sky Blue
        "hex": "#00C8FF",
        "bg_color": (13, 94, 175)
    },
    "France": {
        "code": "fr",
        "laser_color": (60, 140, 255),    # Vibrant Royal Blue
        "hex": "#3C8CFF",
        "bg_color": (0, 85, 164)
    },
    "Brazil": {
        "code": "br",
        "laser_color": (50, 255, 50),     # Neon Lime Green
        "hex": "#32FF32",
        "bg_color": (0, 156, 59)
    },
    "Argentina": {
        "code": "ar",
        "laser_color": (100, 210, 255),   # Ice Blue
        "hex": "#64D2FF",
        "bg_color": (116, 172, 223)
    },
    "United States": {
        "code": "us",
        "laser_color": (255, 70, 70),     # Neon Red
        "hex": "#FF4646",
        "bg_color": (179, 25, 66)
    },
    "United Kingdom": {
        "code": "gb",
        "laser_color": (130, 110, 255),   # Royal Violet
        "hex": "#826EFF",
        "bg_color": (1, 33, 105)
    },
    "Japan": {
        "code": "jp",
        "laser_color": (255, 40, 100),    # Neon Hot Coral / Crimson
        "hex": "#FF2864",
        "bg_color": (188, 0, 45)
    },
    "South Korea": {
        "code": "kr",
        "laser_color": (0, 225, 255),     # Electric Cyan
        "hex": "#00E1FF",
        "bg_color": (205, 46, 58)
    },
    "India": {
        "code": "in",
        "laser_color": (255, 150, 20),    # Vibrant Saffron
        "hex": "#FF9614",
        "bg_color": (255, 153, 51)
    },
    "Canada": {
        "code": "ca",
        "laser_color": (255, 65, 65),     # Maple Red
        "hex": "#FF4141",
        "bg_color": (255, 0, 0)
    },
    "Italy": {
        "code": "it",
        "laser_color": (0, 230, 115),     # Italian Green
        "hex": "#00E673",
        "bg_color": (0, 146, 70)
    },
    "Spain": {
        "code": "es",
        "laser_color": (255, 200, 0),     # Golden Amber
        "hex": "#FFC800",
        "bg_color": (170, 21, 27)
    },
    "Portugal": {
        "code": "pt",
        "laser_color": (0, 220, 100),     # Lusitanian Green
        "hex": "#00DC64",
        "bg_color": (4, 106, 56)
    },
    "Sweden": {
        "code": "se",
        "laser_color": (255, 215, 0),     # Nordic Gold
        "hex": "#FFD700",
        "bg_color": (0, 106, 167)
    },
    "Norway": {
        "code": "no",
        "laser_color": (255, 60, 60),     # Viking Red
        "hex": "#FF3C3C",
        "bg_color": (186, 12, 47)
    },
    "Denmark": {
        "code": "dk",
        "laser_color": (255, 75, 75),     # Danish Red
        "hex": "#FF4B4B",
        "bg_color": (200, 16, 46)
    },
    "Finland": {
        "code": "fi",
        "laser_color": (80, 160, 255),    # Nordic Ice Blue
        "hex": "#50A0FF",
        "bg_color": (0, 47, 108)
    },
    "Switzerland": {
        "code": "ch",
        "laser_color": (255, 50, 50),     # Swiss Bright Red
        "hex": "#FF3232",
        "bg_color": (218, 41, 28)
    },
    "Belgium": {
        "code": "be",
        "laser_color": (255, 190, 0),     # Brussels Gold
        "hex": "#FFBE00",
        "bg_color": (253, 218, 36)
    },
    "Poland": {
        "code": "pl",
        "laser_color": (255, 80, 120),    # Warsaw Rose Red
        "hex": "#FF5078",
        "bg_color": (220, 20, 60)
    },
    "Australia": {
        "code": "au",
        "laser_color": (255, 195, 0),     # Aussie Gold
        "hex": "#FFC300",
        "bg_color": (0, 0, 139)
    },
    "Mexico": {
        "code": "mx",
        "laser_color": (0, 230, 90),      # Aztec Green
        "hex": "#00E65A",
        "bg_color": (0, 104, 71)
    },
    "Turkey": {
        "code": "tr",
        "laser_color": (255, 45, 60),     # Anatolian Red
        "hex": "#FF2D3C",
        "bg_color": (227, 10, 23)
    },
    "Egypt": {
        "code": "eg",
        "laser_color": (230, 180, 50),    # Pyramid Gold
        "hex": "#E6B432",
        "bg_color": (192, 147, 43)
    },
    "South Africa": {
        "code": "za",
        "laser_color": (0, 220, 150),     # Rainbow Teal
        "hex": "#00DC96",
        "bg_color": (0, 122, 54)
    },
    "Morocco": {
        "code": "ma",
        "laser_color": (255, 50, 70),     # Atlas Crimson
        "hex": "#FF3246",
        "bg_color": (193, 39, 45)
    }
}

FLAGS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "flags")

def get_flag_path(country_name: str) -> str:
    """Returns local path to cached circular flag PNG, downloading if needed."""
    os.makedirs(FLAGS_DIR, exist_ok=True)
    clean_name = country_name.replace(" ", "_").lower()
    circular_path = os.path.join(FLAGS_DIR, f"{clean_name}_circle.png")
    
    if os.path.exists(circular_path):
        return circular_path
        
    info = COUNTRY_DATABASE.get(country_name)
    if not info:
        # Fallback to Germany if unknown
        info = COUNTRY_DATABASE["Germany"]
        
    raw_path = os.path.join(FLAGS_DIR, f"{clean_name}_raw.png")
    if not os.path.exists(raw_path):
        url = f"https://flagcdn.com/w320/{info['code']}.png"
        try:
            req = urllib.request.Request(
                url, 
                headers={'User-Agent': 'Mozilla/5.0 (FlagBattleVideoBot/1.0)'}
            )
            with urllib.request.urlopen(req, timeout=10) as response, open(raw_path, 'wb') as out_file:
                out_file.write(response.read())
        except Exception as e:
            print(f"Error downloading flag for {country_name}: {e}")
            # Create a simple fallback striped image
            img = Image.new("RGBA", (320, 213), info.get("bg_color", (100, 100, 100)))
            img.save(raw_path)

    # Process into anti-aliased circular disc
    try:
        raw_img = Image.open(raw_path).convert("RGBA")
        
        # Target size for high-res circular flag icon
        size = 256
        # Crop square from center of the flag
        w, h = raw_img.size
        min_dim = min(w, h)
        left = (w - min_dim) // 2
        top = (h - min_dim) // 2
        square_img = raw_img.crop((left, top, left + min_dim, top + min_dim))
        square_img = square_img.resize((size, size), Image.Resampling.LANCZOS)
        
        # High resolution circular mask with soft anti-aliased edge
        mask = Image.new("L", (size * 2, size * 2), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((4, 4, size * 2 - 5, size * 2 - 5), fill=255)
        mask = mask.resize((size, size), Image.Resampling.LANCZOS)
        
        circular_img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        circular_img.paste(square_img, (0, 0), mask=mask)
        
        # Add subtle inner border / rim
        rim_draw = ImageDraw.Draw(circular_img)
        rim_color = (255, 255, 255, 200)
        rim_draw.ellipse((2, 2, size - 3, size - 3), outline=rim_color, width=4)
        
        circular_img.save(circular_path, "PNG")
        return circular_path
    except Exception as e:
        print(f"Error processing circular flag: {e}")
        return raw_path

def preload_countries(country_list=None):
    """Pre-downloads flags for the requested or all top countries."""
    targets = country_list if country_list else list(COUNTRY_DATABASE.keys())
    print(f"Preloading flags for {len(targets)} countries...")
    for c in targets:
        get_flag_path(c)
    print("Preload complete!")

if __name__ == "__main__":
    # Test preload of the 4 from user screenshot
    preload_countries(["Germany", "Austria", "Ireland", "Netherlands", "Greece"])
