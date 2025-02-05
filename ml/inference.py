import pickle
import os

# Load model once at startup
MODEL_PATH = "ml/trained_model.pkl"
if os.path.exists(MODEL_PATH):
    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)
else:
    raise FileNotFoundError(f"Model file not found: {MODEL_PATH}")

def preprocess_data(data):
    """Extract and prepare features from the input dictionary."""
    mrn = data["PID"]
    timestamp = data["Latest_Result_Timestamp"]
    features = [data["Age"], data["Sex"], data["Mean"], data["Standard_Deviation"], data["Max"], data["Min"], data['Last_Result_Value']]
    return features, mrn, timestamp

def predict_aki(data):
    """
    Predict AKI using the pre-trained model.

    Args:
        data (dict): Input dictionary with required patient features.

    Returns:
        tuple: (prediction result, mrn, timestamp)
    """
    try:
        features, mrn, timestamp = preprocess_data(data)
        result = model.predict([features])  # Wrap in a list for model input
        return result, mrn, timestamp
    except Exception as e:
        print(f"[ml_inference] Prediction error: {e}")
        return None, None, None



