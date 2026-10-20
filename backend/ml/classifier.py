"""
ForestWatch AI - ML Classifier

Random Forest classifier for forest disturbance classification.
Trained on synthetic feature vectors that mirror what Sentinel data would provide.

Production upgrade path:
1. Replace synthetic training data with real labeled Sentinel data
2. Consider CNN for direct image classification
3. Use SHAP for model interpretability
"""
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, f1_score
from sklearn.pipeline import Pipeline
import joblib
import os
from typing import Dict, List, Tuple, Optional
import zlib

# Category mapping
CATEGORIES = [
    "pertanian",
    "penebangan",
    "pertambangan",
    "kebakaran",
    "alami",
    "tidak_diketahui",
]

CATEGORY_LABELS = {
    "pertanian": "Pertanian / Land Clearing",
    "penebangan": "Penebangan Liar",
    "pertambangan": "Pertambangan",
    "kebakaran": "Kebakaran Hutan",
    "alami": "Gangguan Alami",
    "tidak_diketahui": "Tidak Diketahui / Perlu Verifikasi",
}

# Feature names (mirrors GEE feature extraction output)
FEATURE_NAMES = [
    "ndvi_before", "ndvi_after", "ndvi_change",
    "nbr_before", "nbr_after", "nbr_change",
    "evi_before", "evi_after",
    "b4_red_after", "b8_nir_after", "b11_swir1_after", "b12_swir2_after",
    "sar_vv_before", "sar_vv_after", "sar_vv_change",
    "cloud_coverage", "area_ha",
]


# Kelas -> profil spektral pada gis/sentinel_mock.py. "tidak_diketahui" dipetakan ke profil
# "degraded_forest" (degradasi ringan/ambigu) karena tidak ada profil khusus untuk kelas ini.
MOCK_PROFILE_FOR_CATEGORY = {
    "pertanian": "pertanian",
    "penebangan": "penebangan",
    "pertambangan": "pertambangan",
    "kebakaran": "kebakaran",
    "alami": "alami",
    "tidak_diketahui": "degraded_forest",
}


def _generate_synthetic_features(category: str, n_samples: int = 80) -> np.ndarray:
    """
    Bangkitkan sampel latih dari generator Sentinel SIMULASI yang sama dengan data demo
    (gis/sentinel_mock.py), sehingga pelatihan dan demo konsisten. Konsekuensinya metrik evaluasi
    bersifat optimistis: model diuji pada distribusi yang dibuat oleh generator yang sama.
    """
    from datetime import datetime
    import random
    from gis.sentinel_mock import generate_change_detection_pair

    rng = random.Random(zlib.crc32(category.encode()))  # stabil lintas proses
    profile = MOCK_PROFILE_FOR_CATEGORY[category]
    rows = []
    for _ in range(n_samples):
        pair = generate_change_detection_pair(profile, "latih", datetime(2023, 1, 1), datetime(2023, 6, 1), rng=rng)
        m = pair["change_metrics"]
        rows.append(extract_features(
            ndvi_before=m["ndvi_before"], ndvi_after=m["ndvi_after"],
            nbr_before=m["nbr_before"], nbr_after=m["nbr_after"],
            evi_before=m["evi_before"], evi_after=m["evi_after"],
            b4_red_after=m["b4_red_after"], b8_nir_after=m["b8_nir_after"],
            b11_swir1_after=m["b11_swir1_after"], b12_swir2_after=m["b12_swir2_after"],
            sar_vv_before=m["sar_vv_before"], sar_vv_after=m["sar_vv_after"],
            cloud_coverage=pair["sentinel2_before"]["cloud_coverage_pct"],
            area_ha=rng.uniform(5, 350),
        )[0])
    return np.array(rows)


def build_and_train_model() -> Tuple[Pipeline, Dict]:
    """Build and train the classification model on synthetic data."""
    X_list, y_list = [], []
    
    for cat in CATEGORIES:
        X_cat = _generate_synthetic_features(cat, n_samples=100)
        y_cat = [cat] * len(X_cat)
        X_list.append(X_cat)
        y_list.extend(y_cat)
    
    X = np.vstack(X_list)
    y = np.array(y_list)
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )
    
    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", RandomForestClassifier(
            n_estimators=150,
            max_depth=10,
            min_samples_split=5,
            random_state=42,
            class_weight="balanced",
        )),
    ])
    
    pipeline.fit(X_train, y_train)
    y_pred = pipeline.predict(X_test)
    
    report = classification_report(y_test, y_pred, output_dict=True, zero_division=0)

    # Baseline sederhana pada split yang sama, sebagai pembanding wajar.
    baselines = {}
    for name, base in (
        ("majority_class", DummyClassifier(strategy="most_frequent")),
        ("logistic_regression", Pipeline([("scaler", StandardScaler()), ("clf", LogisticRegression(max_iter=1000, random_state=42))])),
    ):
        base.fit(X_train, y_train)
        bp = base.predict(X_test)
        baselines[name] = {
            "accuracy": float((bp == y_test).mean()),
            "macro_f1": float(f1_score(y_test, bp, average="macro", zero_division=0)),
        }
    cm = confusion_matrix(y_test, y_pred, labels=CATEGORIES).tolist()
    
    evaluation = {
        "model_type": "RandomForestClassifier",
        "n_estimators": 150,
        "training_samples": len(X_train),
        "test_samples": len(X_test),
        "accuracy": report["accuracy"],
        "baselines": baselines,
        "macro_f1": report["macro avg"]["f1-score"],
        "weighted_f1": report["weighted avg"]["f1-score"],
        "classification_report": report,
        "confusion_matrix": cm,
        "confusion_matrix_labels": CATEGORIES,
        "feature_names": FEATURE_NAMES,
        "feature_medians": [float(v) for v in np.median(X_train, axis=0)],
        "note": (
            "Model dilatih dan diuji pada data SINTETIS dari generator yang sama dengan data demo; "
            "metrik bersifat optimistis dan BUKAN akurasi dunia nyata. Ganti dengan citra Sentinel "
            "berlabel dan pembagian data yang menghindari kebocoran spasial/temporal untuk penggunaan nyata."
        )
    }
    
    return pipeline, evaluation


# Global model instance (lazy loaded)
_model: Optional[Pipeline] = None
_model_evaluation: Optional[Dict] = None


def get_model() -> Tuple[Pipeline, Dict]:
    """Get or initialize the ML model."""
    global _model, _model_evaluation
    if _model is None:
        print("[ForestWatch ML] Training model on synthetic data...")
        _model, _model_evaluation = build_and_train_model()
        print(f"[ForestWatch ML] Model ready. Accuracy: {_model_evaluation['accuracy']:.3f}")
    return _model, _model_evaluation


def extract_features(
    ndvi_before: float,
    ndvi_after: float,
    nbr_before: float,
    nbr_after: float,
    evi_before: float,
    evi_after: float,
    b4_red_after: float,
    b8_nir_after: float,
    b11_swir1_after: float,
    b12_swir2_after: float,
    sar_vv_before: float,
    sar_vv_after: float,
    cloud_coverage: float,
    area_ha: float,
) -> np.ndarray:
    """
    Susun vektor fitur sesuai urutan FEATURE_NAMES.

    Semua masukan wajib: tidak ada nilai bawaan diam-diam, karena fitur SWIR/NIR sangat menentukan kelas.
    """
    return np.array([[
        ndvi_before, ndvi_after, ndvi_after - ndvi_before,
        nbr_before, nbr_after, nbr_after - nbr_before,
        evi_before, evi_after,
        b4_red_after, b8_nir_after, b11_swir1_after, b12_swir2_after,
        sar_vv_before, sar_vv_after, sar_vv_after - sar_vv_before,
        cloud_coverage, area_ha,
    ]], dtype=float)


def predict(feature_vector: np.ndarray) -> Dict:
    """
    Run inference and return prediction with confidence scores.
    """
    model, _ = get_model()
    
    proba = model.predict_proba(feature_vector)[0]
    classes = model.classes_
    
    proba_dict = {cls: float(p) for cls, p in zip(classes, proba)}
    
    # Sort by probability
    sorted_proba = sorted(proba_dict.items(), key=lambda x: x[1], reverse=True)
    top_category, top_confidence = sorted_proba[0]
    
    # Apply confidence threshold
    from config import settings
    if top_confidence < settings.CONFIDENCE_THRESHOLD:
        top_category = "tidak_diketahui"
    
    # Tingkat keyakinan
    if top_confidence >= 0.75:
        confidence_level = "tinggi"
    elif top_confidence >= 0.50:
        confidence_level = "sedang"
    else:
        confidence_level = "rendah"
    
    return {
        "predicted_category": top_category,
        "category_label": CATEGORY_LABELS.get(top_category, top_category),
        "confidence_score": round(top_confidence, 4),
        "confidence_level": confidence_level,
        "needs_verification": top_category == "tidak_diketahui" or confidence_level == "rendah",
        "all_probabilities": {k: round(v, 4) for k, v in proba_dict.items()},
        "top_3_categories": [
            {"category": cat, "probability": round(prob, 4), "label": CATEGORY_LABELS.get(cat, cat)}
            for cat, prob in sorted_proba[:3]
        ],
        "model_disclaimer": (
            "Prediksi ini dihasilkan oleh model ML berbasis data sintetis. "
            "Hasil bukan verifikasi lapangan. Gunakan sebagai indikasi awal saja."
        )
    }


def explain(feature_vector: np.ndarray, predicted_category: str, top_k: int = 5) -> Dict:
    """
    Penjelasan LOKAL berbasis oklusi: tiap fitur diganti median data latih, lalu dicatat penurunan probabilitas kelas prediksi.
    Nilai positif = fitur itu mendorong prediksi. Ini perkiraan sederhana (bukan SHAP) dan hanya menjelaskan perilaku model,
    bukan penyebab nyata di lapangan; fitur yang saling berkorelasi (mis. NDVI dan EVI) dapat saling menutupi.
    """
    model, evaluation = get_model()
    medians = np.asarray(evaluation["feature_medians"], dtype=float)
    classes = list(model.classes_)
    if predicted_category not in classes:
        predicted_category = classes[int(np.argmax(model.predict_proba(feature_vector)[0]))]
    idx = classes.index(predicted_category)
    base = float(model.predict_proba(feature_vector)[0][idx])
    rows = []
    for i, name in enumerate(FEATURE_NAMES):
        ablated = feature_vector.copy()
        ablated[0, i] = medians[i]
        rows.append({"feature": name, "value": float(feature_vector[0, i]), "reference_median": float(medians[i]),
                     "contribution": round(base - float(model.predict_proba(ablated)[0][idx]), 4)})
    rows.sort(key=lambda r: abs(r["contribution"]), reverse=True)
    return {"method": "oklusi terhadap median data latih (perkiraan, bukan SHAP)", "target_category": predicted_category,
            "base_probability": round(base, 4), "top_features": rows[:top_k],
            "caveat": "Menjelaskan perilaku model pada data simulasi; bukan bukti penyebab di lapangan."}
