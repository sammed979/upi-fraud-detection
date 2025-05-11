from flask import Flask, request, jsonify, render_template
import joblib
import pandas as pd
import os

app = Flask(__name__, template_folder="../templates")

# Correct paths
fraud_model_path = "D:/python/UPI_Fraud_Detection_Project/models/upi_fraud_model.pkl"
anomaly_model_path = "D:/python/UPI_Fraud_Detection_Project/models/anomaly_detection_model.pkl"

# Ensure models exist before loading
fraud_model = joblib.load(fraud_model_path) if os.path.exists(fraud_model_path) else None
anomaly_model = joblib.load(anomaly_model_path) if os.path.exists(anomaly_model_path) else None

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        if fraud_model is None or anomaly_model is None:
            return "⚠️ Models not loaded. Please check your model files.", 500

        data = {key: float(request.form[key]) for key in ['normalized_amount', 'transaction_count', 'merchant_id', 'user_id']}
        features = pd.DataFrame([data])

        fraud_prediction = fraud_model.predict(features)[0]
        anomaly_prediction = anomaly_model.predict(features)[0]

        result = {
            "fraud_prediction": "✅ This transaction looks safe!" if fraud_prediction == 1 else "⚠️ Be careful! This might be risky.",
            "anomaly_detection": "🚨 This transaction is unusual!" if anomaly_prediction == -1 else "✅ Everything seems normal.",
        }
        return render_template("index.html", result=result)

    return render_template("index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)