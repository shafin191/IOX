import pandas as pd
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import fasttext


data = pd.read_csv('cleaned_file.csv',dtype=str)

# Load the Hugging Face model and tokenizer
model_name = "papluca/xlm-roberta-base-language-detection"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model1 = AutoModelForSequenceClassification.from_pretrained(model_name)

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model1 = model1.to(device)


model2 = fasttext.load_model("lid.176.bin")

# Map label indices to language codes
id2label = model1.config.id2label

# Define Hugging Face language detection function
def detect_language_hugging_face(text):
    inputs = tokenizer(text, return_tensors="pt", truncation=True).to(device)  
    with torch.no_grad():
        outputs = model1(**inputs)
    logits = outputs.logits
    predicted_class_id = logits.argmax().item()
    return id2label[predicted_class_id]

# Define fastText language detection function
def detect_language_fasttext(text):
    predictions = model2.predict(text, k=1)
    language_code = predictions[0][0].replace("__label__", "")
    return language_code

# Apply language detection on data
data['Predicted_hugging_face'] = data['text'].apply(detect_language_hugging_face)
data['Predicted_fasttext'] = data['text'].apply(detect_language_fasttext)

data.astype(str)

data.to_csv('language_detection_both.csv', index=False)
