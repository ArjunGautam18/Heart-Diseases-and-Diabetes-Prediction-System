import pickle

with open("D:\\Desktop\\Diseases Prediction\\smart-healthcare-system\\models\\diabetes_features.pkl", "rb") as f:
    features = pickle.load(f)

with open("D:\\Desktop\\Diseases Prediction\\smart-healthcare-system\\models\\diabetes_features.txt", "w") as f:
    for feature in features:
        f.write(feature + "\n")