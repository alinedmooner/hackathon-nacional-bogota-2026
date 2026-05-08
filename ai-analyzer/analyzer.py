import os
import time
import random
import numpy as np
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017")

def connect_mongo():
    client = MongoClient(MONGO_URI)
    return client["ai_analyzer"]

def generate_synthetic_image():
    return np.random.randint(0, 256, (224, 224, 3), dtype=np.uint8)

def analyze_image(image):
    mean_color = np.mean(image, axis=(0, 1))
    std_color = np.std(image, axis=(0, 1))
    brightness = np.mean(image)
    features = {
        "mean_r": float(mean_color[0]),
        "mean_g": float(mean_color[1]),
        "mean_b": float(mean_color[2]),
        "std_r": float(std_color[0]),
        "std_g": float(std_color[1]),
        "std_b": float(std_color[2]),
        "brightness": float(brightness),
        "entropy": random.uniform(0, 1)
    }
    return features

def simulate_deep_learning_inference():
    mock_predictions = {
        "class_scores": {f"class_{i}": random.random() for i in range(10)},
        "confidence": random.uniform(0.5, 0.99),
        "predicted_class": random.randint(0, 9)
    }
    return mock_predictions

def perform_analysis():
    print(f"[{datetime.now()}] Iniciando análisis de datos...")
    
    db = connect_mongo()
    collection = db["results"]
    
    image = generate_synthetic_image()
    image_features = analyze_image(image)
    ml_results = simulate_deep_learning_inference()
    
    result_document = {
        "timestamp": datetime.now(),
        "type": "image_analysis",
        "image_features": image_features,
        "ml_predictions": ml_results,
        "status": "completed",
        "processing_time_ms": random.randint(100, 2000)
    }
    
    insert_result = collection.insert_one(result_document)
    print(f"[{datetime.now()}] Resultado guardado con ID: {insert_result.inserted_id}")
    
    return result_document

def main():
    print("=" * 50)
    print("AI Analyzer - Servicio de Análisis de Datos")
    print(f"Conectando a MongoDB: {MONGO_URI}")
    print("=" * 50)
    
    while True:
        try:
            perform_analysis()
        except Exception as e:
            print(f"[{datetime.now()}] Error: {e}")
        
        print(f"[{datetime.now()}] Esperando 30 segundos...")
        time.sleep(30)

if __name__ == "__main__":
    main()