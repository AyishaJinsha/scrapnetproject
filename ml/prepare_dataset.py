"""
Step 1: Dataset Preparation Script for ScrapNet ML Integration
=====================================================================
Run this script ONCE to:
  1. Generate synthetic vehicle damage images (Low / Medium / High)
  2. Generate synthetic CSV data for scrap price prediction

How to run:
  cd c:\\Users\\ayish\\OneDrive\\Desktop\\scrapnet
  python ml/prepare_dataset.py

Output:
  ml/dataset/images/low/   -> sample "low damage" images
  ml/dataset/images/medium/ -> sample "medium damage" images
  ml/dataset/images/high/   -> sample "high damage" images
  ml/dataset/vehicle_data.csv -> regression dataset
"""

import os
import random
import csv
from PIL import Image, ImageDraw, ImageFilter
import numpy as np

# ─────────────────────────── paths ───────────────────────────
BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
IMG_DIR   = os.path.join(BASE_DIR, "dataset", "images")
CSV_PATH  = os.path.join(BASE_DIR, "dataset", "vehicle_data.csv")

CATEGORIES   = ["low", "medium", "high"]
SAMPLES_EACH = 150          # images per class  (150 × 3 = 450 total)
IMG_SIZE     = (128, 128)   # width × height

random.seed(42)
np.random.seed(42)


# ══════════════════════════════════════════════════════════════
# 1.  SYNTHETIC IMAGE GENERATION
# ══════════════════════════════════════════════════════════════

def _base_car_color(damage_level: str):
    """Return an (R,G,B) base colour that subtly hints at damage severity."""
    if damage_level == "low":
        return (random.randint(180, 220), random.randint(180, 220), random.randint(180, 220))
    elif damage_level == "medium":
        return (random.randint(140, 180), random.randint(110, 150), random.randint(80, 120))
    else:  # high
        return (random.randint(60, 100),  random.randint(40, 80),   random.randint(30, 70))


def generate_damage_image(damage_level: str) -> Image.Image:
    """
    Create a synthetic 128×128 JPEG-style image that visually
    represents a vehicle's damage level.

    • LOW    – few small scratches, mostly clean body colour
    • MEDIUM – multiple dents / rust patches, intermediate tone
    • HIGH   – heavy rust, cracks, dark irregular shapes
    """
    base_color = _base_car_color(damage_level)
    img  = Image.new("RGB", IMG_SIZE, base_color)
    draw = ImageDraw.Draw(img)

    # ── car body silhouette ──────────────────────────────────
    body_rect  = [10, 40, 118, 100]
    roof_rect  = [25, 20, 103, 45]
    body_color = tuple(max(0, c - 20) for c in base_color)
    draw.rectangle(body_rect, fill=body_color, outline=(0, 0, 0))
    draw.rectangle(roof_rect, fill=body_color, outline=(0, 0, 0))

    # ── wheels ───────────────────────────────────────────────
    for cx, cy in [(30, 100), (98, 100)]:
        draw.ellipse([cx - 12, cy - 12, cx + 12, cy + 12],
                     fill=(30, 30, 30), outline=(80, 80, 80))

    # ── damage marks based on level ──────────────────────────
    if damage_level == "low":
        # 2–4 small scratch lines
        for _ in range(random.randint(2, 4)):
            x1 = random.randint(15, 110)
            y1 = random.randint(40, 95)
            x2 = x1 + random.randint(3, 15)
            y2 = y1 + random.randint(1, 5)
            draw.line([x1, y1, x2, y2], fill=(100, 100, 100), width=1)

    elif damage_level == "medium":
        # 4–8 dents (ellipses) + rust patches
        for _ in range(random.randint(4, 8)):
            x = random.randint(15, 105)
            y = random.randint(42, 92)
            w = random.randint(6, 18)
            h = random.randint(4, 12)
            dent_color = (
                random.randint(100, 140),
                random.randint(60, 100),
                random.randint(20, 60),
            )
            draw.ellipse([x, y, x + w, y + h], fill=dent_color)
        # Rust streaks
        for _ in range(random.randint(2, 5)):
            x = random.randint(15, 110)
            y = random.randint(42, 95)
            draw.line([x, y, x + random.randint(8, 25), y + random.randint(2, 8)],
                      fill=(139, 69, 19), width=2)

    else:  # high
        # Many overlapping dark shapes, heavy rust, cracks
        for _ in range(random.randint(10, 18)):
            x = random.randint(10, 105)
            y = random.randint(38, 95)
            w = random.randint(10, 30)
            h = random.randint(8, 20)
            rust = (random.randint(80, 130), random.randint(20, 60), 0)
            draw.ellipse([x, y, x + w, y + h], fill=rust)
        # Crack lines
        for _ in range(random.randint(5, 10)):
            x = random.randint(12, 108)
            y = random.randint(40, 96)
            draw.line(
                [x, y, x + random.randint(-15, 15), y + random.randint(-10, 10)],
                fill=(10, 10, 10), width=random.randint(1, 2),
            )
        # Noise overlay
        arr   = np.array(img)
        noise = np.random.randint(-30, 30, arr.shape, dtype=np.int16)
        arr   = np.clip(arr.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        img   = Image.fromarray(arr)
        draw  = ImageDraw.Draw(img)          # re-bind after array round-trip

    # Slight blur to look more realistic
    img = img.filter(ImageFilter.GaussianBlur(radius=0.5))
    return img


def create_image_dataset():
    print("\n📸  Generating synthetic vehicle images …")
    for label in CATEGORIES:
        folder = os.path.join(IMG_DIR, label)
        os.makedirs(folder, exist_ok=True)
        for i in range(SAMPLES_EACH):
            img  = generate_damage_image(label)
            path = os.path.join(folder, f"{label}_{i:04d}.jpg")
            img.save(path, "JPEG", quality=90)
        print(f"   ✅  {SAMPLES_EACH} '{label}' images  →  {folder}")
    print(f"   Total images: {SAMPLES_EACH * len(CATEGORIES)}")


# ══════════════════════════════════════════════════════════════
# 2.  SYNTHETIC REGRESSION CSV
# ══════════════════════════════════════════════════════════════

VEHICLE_TYPES = ["Sedan", "SUV", "Truck", "Motorcycle", "Van"]

DAMAGE_BASE = {
    "Low":    1.0,
    "Medium": 0.65,
    "High":   0.30,
}

TYPE_MULT = {
    "Sedan":      1.0,
    "SUV":        1.4,
    "Truck":      1.8,
    "Motorcycle": 0.5,
    "Van":        1.2,
}


def compute_price(age, mileage, vehicle_type, damage_level) -> float:
    """
    Deterministic (but realistic) pricing formula.

    Base price  = ₹50,000  (scrap iron/metal base)
    Age factor  = depreciates 5 % per year  (min 20 %)
    Mileage fac = depreciates 0.002 % per 1,000 km  (min 60 %)
    Type mult   = reflects vehicle weight / metal content
    Damage mult = how much usable metal remains
    Noise       = ±5 % random variation
    """
    base        = 50_000
    age_factor  = max(0.20, 1 - 0.05 * age)
    mil_factor  = max(0.60, 1 - 0.00002 * mileage)
    type_mult   = TYPE_MULT.get(vehicle_type, 1.0)
    dmg_mult    = DAMAGE_BASE.get(damage_level, 1.0)
    noise       = random.uniform(0.95, 1.05)

    price = base * age_factor * mil_factor * type_mult * dmg_mult * noise
    return round(price, 2)


def create_regression_dataset(n_samples: int = 1000):
    os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
    print(f"\n📊  Generating regression dataset ({n_samples} rows) …")

    rows = []
    damage_levels = list(DAMAGE_BASE.keys())

    for _ in range(n_samples):
        age          = random.randint(1, 25)
        mileage      = random.randint(5_000, 300_000)
        vehicle_type = random.choice(VEHICLE_TYPES)
        damage_level = random.choice(damage_levels)
        price        = compute_price(age, mileage, vehicle_type, damage_level)

        rows.append({
            "age":          age,
            "mileage":      mileage,
            "vehicle_type": vehicle_type,
            "damage_level": damage_level,
            "scrap_price":  price,
        })

    with open(CSV_PATH, "w", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["age", "mileage", "vehicle_type", "damage_level", "scrap_price"]
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"   ✅  CSV saved  →  {CSV_PATH}")
    print(f"   Sample row: {rows[0]}")


# ══════════════════════════════════════════════════════════════
# 3.  MAIN
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("  ScrapNet – Dataset Preparation (Step 1 of ML Pipeline)")
    print("=" * 60)

    create_image_dataset()
    create_regression_dataset(n_samples=1000)

    print("\n" + "=" * 60)
    print("  ✅  Dataset preparation complete!")
    print(f"  Images : {IMG_DIR}")
    print(f"  CSV    : {CSV_PATH}")
    print("\n  Next step → run:  python ml/train_models.py")
    print("=" * 60)
