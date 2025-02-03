import pickle


def preprocess_data(data):
    #TODO: See if any pre processing needs to be done
    return data


def predict_aki(data):
    features = preprocess_data(data)

    # with open("/ml/trained_model.pkl", "rb") as f:
    #     model = pickle.load(f)
    
    # result = model.predict(features)
    result = 1
    return result, 32, 42



