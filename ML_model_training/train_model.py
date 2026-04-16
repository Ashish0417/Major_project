# # ============================================
# # COMPLETE PIPELINE TO TRAIN RANDOM FOREST MODEL
# # Project: Travel Feedback → Weight Predictor
# # Input : feedback text
# # Output: cost, time, pref, pop
# # ============================================

# # INSTALL FIRST:
# # pip install pandas numpy scikit-learn sentence-transformers joblib

# import pandas as pd
# import numpy as np
# import joblib

# from sentence_transformers import SentenceTransformer

# from sklearn.model_selection import train_test_split
# from sklearn.multioutput import MultiOutputRegressor
# from sklearn.ensemble import RandomForestRegressor
# from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# # ============================================
# # STEP 1: LOAD DATASET
# # ============================================

# df = pd.read_csv("ML_model_training/travel_feedback_10000_clean_rf.csv")

# print("Dataset Shape:", df.shape)
# print(df.head())

# # --------------------------------------------
# # Expected columns:
# # feedback, cost, time, pref, pop
# # --------------------------------------------

# # ============================================
# # STEP 2: INPUT + TARGETS
# # ============================================

# texts = df["feedback"].astype(str).tolist()

# y = df[["cost", "time", "pref", "pop"]].values

# # ============================================
# # STEP 3: LOAD SENTENCE TRANSFORMER
# # ============================================

# print("\nLoading SentenceTransformer...")

# embedder = SentenceTransformer("all-MiniLM-L6-v2")

# # ============================================
# # STEP 4: CREATE EMBEDDINGS
# # ============================================

# print("Generating embeddings...")

# X = embedder.encode(
#     texts,
#     batch_size=32,
#     show_progress_bar=True,
#     convert_to_numpy=True,
#     normalize_embeddings=True
# )

# print("Embedding Shape:", X.shape)   # (10000, 384)

# # ============================================
# # STEP 5: TRAIN TEST SPLIT
# # ============================================

# X_train, X_test, y_train, y_test = train_test_split(
#     X,
#     y,
#     test_size=0.2,
#     random_state=42
# )

# print("Train Shape:", X_train.shape)
# print("Test Shape :", X_test.shape)

# # ============================================
# # STEP 6: RANDOM FOREST MODEL
# # ============================================

# rf = RandomForestRegressor(
#     n_estimators=300,
#     max_depth=20,
#     min_samples_split=3,
#     min_samples_leaf=1,
#     n_jobs=-1,
#     random_state=42
# )

# model = MultiOutputRegressor(rf)

# # ============================================
# # STEP 7: TRAIN MODEL
# # ============================================

# print("\nTraining Random Forest...")

# model.fit(X_train, y_train)

# print("Training Complete.")

# # ============================================
# # STEP 8: EVALUATION
# # ============================================

# pred = model.predict(X_test)

# mae = mean_absolute_error(y_test, pred)
# rmse = np.sqrt(mean_squared_error(y_test, pred))
# r2 = r2_score(y_test, pred)

# print("\n========== RESULTS ==========")
# print("MAE :", round(mae, 4))
# print("RMSE:", round(rmse, 4))
# print("R2  :", round(r2, 4))

# # Individual target scores
# targets = ["cost", "time", "pref", "pop"]

# for i, t in enumerate(targets):
#     r2_ind = r2_score(y_test[:, i], pred[:, i])
#     print(f"{t} R2: {round(r2_ind,4)}")

# # ============================================
# # STEP 9: SAVE MODEL
# # ============================================

# joblib.dump(model, "rf_feedback_model.pkl")
# joblib.dump(embedder, "sentence_transformer.pkl")

# print("\nModel Saved:")
# print("rf_feedback_model.pkl")

# # ============================================
# # STEP 10: PREDICTION FUNCTION
# # ============================================

# def predict_feedback(text):
#     vec = embedder.encode(
#         [text],
#         convert_to_numpy=True,
#         normalize_embeddings=True
#     )

#     out = model.predict(vec)[0]

#     result = {
#         "cost": round(float(out[0]), 3),
#         "time": round(float(out[1]), 3),
#         "pref": round(float(out[2]), 3),
#         "pop":  round(float(out[3]), 3)
#     }

#     return result

# # ============================================
# # STEP 11: TEST LIVE PREDICTION
# # ============================================

# sample = "Trip was expensive and too hectic but loved hidden gems"

# print("\nSample Input:")
# print(sample)

# print("\nPrediction:")
# print(predict_feedback(sample))
# ==========================================================
# COMPARE 3 MODELS FOR TEXT FEEDBACK REGRESSION
# RandomForest vs XGBoost vs CatBoost
# Input : feedback text
# Output: cost, time, pref, pop
# ==========================================================

# INSTALL FIRST:
# pip install pandas numpy scikit-learn sentence-transformers xgboost catboost joblib

# import pandas as pd
# import numpy as np
# import warnings
# warnings.filterwarnings("ignore")

# from sentence_transformers import SentenceTransformer

# from sklearn.model_selection import train_test_split
# from sklearn.multioutput import MultiOutputRegressor
# from sklearn.metrics import (
#     mean_absolute_error,
#     mean_squared_error,
#     r2_score
# )

# from sklearn.ensemble import RandomForestRegressor
# from xgboost import XGBRegressor
# from catboost import CatBoostRegressor

# # ==========================================================
# # STEP 1: LOAD DATASET
# # ==========================================================

# df = pd.read_csv("ML_model_training/travel_feedback_10000_clean_rf.csv")

# print("Dataset Loaded:", df.shape)

# # Expected columns:
# # feedback, cost, time, pref, pop

# texts = df["feedback"].astype(str).tolist()
# y = df[["cost", "time", "pref", "pop"]].values

# # ==========================================================
# # STEP 2: EMBEDDINGS
# # ==========================================================

# print("\nLoading SentenceTransformer...")
# embedder = SentenceTransformer("all-MiniLM-L6-v2")

# print("Generating embeddings...")
# X = embedder.encode(
#     texts,
#     batch_size=32,
#     show_progress_bar=True,
#     convert_to_numpy=True,
#     normalize_embeddings=True
# )

# print("Embeddings Shape:", X.shape)

# # ==========================================================
# # STEP 3: TRAIN TEST SPLIT
# # ==========================================================

# X_train, X_test, y_train, y_test = train_test_split(
#     X,
#     y,
#     test_size=0.20,
#     random_state=42
# )

# print("\nTrain:", X_train.shape)
# print("Test :", X_test.shape)

# # ==========================================================
# # STEP 4: DEFINE MODELS
# # ==========================================================

# models = {

#     "RandomForest": MultiOutputRegressor(
#         RandomForestRegressor(
#             n_estimators=300,
#             max_depth=20,
#             min_samples_split=3,
#             min_samples_leaf=1,
#             n_jobs=-1,
#             random_state=42
#         )
#     ),

#     "XGBoost": MultiOutputRegressor(
#         XGBRegressor(
#             n_estimators=400,
#             max_depth=8,
#             learning_rate=0.05,
#             subsample=0.85,
#             colsample_bytree=0.85,
#             objective="reg:squarederror",
#             random_state=42,
#             n_jobs=-1
#         )
#     ),

#     "CatBoost": MultiOutputRegressor(
#         CatBoostRegressor(
#             iterations=400,
#             depth=8,
#             learning_rate=0.05,
#             loss_function="RMSE",
#             verbose=0,
#             random_seed=42
#         )
#     )
# }

# # ==========================================================
# # STEP 5: TRAIN + EVALUATE
# # ==========================================================

# results = []

# targets = ["cost", "time", "pref", "pop"]

# for name, model in models.items():

#     print(f"\n==============================")
#     print(f"Training {name}")
#     print(f"==============================")

#     model.fit(X_train, y_train)

#     pred = model.predict(X_test)

#     mae = mean_absolute_error(y_test, pred)
#     rmse = np.sqrt(mean_squared_error(y_test, pred))
#     r2 = r2_score(y_test, pred)

#     print(f"\n{name} Results")
#     print("MAE :", round(mae, 4))
#     print("RMSE:", round(rmse, 4))
#     print("R2  :", round(r2, 4))

#     per_target = []

#     for i, t in enumerate(targets):
#         r2_ind = r2_score(y_test[:, i], pred[:, i])
#         per_target.append(round(r2_ind, 4))
#         print(f"{t} R2: {round(r2_ind,4)}")

#     results.append({
#         "Model": name,
#         "MAE": round(mae, 4),
#         "RMSE": round(rmse, 4),
#         "R2": round(r2, 4),
#         "cost_R2": per_target[0],
#         "time_R2": per_target[1],
#         "pref_R2": per_target[2],
#         "pop_R2": per_target[3]
#     })

# # ==========================================================
# # STEP 6: FINAL COMPARISON TABLE
# # ==========================================================

# results_df = pd.DataFrame(results)

# print("\n\n======================================")
# print("FINAL MODEL COMPARISON")
# print("======================================")
# print(results_df.sort_values("R2", ascending=False))

# # ==========================================================
# # STEP 7: BEST MODEL
# # ==========================================================

# best_model_name = results_df.sort_values("R2", ascending=False).iloc[0]["Model"]

# print(f"\nBest Model = {best_model_name}")

# # ==========================================================
# # OPTIONAL: LIVE TEST WITH BEST MODEL
# # ==========================================================

# # Refit best model
# best_model = models[best_model_name]
# best_model.fit(X_train, y_train)

# def predict_feedback(text):
#     vec = embedder.encode(
#         [text],
#         convert_to_numpy=True,
#         normalize_embeddings=True
#     )

#     out = best_model.predict(vec)[0]

#     return {
#         "cost": round(float(out[0]),3),
#         "time": round(float(out[1]),3),
#         "pref": round(float(out[2]),3),
#         "pop": round(float(out[3]),3)
#     }

# sample = "Trip was expensive and too rushed but I loved hidden gems"

# print("\nSample Input:")
# print(sample)

# print("\nPrediction:")
# print(predict_feedback(sample))
# ==========================================================
# FULL UPDATED TRAINING PIPELINE
# Saves:
#   ✅ Best model (.pkl)
#   ✅ Comparison CSV
#   ✅ Evaluation TXT report
#   ✅ Metadata JSON
#   ✅ Sample prediction JSON
# Ready for deployment
# ==========================================================

# INSTALL:
# pip install pandas numpy scikit-learn sentence-transformers xgboost catboost joblib

import os
import json
import joblib
import warnings
import pandas as pd
import numpy as np

from datetime import datetime

warnings.filterwarnings("ignore")

from sentence_transformers import SentenceTransformer

from sklearn.model_selection import train_test_split
from sklearn.multioutput import MultiOutputRegressor
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score
)

from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor
from catboost import CatBoostRegressor

# ==========================================================
# CONFIG
# ==========================================================

DATASET_PATH = "ML_model_training/travel_feedback_10000_clean_rf.csv"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
OUTPUT_DIR = "saved_feedback_model"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ==========================================================
# STEP 1: LOAD DATA
# ==========================================================

print("Loading dataset...")

df = pd.read_csv(DATASET_PATH)

print("Dataset Shape:", df.shape)

texts = df["feedback"].astype(str).tolist()
y = df[["cost", "time", "pref", "pop"]].values

targets = ["cost", "time", "pref", "pop"]

# ==========================================================
# STEP 2: LOAD EMBEDDING MODEL
# ==========================================================

print("\nLoading SentenceTransformer...")
embedder = SentenceTransformer(EMBEDDING_MODEL)

# ==========================================================
# STEP 3: GENERATE EMBEDDINGS
# ==========================================================

print("Generating embeddings...")

X = embedder.encode(
    texts,
    batch_size=32,
    show_progress_bar=True,
    convert_to_numpy=True,
    normalize_embeddings=True
)

print("Embedding Shape:", X.shape)

# Save embeddings optional
np.save(os.path.join(OUTPUT_DIR, "X_embeddings.npy"), X)

# ==========================================================
# STEP 4: TRAIN TEST SPLIT
# ==========================================================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42
)

print("\nTrain Shape:", X_train.shape)
print("Test Shape :", X_test.shape)

# ==========================================================
# STEP 5: DEFINE MODELS
# ==========================================================

models = {

    "RandomForest": MultiOutputRegressor(
        RandomForestRegressor(
            n_estimators=300,
            max_depth=20,
            min_samples_split=3,
            min_samples_leaf=1,
            n_jobs=-1,
            random_state=42
        )
    ),

    "XGBoost": MultiOutputRegressor(
        XGBRegressor(
            n_estimators=400,
            max_depth=8,
            learning_rate=0.05,
            subsample=0.85,
            colsample_bytree=0.85,
            objective="reg:squarederror",
            random_state=42,
            n_jobs=-1
        )
    ),

    "CatBoost": MultiOutputRegressor(
        CatBoostRegressor(
            iterations=400,
            depth=8,
            learning_rate=0.05,
            loss_function="RMSE",
            verbose=0,
            random_seed=42
        )
    )
}

# ==========================================================
# STEP 6: TRAIN + EVALUATE
# ==========================================================

results = {}
comparison_rows = []

best_r2 = -999
best_model = None
best_model_name = None
best_predictions = None

for name, model in models.items():

    print("\n===================================")
    print("Training:", name)
    print("===================================")

    model.fit(X_train, y_train)

    pred = model.predict(X_test)

    mae = mean_absolute_error(y_test, pred)
    rmse = np.sqrt(mean_squared_error(y_test, pred))
    r2 = r2_score(y_test, pred)

    per_target = {}

    for i, t in enumerate(targets):
        per_target[t] = round(
            r2_score(y_test[:, i], pred[:, i]), 4
        )

    results[name] = {
        "MAE": round(float(mae), 4),
        "RMSE": round(float(rmse), 4),
        "R2": round(float(r2), 4),
        "per_target_r2": per_target
    }

    comparison_rows.append({
        "Model": name,
        "MAE": round(float(mae), 4),
        "RMSE": round(float(rmse), 4),
        "R2": round(float(r2), 4),
        "cost_R2": per_target["cost"],
        "time_R2": per_target["time"],
        "pref_R2": per_target["pref"],
        "pop_R2": per_target["pop"]
    })

    print("MAE :", round(mae, 4))
    print("RMSE:", round(rmse, 4))
    print("R2  :", round(r2, 4))

    if r2 > best_r2:
        best_r2 = r2
        best_model = model
        best_model_name = name
        best_predictions = pred

# ==========================================================
# STEP 7: SAVE COMPARISON CSV
# ==========================================================

comparison_df = pd.DataFrame(comparison_rows)
comparison_df = comparison_df.sort_values("R2", ascending=False)

comparison_csv_path = os.path.join(OUTPUT_DIR, "model_comparison.csv")
comparison_df.to_csv(comparison_csv_path, index=False)

# ==========================================================
# STEP 8: SAVE BEST MODEL
# ==========================================================

best_model_path = os.path.join(OUTPUT_DIR, "best_feedback_model.pkl")
joblib.dump(best_model, best_model_path)

# ==========================================================
# STEP 9: SAVE METADATA JSON
# ==========================================================

metadata = {
    "best_model": best_model_name,
    "best_r2": round(float(best_r2), 4),
    "embedding_model": EMBEDDING_MODEL,
    "dataset_path": DATASET_PATH,
    "dataset_rows": int(len(df)),
    "feature_dimension": int(X.shape[1]),
    "train_size": int(len(X_train)),
    "test_size": int(len(X_test)),
    "created_at": str(datetime.now())
}

metadata_path = os.path.join(OUTPUT_DIR, "metadata.json")

with open(metadata_path, "w") as f:
    json.dump(metadata, f, indent=4)

# ==========================================================
# STEP 10: SAVE TXT REPORT
# ==========================================================

report_path = os.path.join(OUTPUT_DIR, "evaluation_report.txt")

with open(report_path, "w") as f:

    f.write("TRAVEL FEEDBACK MODEL REPORT\n")
    f.write("=" * 50 + "\n\n")

    f.write("Created At: " + str(datetime.now()) + "\n")
    f.write("Dataset: " + DATASET_PATH + "\n")
    f.write("Embedding Model: " + EMBEDDING_MODEL + "\n\n")

    f.write("BEST MODEL: " + best_model_name + "\n")
    f.write("BEST R2   : " + str(round(best_r2, 4)) + "\n\n")

    f.write("FULL COMPARISON:\n")
    f.write(comparison_df.to_string(index=False))
    f.write("\n")

# ==========================================================
# STEP 11: SAMPLE PREDICTION SAVE
# ==========================================================

def predict_feedback(text):

    vec = embedder.encode(
        [text],
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    out = best_model.predict(vec)[0]

    return {
        "input_text": text,
        "cost": round(float(out[0]), 3),
        "time": round(float(out[1]), 3),
        "pref": round(float(out[2]), 3),
        "pop": round(float(out[3]), 3)
    }

sample = "Trip was expensive and too rushed but I loved hidden gems"

sample_result = predict_feedback(sample)

sample_json_path = os.path.join(OUTPUT_DIR, "sample_prediction.json")

with open(sample_json_path, "w") as f:
    json.dump(sample_result, f, indent=4)

# ==========================================================
# FINAL OUTPUT
# ==========================================================

print("\n======================================")
print("TRAINING COMPLETE")
print("======================================")
print("Best Model :", best_model_name)
print("Best R2    :", round(best_r2, 4))

print("\nSaved Files:")
print("1.", best_model_path)
print("2.", comparison_csv_path)
print("3.", report_path)
print("4.", metadata_path)
print("5.", sample_json_path)
print("6.", os.path.join(OUTPUT_DIR, "X_embeddings.npy"))

print("\nSample Prediction:")
print(sample_result)