"""
ml_pipeline.py - Machine Learning Pipeline for Pathal Kaval (ESP32 JSON Telemetry)

Hardware Sensor Ranges:
1. [MQ-3 Breath / Alcohol Sensor] (ADC 0-4095, GPIO 34): Baseline ~850, blowing breath spikes to 2800-3900.
2. [GL5528 LDR Sensor] (ADC 0-4095, GPIO 35): Ambient ~1900, covered drops < 450.
3. [Laptop Built-in Mic / Speech STT] (Trigger 0 or 1): Real-time Malayalam chant & loud shout detection.
4. [10K Potentiometer Gate Angle] (0 - 90 deg, GPIO 32): Locked gate rotated to > 65 deg.

Target Actions: ["IDLE", "BLOWING", "GATE_LOCKED", "SHOUT_MIC", "LIGHT_COVERED"]
"""

import os
import pickle
import numpy as np
from typing import Tuple, Dict, List, Optional
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

MODEL_FILE = os.path.join(os.path.dirname(__file__), "action_classifier.pkl")

ACTIONS = [
    "IDLE",
    "BLOWING",
    "GATE_LOCKED",
    "SHOUT_MIC",
    "LIGHT_COVERED"
]


def generate_synthetic_telemetry(n_samples_per_class: int = 1500, random_state: int = 42) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate realistic 12-bit ADC sensor readings:
      0: mq3_raw     (MQ-3 Breath Sensor: 0 - 4095)
      1: ldr_raw     (GL5528 LDR Sensor: 0 - 4095)
      2: mic_trigger (Laptop Built-in Mic Shout: 0 or 1)
      3: gate_angle  (10K Potentiometer: 0 - 90 deg)
    """
    rng = np.random.RandomState(random_state)
    X_list = []
    y_list = []

    # 1. IDLE (Normal baseline ambient state)
    for _ in range(n_samples_per_class):
        mq3 = rng.normal(loc=500, scale=60)
        ldr = rng.normal(loc=1900, scale=120)
        mic = 0 if rng.rand() > 0.02 else 1
        gate = rng.normal(loc=18, scale=8)
        X_list.append([mq3, ldr, mic, gate])
        y_list.append("IDLE")

    # 2. BLOWING (Player blows onto MQ-3 Breath Sensor)
    for _ in range(n_samples_per_class):
        mq3 = rng.normal(loc=2200, scale=400)
        ldr = rng.normal(loc=1850, scale=120)
        mic = 0
        gate = rng.normal(loc=18, scale=8)
        X_list.append([mq3, ldr, mic, gate])
        y_list.append("BLOWING")

    # 3. LIGHT_COVERED (Player covers GL5528 LDR Sensor)
    for _ in range(n_samples_per_class):
        mq3 = rng.normal(loc=500, scale=60)
        ldr = rng.normal(loc=240, scale=60)
        mic = 0
        gate = rng.normal(loc=18, scale=8)
        X_list.append([mq3, ldr, mic, gate])
        y_list.append("LIGHT_COVERED")

    # 4. GATE_LOCKED (Player rotates 10K Potentiometer to lock position > 65°)
    for _ in range(n_samples_per_class):
        mq3 = rng.normal(loc=500, scale=60)
        ldr = rng.normal(loc=1900, scale=120)
        mic = 0
        gate = rng.normal(loc=82, scale=6)
        X_list.append([mq3, ldr, mic, gate])
        y_list.append("GATE_LOCKED")

    # 5. SHOUT_MIC (Player chants / shouts into Laptop Microphone)
    for _ in range(n_samples_per_class):
        mq3 = rng.normal(loc=510, scale=60)
        ldr = rng.normal(loc=1900, scale=120)
        mic = 1
        gate = rng.normal(loc=20, scale=10)
        X_list.append([mq3, ldr, mic, gate])
        y_list.append("SHOUT_MIC")

    X = np.array(X_list)
    # Clip values to 12-bit ADC ranges
    X[:, 0] = np.clip(X[:, 0], 0, 4095)  # mq3_raw
    X[:, 1] = np.clip(X[:, 1], 0, 4095)  # ldr_raw
    X[:, 2] = np.clip(X[:, 2], 0, 1)     # mic_trigger
    X[:, 3] = np.clip(X[:, 3], 0, 90)    # gate_angle

    y = np.array(y_list)
    return X, y


def train_and_save_model(output_path: str = MODEL_FILE) -> RandomForestClassifier:
    """Train the RandomForestClassifier and export it to action_classifier.pkl."""
    print("=" * 60)
    print("Pathal Kaval AI - Training Action Classifier (RandomForest)")
    print("=" * 60)

    X, y = generate_synthetic_telemetry(n_samples_per_class=1500)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    clf = RandomForestClassifier(
        n_estimators=120,
        max_depth=12,
        min_samples_split=4,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1
    )
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"\nModel Accuracy on Test Set: {acc * 100:.2f}%")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, digits=4))

    # Save to disk
    with open(output_path, "wb") as f:
        pickle.dump({
            "model": clf,
            "classes": clf.classes_,
            "feature_names": ["mq3_raw", "ldr_raw", "laptop_mic", "gate_angle"]
        }, f)

    print(f"[OK] Model successfully serialized to: {output_path}\n")
    return clf


class ActionPredictor:
    """
    Inference helper for real-time game action prediction.
    Features rolling window smoothing and confidence calculation.
    """
    def __init__(self, model_path: str = MODEL_FILE, window_size: int = 5):
        self.model_path = model_path
        self.window_size = window_size
        self.history: List[str] = []
        self.model: Optional[RandomForestClassifier] = None
        self.classes: Optional[np.ndarray] = None
        self.load_or_train_model()

    def load_or_train_model(self):
        """Loads action_classifier.pkl or trains it if missing."""
        if not os.path.exists(self.model_path):
            print(f"[WARN] {self.model_path} not found. Training a new model automatically...")
            self.model = train_and_save_model(self.model_path)
            self.classes = self.model.classes_
        else:
            try:
                with open(self.model_path, "rb") as f:
                    data = pickle.load(f)
                    self.model = data["model"]
                    self.classes = data["classes"]
                print(f"[OK] ActionPredictor loaded model from {self.model_path}")
            except Exception as e:
                print(f"[ERROR] Failed to load model: {e}. Retraining...")
                self.model = train_and_save_model(self.model_path)
                self.classes = self.model.classes_

    def predict(self, thermistor: float, ldr: float, mic_trigger: int, gate_angle: float) -> Tuple[str, float, Dict[str, float]]:
        """
        Takes live sensor snapshot and returns:
          - smoothed_action (str)
          - confidence (float 0.0 - 1.0)
          - probabilities (dict mapping class name to float)
        """
        if self.model is None:
            return "IDLE", 0.0, {c: 0.0 for c in ACTIONS}

        features = np.array([[
            float(np.clip(thermistor, 0, 4095)),
            float(np.clip(ldr, 0, 4095)),
            int(1 if mic_trigger else 0),
            float(np.clip(gate_angle, 0, 90))
        ]])

        try:
            raw_pred = self.model.predict(features)[0]
            probs = self.model.predict_proba(features)[0]
            prob_dict = {cls: float(p) for cls, p in zip(self.classes, probs)}
            confidence = float(np.max(probs))

            # Sliding window for temporal smoothing
            self.history.append(raw_pred)
            if len(self.history) > self.window_size:
                self.history.pop(0)

            # Majority vote over the sliding window
            action_counts = {}
            for act in self.history:
                action_counts[act] = action_counts.get(act, 0) + 1
            smoothed_action = max(action_counts, key=action_counts.get)

            return smoothed_action, confidence, prob_dict
        except Exception as err:
            print(f"[Predict Error] {err}")
            return "IDLE", 0.0, {c: 0.0 for c in ACTIONS}


if __name__ == "__main__":
    train_and_save_model()
