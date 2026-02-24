"""
ScrapNet – ML Model Loader & Predictor  (ml_model.py)
=====================================================================
• Loaded ONCE at Django startup (module-level singletons).
• Provides two public functions:
    predict_damage(image_path)  →  "Low" | "Medium" | "High"
    predict_price(age, mileage, vehicle_type, damage_level)  →  float (₹)

• Falls back to rule-based predictions when models are not yet trained.
"""

import os
import pickle
import logging

try:
    import numpy as np
    from PIL import Image
    _DEPS_AVAILABLE = True
except ImportError:
    _DEPS_AVAILABLE = False

logger = logging.getLogger(__name__)

# ─────────────────────────── paths ───────────────────────────
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_ML_DIR   = os.path.join(_BASE_DIR, "ml", "models")

DAMAGE_MODEL_PATH = os.path.join(_ML_DIR, "damage_model.h5")
PRICE_MODEL_PATH  = os.path.join(_ML_DIR, "price_model.pkl")
ENCODER_PATH      = os.path.join(_ML_DIR, "label_encoders.pkl")

IMG_SIZE = (128, 128)
CLASSES  = ["Low", "Medium", "High"]   # must match training order

# ─────────────────────────── singletons ──────────────────────
_damage_model  = None
_price_model   = None
_encoders      = None
_tf_available  = False


def _load_models():
    """Load models once; called lazily on first prediction request."""
    global _damage_model, _price_model, _encoders, _tf_available

    # ── CNN ───────────────────────────────────────────────────
    if os.path.exists(DAMAGE_MODEL_PATH):
        try:
            import tensorflow as tf
            _damage_model = tf.keras.models.load_model(DAMAGE_MODEL_PATH)
            _tf_available = True
            logger.info("✅ Damage CNN loaded from %s", DAMAGE_MODEL_PATH)
        except Exception as e:
            logger.warning("❌ Could not load damage model: %s", e)
    else:
        logger.warning("⚠️ Damage model not found at %s – using rule-based fallback", DAMAGE_MODEL_PATH)

    # ── Price RF ──────────────────────────────────────────────
    if os.path.exists(PRICE_MODEL_PATH):
        try:
            with open(PRICE_MODEL_PATH, "rb") as f:
                _price_model = pickle.load(f)
            logger.info("✅ Price model loaded from %s", PRICE_MODEL_PATH)
        except Exception as e:
            logger.warning("❌ Could not load price model: %s", e)
    else:
        logger.warning("⚠️ Price model not found at %s – using formula fallback", PRICE_MODEL_PATH)

    # ── Encoders ──────────────────────────────────────────────
    if os.path.exists(ENCODER_PATH):
        try:
            with open(ENCODER_PATH, "rb") as f:
                _encoders = pickle.load(f)
            logger.info("✅ Label encoders loaded")
        except Exception as e:
            logger.warning("❌ Could not load encoders: %s", e)


# Load at import time (Django startup)
_load_models()


# ══════════════════════════════════════════════════════════════
# PUBLIC API
# ══════════════════════════════════════════════════════════════

def predict_damage(image_path: str) -> str:
    """
    Predict damage level from a vehicle image file.

    Parameters
    ----------
    image_path : absolute path to the image

    Returns
    -------
    str  – one of  "Low" | "Medium" | "High"
    """
    if _damage_model is not None and _tf_available:
        try:
            img   = Image.open(image_path).convert("RGB").resize(IMG_SIZE)
            arr   = np.array(img, dtype=np.float32) / 255.0
            arr   = np.expand_dims(arr, axis=0)           # shape (1,128,128,3)
            probs = _damage_model.predict(arr, verbose=0)  # shape (1,3)
            idx   = int(np.argmax(probs[0]))
            label = CLASSES[idx]
            confidence = float(probs[0][idx]) * 100
            logger.info("Damage prediction: %s  (%.1f%%)", label, confidence)
            return label
        except Exception as e:
            logger.error("Damage prediction failed: %s – falling back to rule-based", e)

    # ── Rule-based fallback ────────────────────────────────────
    return _rule_based_damage(image_path)


def _rule_based_damage(image_path: str) -> str:
    """
    Fast brightness-based heuristic when the CNN is not available.
    Uses thumbnailing to minimize memory and I/O overhead.
    """
    import time
    start = time.time()
    try:
        # Optimization: Open and Resize immediately to avoid loading full high-res image
        with Image.open(image_path) as img:
            img.thumbnail((64, 64))  # Small thumbnail is enough for brightness
            img = img.convert("L")   # grayscale
            brightness = np.mean(np.array(img))
        
        duration = time.time() - start
        logger.info("Fast rule-based analysis completed in %.4fs", duration)
        
        if brightness > 160:
            return "Low"
        elif brightness > 100:
            return "Medium"
        else:
            return "High"
    except Exception as e:
        logger.error("Fallback damage estimation failed: %s", e)
        return "Medium"   # safe default


def predict_price(age: int, mileage: int, vehicle_type: str, damage_level: str) -> float:
    """
    Predict scrap price.

    Parameters
    ----------
    age           : vehicle age in years
    mileage       : total km driven
    vehicle_type  : e.g. "Sedan", "SUV", "Truck", "Motorcycle", "Van"
    damage_level  : "Low" | "Medium" | "High"

    Returns
    -------
    float  – predicted scrap price in ₹
    """
    if _price_model is not None and _encoders is not None:
        try:
            le_type   = _encoders["vehicle_type"]
            le_damage = _encoders["damage_level"]

            # Handle unseen labels gracefully
            if vehicle_type not in le_type.classes_:
                vehicle_type = le_type.classes_[0]
            if damage_level not in le_damage.classes_:
                damage_level = "Medium"

            vt_enc = le_type.transform([vehicle_type])[0]
            dl_enc = le_damage.transform([damage_level])[0]

            X     = np.array([[age, mileage, vt_enc, dl_enc]], dtype=np.float32)
            price = float(_price_model.predict(X)[0])
            logger.info("Price prediction: ₹%.2f", price)
            return round(price, 2)
        except Exception as e:
            logger.error("Price prediction failed: %s – using formula fallback", e)

    # ── Formula fallback ──────────────────────────────────────
    return _formula_price(age, mileage, vehicle_type, damage_level)


def _formula_price(age, mileage, vehicle_type, damage_level) -> float:
    """Deterministic pricing formula (same logic as prepare_dataset.py)."""
    TYPE_MULT   = {"Sedan": 1.0, "SUV": 1.4, "Truck": 1.8, "Motorcycle": 0.5, "Van": 1.2}
    DAMAGE_MULT = {"Low": 1.0, "Medium": 0.65, "High": 0.30}

    base       = 50_000
    age_f      = max(0.20, 1 - 0.05 * int(age))
    mil_f      = max(0.60, 1 - 0.00002 * int(mileage))
    type_m     = TYPE_MULT.get(vehicle_type, 1.0)
    dmg_m      = DAMAGE_MULT.get(damage_level, 0.65)

    return round(base * age_f * mil_f * type_m * dmg_m, 2)
