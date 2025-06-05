import torch
import pandas as pd
from transformers import pipeline
from multiprocessing import cpu_count
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

# Setup devices and batch size
num_gpus = torch.cuda.device_count()
device_ids = list(range(1, num_gpus)) if num_gpus > 1 else [-1]
BATCH_SIZE = 128

# Load models
classifiers = [
    pipeline(
        "zero-shot-classification",
        model="mlburnham/Political_DEBATE_large_v1.0",
        device=device_id,
        batch_size=BATCH_SIZE
    ) for device_id in device_ids
]

# Load data
df = pd.read_csv("/aul/homes/msidd040/twikit/All_tweets/Analyzing_for_classification/only_english_tweets_simple.csv", dtype=str)
df = df.dropna(subset=["text"])
NUM_WORKERS = min(4, len(device_ids) * 2)

# Labels and templates
political_labels = ["Political", "Apolitical"]
political_template = "This text is {}."

domestic_foreign_labels = {
    "Domestic": "This text is about the United States.",
    "Foreign": "This text is about a country other than the United States."
}

stance_labels = {
    "Pro-D": "The author of this text supports Democrats.",
    "Anti-D": "The author of this text opposes Democrats.",
    "Pro-R": "The author of this text supports Republicans.",
    "Anti-R": "The author of this text opposes Republicans.",
    "Neutral": "The author of this text does not favor or oppose any political party."
}

@torch.no_grad()
def classify_batch(texts, classifier, labels, template):
    try:
        candidate_labels = list(labels.values()) if isinstance(labels, dict) else labels
        results = classifier(
            texts,
            candidate_labels=candidate_labels,
            hypothesis_template=template,
            multi_label=False
        )
        predicted_labels = [
            next((key for key, value in labels.items() if value == res["labels"][0]), res["labels"][0])
            if isinstance(labels, dict) else res["labels"][0]
            for res in results
        ]
        confidence_scores = [res["scores"][0] for res in results]
        return predicted_labels, confidence_scores
    except Exception as e:
        print(f"Error in classification: {e}")
        return ["Unknown"] * len(texts), [0.0] * len(texts)

def process_batches(texts, classify_function, labels, template, description="Processing"):
    labels_results = []
    confidence_results = []
    with ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
        futures = []
        for i in tqdm(range(0, len(texts), BATCH_SIZE), desc=description):
            batch = texts[i: i + BATCH_SIZE]
            classifier = classifiers[i % len(classifiers)]
            futures.append(executor.submit(classify_function, batch, classifier, labels, template))
        for future in tqdm(futures, desc="Merging Results"):
            batch_labels, batch_confidence = future.result()
            labels_results.extend(batch_labels)
            confidence_results.extend(batch_confidence)
    return labels_results, confidence_results

# Political vs Apolitical Classification
if "political_label" not in df.columns:
    print("Starting Political vs. Apolitical Classification...")
    df["political_label"], df["political_confidence"] = process_batches(
        df["text"].tolist(), classify_batch, political_labels, political_template, "Classifying Political vs Apolitical"
    )
    df.to_csv("/aul/homes/msidd040/twikit/All_tweets/Analyzing_for_classification/political_vs_apolitical_results.csv", index=False)

# Filter Political tweets
df_political = df[df["political_label"] == "Political"].copy()
if df_political.empty:
    print("No political tweets found. Skipping further classification.")
    exit()

# Domestic vs Foreign Classification
if "geo_category" not in df_political.columns:
    print("Starting Domestic vs. Foreign Classification...")
    df_political["geo_category"], df_political["geo_confidence"] = process_batches(
        df_political["text"].tolist(), classify_batch, domestic_foreign_labels, "{}", "Classifying Domestic vs Foreign"
    )
    df_political.to_csv("/aul/homes/msidd040/twikit/All_tweets/Analyzing_for_classification/domestic_foreign_results.csv", index=False)

# Stance Classification (for Domestic tweets)
df_domestic = df_political[df_political["geo_category"] == "Domestic"].copy()
if not df_domestic.empty and "stance" not in df_domestic.columns:
    print("Starting Stance Classification...")
    df_domestic["stance"], df_domestic["stance_confidence"] = process_batches(
        df_domestic["text"].tolist(), classify_batch, stance_labels, "{}", "Classifying Stance"
    )
    df_domestic.to_csv("/aul/homes/msidd040/twikit/All_tweets/Analyzing_for_classification/stance_results.csv", index=False)

    df_political = df_political.merge(
        df_domestic[["text", "stance", "stance_confidence"]],
        on="text",
        how="left"
    )

# Merge results back
df = df.merge(
    df_political[["text", "geo_category", "geo_confidence", "stance", "stance_confidence"]],
    on="text",
    how="left"
)

expected_columns = ["political_label", "political_confidence", "geo_category", "geo_confidence", "stance", "stance_confidence"]
for col in expected_columns:
    if col not in df.columns:
        df[col] = None

output_path = "/aul/homes/msidd040/twikit/All_tweets/Analyzing_for_classification/only_english_tweets_classification.csv"
df.to_csv(output_path, index=False)


