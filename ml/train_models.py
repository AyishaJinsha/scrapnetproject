"""
Step 2: Model Training Script for ScrapNet ML Integration
=====================================================================
Trains two models:

  1. CNN (TensorFlow/Keras) – damage level classification
       Input  : 128×128 RGB vehicle image
       Output : Low / Medium / High

  2. Random Forest Regressor (scikit-learn) – scrap price prediction
       Inputs : age, mileage, vehicle_type, damage_level
       Output : scrap price (₹)

How to run (after prepare_dataset.py):
  cd c:\\Users\\ayish\\OneDrive\\Desktop\\scrapnet
  python ml/train_models.py

Saved models:
  ml/models/damage_model.h5       (CNN  – damage classification)
  ml/models/price_model.pkl       (RF   – scrap price regression)
  ml/models/label_encoders.pkl    (encoders for categorical features)
"""

import os
import sys
import pickle
import numpy as np
import pandas as pd
from PIL import Image

# ─────────────────────────── paths ───────────────────────────
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
IMG_DIR     = os.path.join(BASE_DIR, "dataset", "images")
CSV_PATH    = os.path.join(BASE_DIR, "dataset", "vehicle_data.csv")
MODEL_DIR   = os.path.join(BASE_DIR, "models")
os.makedirs(MODEL_DIR, exist_ok=True)

DAMAGE_MODEL_PATH   = os.path.join(MODEL_DIR, "damage_model.h5")
PRICE_MODEL_PATH    = os.path.join(MODEL_DIR, "price_model.pkl")
ENCODER_PATH        = os.path.join(MODEL_DIR, "label_encoders.pkl")

IMG_SIZE    = (128, 128)
CLASSES     = ["Low", "Medium", "High"]   # CNN output labels (title-case)
CLASS_DIRS  = ["low",  "medium",  "high"] # folder names (lower-case)


# ══════════════════════════════════════════════════════════════
# 1.  CNN – DAMAGE CLASSIFICATION
# ══════════════════════════════════════════════════════════════

def load_image_dataset():
    """Load images from ml/dataset/images/{low,medium,high}/ folders."""
    X, y = [], []
    print("\n🖼️   Loading images …")
    for idx, (folder, label) in enumerate(zip(CLASS_DIRS, CLASSES)):
        folder_path = os.path.join(IMG_DIR, folder)
        if not os.path.exists(folder_path):
            print(f"   ⚠️   Missing folder: {folder_path}")
            print("   → Run 'python ml/prepare_dataset.py' first!")
            sys.exit(1)
        files = [f for f in os.listdir(folder_path) if f.endswith(".jpg")]
        for fname in files:
            img = Image.open(os.path.join(folder_path, fname)).convert("RGB")
            img = img.resize(IMG_SIZE)
            X.append(np.array(img, dtype=np.float32) / 255.0)
            y.append(idx)
        print(f"   ✅  Loaded {len(files)} '{label}' images")

    return np.array(X), np.array(y)


def train_damage_model():
    try:
        import tensorflow as tf
        from tensorflow import keras
        from tensorflow.keras import layers
    except ImportError:
        print("   ❌  TensorFlow not installed. Run: pip install tensorflow")
        print("   ⚠️   Skipping CNN training. Using Rule-Based fallback in ml_model.py")
        return None

    X, y = load_image_dataset()
    total = len(X)
    print(f"\n   Total images: {total}")

    # Shuffle
    idx = np.random.permutation(total)
    X, y = X[idx], y[idx]

    split = int(0.8 * total)
    X_train, X_test = X[:split], X[split:]
    y_train, y_test = y[:split], y[split:]

    print(f"   Train: {len(X_train)}  |  Test: {len(X_test)}")

    # ── Build CNN ─────────────────────────────────────────────
    model = keras.Sequential([
        # Block 1
        layers.Conv2D(32, (3, 3), activation="relu", input_shape=(128, 128, 3)),
        layers.MaxPooling2D(2, 2),
        # Block 2
        layers.Conv2D(64, (3, 3), activation="relu"),
        layers.MaxPooling2D(2, 2),
        # Block 3
        layers.Conv2D(128, (3, 3), activation="relu"),
        layers.MaxPooling2D(2, 2),
        # Head
        layers.Flatten(),
        layers.Dense(256, activation="relu"),
        layers.Dropout(0.4),
        layers.Dense(3, activation="softmax"),   # 3 classes
    ])

    model.compile(
        optimizer="adam",
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )
    model.summary()

    print("\n🤖  Training CNN (10 epochs) …")
    history = model.fit(
        X_train, y_train,
        epochs=10,
        batch_size=32,
        validation_data=(X_test, y_test),
        verbose=1,
    )

    # Evaluate
    loss, acc = model.evaluate(X_test, y_test, verbose=0)
    print(f"\n   ✅  CNN Accuracy: {acc * 100:.2f}%  |  Loss: {loss:.4f}")

    # Save
    model.save(DAMAGE_MODEL_PATH)
    print(f"   💾  Model saved → {DAMAGE_MODEL_PATH}")
    return model


# ══════════════════════════════════════════════════════════════
# 2.  RANDOM FOREST – SCRAP PRICE PREDICTION
# ══════════════════════════════════════════════════════════════

def train_price_model():
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import LabelEncoder
    from sklearn.metrics import mean_squared_error

    if not os.path.exists(CSV_PATH):
        print(f"   ⚠️   Missing CSV: {CSV_PATH}")
        print("   → Run 'python ml/prepare_dataset.py' first!")
        sys.exit(1)

    print("\n💰  Training Price Prediction Model …")
    df = pd.read_csv(CSV_PATH)
    print(f"   Dataset shape: {df.shape}")
    print(df.head(3))

    # Encode categorical columns
    le_type   = LabelEncoder()
    le_damage = LabelEncoder()

    df["vehicle_type_enc"] = le_type.fit_transform(df["vehicle_type"])
    df["damage_level_enc"] = le_damage.fit_transform(df["damage_level"])

    features = ["age", "mileage", "vehicle_type_enc", "damage_level_enc"]
    X = df[features].values
    y = df["scrap_price"].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    rf = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    rf.fit(X_train, y_train)

    preds = rf.predict(X_test)
    rmse  = np.sqrt(mean_squared_error(y_test, preds))
    print(f"\n   ✅  RMSE: ₹{rmse:.2f}")
    print(f"   Sample actual vs predicted: {list(zip(y_test[:5].round(0), preds[:5].round(0)))}")

    # Save model + encoders
    with open(PRICE_MODEL_PATH, "wb") as f:
        pickle.dump(rf, f)
    with open(ENCODER_PATH, "wb") as f:
        pickle.dump({"vehicle_type": le_type, "damage_level": le_damage}, f)

    print(f"   💾  Price model saved  → {PRICE_MODEL_PATH}")
    print(f"   💾  Encoders saved     → {ENCODER_PATH}")
    return rf


# ══════════════════════════════════════════════════════════════
# 3.  MAIN
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("  ScrapNet – Model Training (Step 2 of ML Pipeline)")
    print("=" * 60)

    print("\n【1/2】 Training Damage Classification CNN …")
    train_damage_model()

    print("\n【2/2】 Training Scrap Price Regression Model …")
    train_price_model()

    print("\n" + "=" * 60)
    print("  ✅  Both models trained and saved!")
    print(f"  Damage model : {DAMAGE_MODEL_PATH}")
    print(f"  Price model  : {PRICE_MODEL_PATH}")
    print("\n  Next step → Update Django database and integrate ml_model.py")
    print("=" * 60)
