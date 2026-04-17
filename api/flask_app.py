from flask import Flask, request, jsonify, render_template, send_file
import joblib
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import io
import sys

# ── paths ──────────────────────────────────────────────────────────────────────
BASE_DIR  = Path(__file__).resolve().parent.parent
MODEL_DIR = BASE_DIR / "models"
sys.path.insert(0, str(BASE_DIR / "api"))

from database import init_db, save_transaction, get_all_transactions, get_stats
import razorpay
import hmac
import hashlib

# ── Razorpay credentials — ADD YOUR KEYS HERE ─────────────────────────────────
RAZORPAY_KEY_ID     = "rzp_test_SeC6p1AtAGfirl"   # <-- paste your Key ID here
RAZORPAY_KEY_SECRET = "p5XJQ2akIhtpE3SbICrlzkw8"    # <-- paste your Key Secret here
RAZORPAY_WEBHOOK_SECRET = "$@mmedP1022*" # <-- paste your Webhook Secret here
# ──────────────────────────────────────────────────────────────────────────────

razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

app = Flask(
    __name__,
    template_folder=str(BASE_DIR / "templates"),
    static_folder=str(BASE_DIR / "static")
)

# ── load models ────────────────────────────────────────────────────────────────
def _load(path):
    return joblib.load(path) if path.exists() else None

fraud_model   = _load(MODEL_DIR / "upi_fraud_model.pkl")
anomaly_model = _load(MODEL_DIR / "anomaly_detection_model.pkl")
scaler        = _load(MODEL_DIR / "amount_scaler.pkl")

init_db()

FEATURES = ["normalized_amount", "transaction_count", "merchant_id", "user_id", "hour_of_day"]

# ── helpers ────────────────────────────────────────────────────────────────────
def compute_fraud_score(fraud_proba, anomaly_pred):
    """Combine model probability + anomaly signal into 0-100 score."""
    base  = fraud_proba * 80
    bonus = 20 if anomaly_pred == -1 else 0
    return round(min(base + bonus, 100), 1)

def risk_label(score):
    if score >= 70: return "HIGH"
    if score >= 40: return "MEDIUM"
    return "LOW"

def predict(amount, transaction_count, merchant_id, user_id, hour_of_day):
    if not fraud_model or not anomaly_model or not scaler:
        return None, None, None, None

    norm_amount = float(scaler.transform([[amount]])[0][0])
    features    = pd.DataFrame([[norm_amount, transaction_count, merchant_id, user_id, hour_of_day]],
                                columns=FEATURES)

    fraud_pred   = int(fraud_model.predict(features)[0])          # 1=fraud, 0=legit
    fraud_proba  = float(fraud_model.predict_proba(features)[0][1])
    anomaly_pred = int(anomaly_model.predict(features)[0])         # -1=anomaly, 1=normal
    score        = compute_fraud_score(fraud_proba, anomaly_pred)
    return fraud_pred, anomaly_pred, score, norm_amount

# ── routes ─────────────────────────────────────────────────────────────────────
@app.route("/", methods=["GET", "POST"])
def home():
    result = None
    error  = None

    if request.method == "POST":
        if not fraud_model or not anomaly_model:
            error = "Models not loaded. Run the training scripts first."
        else:
            try:
                amount            = float(request.form["transaction_amount"])
                transaction_count = int(request.form["transaction_count"])
                merchant_id       = int(request.form["merchant_id"])
                user_id           = int(request.form["user_id"])
                hour_of_day       = int(request.form["hour_of_day"])

                fraud_pred, anomaly_pred, score, norm_amount = predict(
                    amount, transaction_count, merchant_id, user_id, hour_of_day
                )

                risk = risk_label(score)

                save_transaction({
                    "user_id":             user_id,
                    "merchant_id":         merchant_id,
                    "transaction_amount":  amount,
                    "hour_of_day":         hour_of_day,
                    "normalized_amount":   norm_amount,
                    "transaction_count":   transaction_count,
                    "fraud_prediction":    fraud_pred,
                    "anomaly_prediction":  anomaly_pred,
                    "fraud_score":         score,
                    "risk_level":          risk,
                    "source":              "manual",
                    "razorpay_payment_id": None,
                })

                result = {
                    "fraud_prediction":  fraud_pred,
                    "anomaly_prediction": anomaly_pred,
                    "fraud_score":       score,
                    "risk_level":        risk,
                    "amount":            amount,
                    "fraud_label":       "FRAUD DETECTED" if fraud_pred == 1 else "Transaction Safe",
                    "anomaly_label":     "Unusual Pattern" if anomaly_pred == -1 else "Normal Pattern",
                }
            except (ValueError, KeyError) as e:
                error = f"Invalid input: {e}"

    stats        = get_stats()
    transactions = get_all_transactions(20)
    last_id      = transactions[0][0] if transactions else None
    return render_template("index.html", result=result, error=error,
                           transactions=transactions, stats=stats, last_id=last_id)


@app.route("/history")
def history():
    transactions = get_all_transactions(100)
    return render_template("history.html", transactions=transactions)


@app.route("/report/<int:txn_id>")
def download_report(txn_id):
    """Generate a PDF fraud report for a transaction."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas as rl_canvas
    except ImportError:
        return "reportlab not installed. Run: pip install reportlab", 500

    from database import get_connection
    conn = get_connection()
    row  = conn.execute("SELECT * FROM transactions WHERE id=?", (txn_id,)).fetchone()
    conn.close()

    if not row:
        return "Transaction not found", 404

    buf = io.BytesIO()
    c   = rl_canvas.Canvas(buf, pagesize=A4)
    w, h = A4

    c.setFont("Helvetica-Bold", 18)
    c.drawString(50, h - 60, "UPI Fraud Detection — Transaction Report")
    c.setFont("Helvetica", 12)
    c.drawString(50, h - 90, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    c.line(50, h - 100, w - 50, h - 100)

    fields = [
        ("Transaction ID",    row[0]),
        ("User ID",           row[1]),
        ("Merchant ID",       row[2]),
        ("Amount (₹)",        f"{row[3]:,.2f}"),
        ("Hour of Day",       row[4]),
        ("Fraud Prediction",  "FRAUD" if row[7] == 1 else "SAFE"),
        ("Anomaly Detection", "ANOMALY" if row[8] == -1 else "NORMAL"),
        ("Fraud Score",       f"{row[9]}/100"),
        ("Risk Level",        row[10]),
        ("Source",            row[11]),
        ("Razorpay ID",       row[12] or "N/A"),
        ("Timestamp",         row[13]),
    ]

    y = h - 130
    for label, value in fields:
        c.setFont("Helvetica-Bold", 11)
        c.drawString(60, y, f"{label}:")
        c.setFont("Helvetica", 11)
        c.drawString(220, y, str(value))
        y -= 25

    # Risk colour box
    risk = row[10]
    colour = (0.8, 0.1, 0.1) if risk == "HIGH" else (0.9, 0.6, 0.0) if risk == "MEDIUM" else (0.1, 0.7, 0.1)
    c.setFillColorRGB(*colour)
    c.roundRect(50, y - 40, 200, 35, 8, fill=1, stroke=0)
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(80, y - 22, f"RISK LEVEL: {risk}")

    c.save()
    buf.seek(0)
    return send_file(buf, mimetype="application/pdf",
                     download_name=f"fraud_report_{txn_id}.pdf")


# ── Razorpay webhook ──────────────────────────────────────────────────────────
@app.route("/webhook/razorpay", methods=["POST"])
def razorpay_webhook():
    # 1. Verify webhook signature
    webhook_body      = request.get_data()
    webhook_signature = request.headers.get("X-Razorpay-Signature", "")

    expected = hmac.new(
        RAZORPAY_WEBHOOK_SECRET.encode(),
        webhook_body,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected, webhook_signature):
        return jsonify({"error": "Invalid signature"}), 400

    # 2. Parse payment data
    payload = request.get_json(force=True)
    event   = payload.get("event", "")

    if event not in ("payment.captured", "payment.failed"):
        return jsonify({"status": "ignored"}), 200

    payment = payload["payload"]["payment"]["entity"]

    payment_id = payment.get("id", "")
    amount     = payment.get("amount", 0) / 100        # Razorpay sends paise
    user_id    = abs(hash(payment.get("contact", "0"))) % 1000
    merchant_id = abs(hash(payment.get("description", "0"))) % 200
    hour_of_day = datetime.now().hour

    # 3. Get user transaction count from DB
    from database import get_connection
    conn  = get_connection()
    count = conn.execute(
        "SELECT COUNT(*) FROM transactions WHERE user_id=?", (user_id,)
    ).fetchone()[0] + 1
    conn.close()

    # 4. Run fraud prediction
    fraud_pred, anomaly_pred, score, norm_amount = predict(
        amount, count, merchant_id, user_id, hour_of_day
    )
    risk = risk_label(score)

    # 5. Save to DB
    save_transaction({
        "user_id":             user_id,
        "merchant_id":         merchant_id,
        "transaction_amount":  amount,
        "hour_of_day":         hour_of_day,
        "normalized_amount":   norm_amount,
        "transaction_count":   count,
        "fraud_prediction":    fraud_pred,
        "anomaly_prediction":  anomaly_pred,
        "fraud_score":         score,
        "risk_level":          risk,
        "source":              "razorpay",
        "razorpay_payment_id": payment_id,
    })

    return jsonify({
        "status":       "processed",
        "payment_id":   payment_id,
        "fraud_score":  score,
        "risk_level":   risk,
    }), 200


@app.route("/api/stats")
def api_stats():
    return jsonify(get_stats())


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
