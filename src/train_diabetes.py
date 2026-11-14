"""Precision-focused diabetes model training."""
import os
import sys
import warnings

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
import joblib
import matplotlib
matplotlib.use("Agg")

from sklearn.ensemble        import RandomForestClassifier, GradientBoostingClassifier
from sklearn.calibration     import CalibratedClassifierCV
from sklearn.model_selection import (
    GridSearchCV, RandomizedSearchCV, StratifiedKFold, cross_val_score, cross_val_predict
)
from sklearn.metrics         import (
    precision_score, recall_score, f1_score, classification_report, make_scorer
)
from sklearn.preprocessing   import StandardScaler
from sklearn.pipeline        import Pipeline
from xgboost                 import XGBClassifier

from src.common.datasets     import load_processed
from src.common.metrics      import compute_metrics, save_evaluation_panel, save_roc_curve
from src.common.paths        import MODELS_DIR, PLOTS_DIR, ensure_dirs
from src.preprocess          import preprocess_diabetes

warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────
#  PATHS
# ─────────────────────────────────────────────
ensure_dirs(MODELS_DIR, PLOTS_DIR)
LEGACY_DIABETES_DIR = os.path.join(MODELS_DIR, "legacy_diabetes")
ensure_dirs(LEGACY_DIABETES_DIR)

CLASS_LABELS = ["No Diabetes", "Diabetes"]
PRECISION_TARGET = 0.80
RECALL_FLOOR = 0.72

print("=" * 62)
print("  DIABETES MODEL — PRECISION-FOCUSED TRAINING")
print("=" * 62)

# ─────────────────────────────────────────────
#  PREPROCESS DATA
# ─────────────────────────────────────────────
print("\n  Preprocessing diabetes raw data and regenerating feature sets...")
preprocess_diabetes()

X_train, y_train, X_test, y_test = load_processed("diabetes")

n_pos      = int(y_train.sum())
n_neg      = int(len(y_train) - n_pos)
scale_pos  = n_neg / n_pos
print(f"\n  Train: {len(X_train)} | Test: {len(X_test)}")
print(f"  Negative: {n_neg} | Positive: {n_pos} | scale_pos_weight={scale_pos:.2f}")

print("\n  Loading regenerated diabetes features...")
X_train_eng = X_train.copy()
X_test_eng  = X_test.copy()
print(f"  Loaded {X_train_eng.shape[1]} processed features for training")

cv5 = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

# ─────────────────────────────────────────────
#  PRECISION-CONSTRAINED SCORER FOR HYPERPARAM SEARCH
#  Rewards recall, but only once precision clears the floor.
#  This keeps GridSearch/RandomizedSearch aligned with the
#  stated goal instead of optimizing plain F1.
# ─────────────────────────────────────────────
def precision_gated_score(y_true, y_proba_or_pred):
    # Works whether the estimator exposes predict (0/1) or we pass proba.
    yp = y_proba_or_pred
    p = precision_score(y_true, yp, zero_division=0)
    r = recall_score(y_true, yp, zero_division=0)
    if p < PRECISION_TARGET:
        # Penalize under-target precision so the search moves toward it.
        return p - 1.0
    return r

precision_gated_scorer = make_scorer(precision_gated_score)

# ─────────────────────────────────────────────
#  PRECISION-FOCUSED THRESHOLD FINDER (unchanged logic,
#  now always called with OUT-OF-FOLD probabilities)
# ─────────────────────────────────────────────
def find_precision_threshold(y_true, y_proba, min_precision=PRECISION_TARGET, min_recall=RECALL_FLOOR):
    thresholds = np.arange(0.30, 0.80, 0.01)
    best_t, best_f1 = 0.5, 0.0
    valid = []
    for t in thresholds:
        yp = (y_proba >= t).astype(int)
        p  = precision_score(y_true, yp, zero_division=0)
        r  = recall_score(y_true,    yp, zero_division=0)
        f  = f1_score(y_true,        yp, zero_division=0)
        if p >= min_precision and r >= min_recall:
            valid.append((t, p, r, f))
        if f > best_f1:
            best_f1, best_t = f, t
    if valid:
        bv = max(valid, key=lambda x: x[3])
        print(f"  Target reached at threshold {bv[0]:.2f} → "
              f"Prec={bv[1]*100:.1f}%  Rec={bv[2]*100:.1f}%  F1={bv[3]:.4f}")
        return round(bv[0], 2)
    print(f"  Target not reached — using best-F1 threshold={best_t:.2f} (F1={best_f1:.4f})")
    return round(best_t, 2)

# ─────────────────────────────────────────────
#  MODEL 1 — RANDOM FOREST (class_weight, no SMOTE)
#  SMOTE adds noise which hurts precision
# ─────────────────────────────────────────────
print("\n[1/4] Tuning Random Forest (no SMOTE, class_weight=balanced)...")
rf_pipe = Pipeline([
    ("scaler", StandardScaler()),
    ("clf", RandomForestClassifier(
        random_state=42, class_weight="balanced", n_jobs=-1
    ))
])
rf_grid = GridSearchCV(
    rf_pipe,
    {
        "clf__n_estimators":      [300, 500],
        "clf__max_depth":         [8, 12, None],
        "clf__min_samples_split": [2, 5, 10],
        "clf__min_samples_leaf":  [1, 2, 4],
        "clf__max_features":      ["sqrt", "log2"],
    },
    cv=cv5, scoring=precision_gated_scorer, n_jobs=-1, verbose=0
)
rf_grid.fit(X_train_eng, y_train)
rf_best  = rf_grid.best_estimator_
rf_cv_score = rf_grid.best_score_
print(f"  Best params : {rf_grid.best_params_}")
print(f"  Best CV precision-gated score : {rf_cv_score:.4f}")

# ─────────────────────────────────────────────
#  MODEL 2 — XGBOOST (scale_pos_weight + regularization)
#  L1/L2 regularization reduces false positives → higher precision
# ─────────────────────────────────────────────
print("\n[2/4] Tuning XGBoost (scale_pos_weight + L1/L2 regularization)...")
xgb_pipe = Pipeline([
    ("scaler", StandardScaler()),
    ("clf", XGBClassifier(
        random_state=42, eval_metric="logloss",
        scale_pos_weight=scale_pos, n_jobs=-1
    ))
])
xgb_search = RandomizedSearchCV(
    xgb_pipe,
    {
        "clf__n_estimators":     [100, 200, 300],
        "clf__max_depth":        [3, 4, 5],
        "clf__learning_rate":    [0.01, 0.05, 0.1],
        "clf__subsample":        [0.7, 0.85, 1.0],
        "clf__colsample_bytree": [0.7, 0.85, 1.0],
        "clf__min_child_weight": [1, 3, 5],
        "clf__gamma":            [0, 0.1, 0.3],
        "clf__reg_alpha":        [0, 0.1, 0.5],   # L1 → precision boost
        "clf__reg_lambda":       [1, 1.5, 2.0],   # L2 → precision boost
    },
    n_iter=30, cv=cv5, scoring=precision_gated_scorer, n_jobs=-1, verbose=0, random_state=42
)
xgb_search.fit(X_train_eng, y_train)
xgb_best  = xgb_search.best_estimator_
xgb_cv_score = xgb_search.best_score_
print(f"  Best params : {xgb_search.best_params_}")
print(f"  Best CV precision-gated score : {xgb_cv_score:.4f}")

# ─────────────────────────────────────────────
#  MODEL 3 — GRADIENT BOOSTING
# ─────────────────────────────────────────────
print("\n[3/4] Gradient Boosting...")
gb_pipe = Pipeline([
    ("scaler", StandardScaler()),
    ("clf", GradientBoostingClassifier(
        random_state=42, n_estimators=300,
        max_depth=4, learning_rate=0.05,
        subsample=0.85, min_samples_split=10, min_samples_leaf=5
    ))
])
gb_scores = cross_val_score(gb_pipe, X_train_eng, y_train, cv=cv5, scoring=precision_gated_scorer)
gb_cv_score = gb_scores.mean()
print(f"  CV precision-gated score: {gb_cv_score:.4f} (±{gb_scores.std():.4f})")
gb_pipe.fit(X_train_eng, y_train)

# ─────────────────────────────────────────────
#  MODEL 4 — CALIBRATED XGBOOST (Platt scaling)
#  Calibration makes probabilities more reliable
#  → threshold search finds better precision point
# ─────────────────────────────────────────────
print("\n[4/4] Calibrated XGBoost (Platt scaling)...")
best_xgb_params = {
    k.replace("clf__", ""): v
    for k, v in xgb_search.best_params_.items()
}
xgb_base = XGBClassifier(
    **best_xgb_params, random_state=42,
    eval_metric="logloss", scale_pos_weight=scale_pos, n_jobs=-1
)
cal_pipe = Pipeline([
    ("scaler", StandardScaler()),
    ("clf", CalibratedClassifierCV(xgb_base, method="sigmoid", cv=3))
])
cal_scores = cross_val_score(cal_pipe, X_train_eng, y_train, cv=3, scoring=precision_gated_scorer)
cal_cv_score = cal_scores.mean()
print(f"  CV precision-gated score: {cal_cv_score:.4f} (±{cal_scores.std():.4f})")
cal_pipe.fit(X_train_eng, y_train)

# ─────────────────────────────────────────────
#  SELECT BEST MODEL
# ─────────────────────────────────────────────
candidates = {
    "Random Forest (Balanced)": (rf_best,   rf_cv_score),
    "XGBoost (Tuned)":          (xgb_best,  xgb_cv_score),
    "Gradient Boosting":        (gb_pipe,   gb_cv_score),
    "Calibrated XGBoost":       (cal_pipe,  cal_cv_score),
}

print("\n" + "=" * 62)
print("  CV PRECISION-GATED SCORE RANKING")
print("=" * 62)
for name, (_, score) in sorted(candidates.items(), key=lambda x: -x[1][1]):
    # score can be negative (precision below target) — clip for the bar
    bar = "█" * max(int(score * 30), 0)
    print(f"  {name:<30} score={score:.4f}  {bar}")

best_name, (best_model, _) = max(candidates.items(), key=lambda x: x[1][1])
print(f"\n  ✅ Selected: {best_name}")
best_model.fit(X_train_eng, y_train)

# ─────────────────────────────────────────────
#  THRESHOLD SELECTION — OUT-OF-FOLD, NOT ON TRAINING PREDICTIONS
#  Fitting best_model on the full training set and then scoring it on
#  that same training set (as the old script did) overstates precision
#  and recall, because the model has memorized part of what it's being
#  evaluated on. cross_val_predict instead gives each training row a
#  probability from a fold where that row was held out, which is a
#  realistic stand-in for test-time performance.
# ─────────────────────────────────────────────
print("\n  Finding precision-optimized threshold (out-of-fold predictions)...")
y_proba_oof = cross_val_predict(
    best_model, X_train_eng, y_train, cv=cv5,
    method="predict_proba", n_jobs=-1
)[:, 1]
best_threshold = find_precision_threshold(
    y_train, y_proba_oof, min_precision=PRECISION_TARGET, min_recall=RECALL_FLOOR
)

# ─────────────────────────────────────────────
#  FINAL EVALUATION (held-out test set — untouched throughout)
# ─────────────────────────────────────────────
y_proba = best_model.predict_proba(X_test_eng)[:, 1]
y_pred  = (y_proba >= best_threshold).astype(int)

metrics = compute_metrics(y_test, y_pred, y_proba)
acc, prec, rec = metrics["accuracy"], metrics["precision"], metrics["recall"]
f1, auc, pr_auc, mcc = metrics["f1"], metrics["auc"], metrics["pr_auc"], metrics["mcc"]
cm = metrics["confusion_matrix"]
TN, FP, FN, TP = cm["tn"], cm["fp"], cm["fn"], cm["tp"]

print("\n" + "=" * 62)
print("  FINAL TEST RESULTS — BEFORE vs AFTER")
print("=" * 62)
print(f"  {'Metric':<20} {'Before':>10} {'After':>10}  {'Status'}")
print(f"  {'─'*55}")
print(f"  {'Accuracy':<20} {'81.29%':>10} {acc*100:>9.2f}%  {'✅' if acc>0.81 else '⚠️'}")
print(f"  {'Precision':<20} {'68.42%':>10} {prec*100:>9.2f}%  {'✅ FIXED' if prec>0.75 else '⚠️ Improve more'}")
print(f"  {'Recall':<20} {'82.98%':>10} {rec*100:>9.2f}%")
print(f"  {'F1 Score':<20} {'0.7500':>10} {f1:>10.4f}  {'✅' if f1>0.75 else '⚠️'}")
print(f"  {'ROC-AUC':<20} {'0.9170':>10} {auc:>10.4f}  {'✅' if auc>0.91 else '⚠️'}")
print(f"  {'PR-AUC':<20} {'   —  ':>10} {pr_auc:>10.4f}")
print(f"  {'MCC':<20} {'0.6099':>10} {mcc:>10.4f}")
print(f"\n  TP={TP}  TN={TN}  FP={FP}  FN={FN}")
print(f"  False Negative Rate : {FN/(FN+TP)*100:.2f}%  ({FN} diabetics missed)")
print(f"  False Positive Rate : {FP/(FP+TN)*100:.2f}%  ({FP} wrongly flagged)")
print(f"\n{classification_report(y_test, y_pred, target_names=CLASS_LABELS, zero_division=0)}")
print(
    "\n  Note: these test-set numbers can legitimately differ from the CV\n"
    "  precision-gated score above — the test set is a single held-out\n"
    "  split, while the CV score is averaged across folds. If the test\n"
    "  numbers look implausibly close to 100%, re-check for leakage\n"
    "  upstream (e.g. features derived using target info, or duplicate\n"
    "  rows shared between train and test)."
)

# ─────────────────────────────────────────────
#  SAVE
# ─────────────────────────────────────────────
feature_cols = list(X_train_eng.columns)
joblib.dump(best_model,     os.path.join(LEGACY_DIABETES_DIR, "diabetes_model.pkl"))
joblib.dump(best_name,      os.path.join(LEGACY_DIABETES_DIR, "diabetes_model_name.pkl"))
joblib.dump(best_threshold, os.path.join(LEGACY_DIABETES_DIR, "diabetes_threshold.pkl"))
joblib.dump(feature_cols,   os.path.join(LEGACY_DIABETES_DIR, "diabetes_model_features.pkl"))
print(f"  Saved threshold={best_threshold} → models/legacy_diabetes/diabetes_threshold.pkl")
print(f"  Saved {len(feature_cols)} model features → models/legacy_diabetes/diabetes_model_features.pkl")

# ─────────────────────────────────────────────
#  PLOTS
# ─────────────────────────────────────────────
save_evaluation_panel(
    y_test, y_proba, metrics,
    model_name=best_name,
    disease_label="Diabetes",
    class_labels=CLASS_LABELS,
    output_paths=[
        os.path.join(PLOTS_DIR, "diabetes_confusion_matrix.png"),
        os.path.join(LEGACY_DIABETES_DIR, "diabetes_model_evaluation.png"),
    ],
    cm_subtitle=f"Precision={prec*100:.1f}%  Recall={rec*100:.1f}%",
    precision_target=PRECISION_TARGET,
)
save_roc_curve(
    y_test, y_proba, auc,
    title="Diabetes: ROC Curve",
    output_path=os.path.join(PLOTS_DIR, "diabetes_roc_curve.png"),
)

print("\n  Plots saved → notebooks/eval_plots/")
print("\n" + "=" * 62)
print("  SERVING")
print("=" * 62)
print(f"""
  src/app.py picks the new artifacts up automatically through
  src.common.artifacts.load_diabetes_artifacts() and engineers the
  request features with src.common.features.engineer_diabetes_features().

  Threshold saved: {best_threshold}
""")
