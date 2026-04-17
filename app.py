"""
app.py
------
UPI Shield AI - Flask Backend
Hybrid fraud scoring: Rule-based (60%) + ML model (40%)
"""

from flask import Flask, request, jsonify, render_template
from pathlib import Path
import pickle
import numpy as np
import re

from database import init_db, is_reported, report_upi, log_transaction, get_recent_logs

app = Flask(__name__)

# ── Load ML model ─────────────────────────────────────────────────────────────
MODEL_PATH = Path(__file__).parent / "model.pkl"
ml_model = None
if MODEL_PATH.exists():
    with open(MODEL_PATH, "rb") as f:
        ml_model = pickle.load(f)
    print("[OK] ML model loaded")
else:
    print("[WARN] model.pkl not found. Run: python model.py")

init_db()

# ── Purpose map ───────────────────────────────────────────────────────────────
PURPOSE_MAP = {
    "education":    0,
    "shopping":     1,
    "friend_family": 2,
    "unknown":      3,
}

# ── Helpers ───────────────────────────────────────────────────────────────────
def validate_upi(upi_id: str) -> bool:
    """Basic UPI ID format check: something@something"""
    return bool(re.match(r"^[\w.\-]+@[\w]+$", upi_id.strip()))

def rule_based_score(amount, purpose, is_new, reported) -> tuple[float, list]:
    """
    Returns (score, reasons_list)
    Reasons explain WHY the score is what it is.
    """
    score   = 0
    reasons = []

    # Risk factors
    if reported:
        score += 50
        reasons.append("This UPI ID has been reported for fraud")
    if is_new:
        score += 30
        reasons.append("First time paying this UPI ID")
    if amount > 10000:
        score += 20
        reasons.append(f"High amount (Rs.{amount:,.0f})")
    if purpose == "unknown":
        score += 25
        reasons.append("Purpose is unknown")

    # Trust factors
    if purpose == "education":
        score -= 20
        reasons.append("Education payments are generally safer")
    if not is_new:
        score -= 15
        reasons.append("Repeat receiver reduces risk")

    return float(np.clip(score, 0, 100)), reasons

def ml_score(amount, purpose, is_new, reported) -> float:
    """Returns ML fraud probability as 0-100 score."""
    if ml_model is None:
        return 0.0
    purpose_code = PURPOSE_MAP.get(purpose, 3)
    features     = np.array([[amount, int(is_new), purpose_code, int(reported)]])
    proba        = ml_model.predict_proba(features)[0][1]  # fraud probability
    return round(proba * 100, 1)

def risk_level(score: float) -> str:
    if score <= 40: return "SAFE"
    if score <= 70: return "SUSPICIOUS"
    return "HIGH RISK"

def build_explanation(reasons: list, risk: str) -> str:
    if not reasons:
        return "No significant risk factors detected."
    return " + ".join(reasons[:3]) + f" -> {risk} transaction"

# ── Routes ────────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    logs = get_recent_logs(10)
    return render_template("index.html", logs=logs)


@app.route("/analyze", methods=["POST"])
def analyze():
    """
    POST /analyze
    Body: { upi_id, amount, purpose, is_new_receiver }
    Returns: { risk_score, risk_level, explanation, rule_score, ml_score }
    """
    data = request.get_json()

    upi_id       = str(data.get("upi_id", "")).strip()
    amount       = float(data.get("amount", 0))
    purpose      = str(data.get("purpose", "unknown")).lower()
    is_new       = bool(data.get("is_new_receiver", True))

    # Validate
    if not upi_id:
        return jsonify({"error": "UPI ID is required"}), 400
    if not validate_upi(upi_id):
        return jsonify({"error": "Invalid UPI ID format (e.g. name@upi)"}), 400
    if amount <= 0:
        return jsonify({"error": "Amount must be greater than 0"}), 400

    # Check if reported
    reported = is_reported(upi_id)

    # Compute scores
    r_score, reasons = rule_based_score(amount, purpose, is_new, reported)
    m_score          = ml_score(amount, purpose, is_new, reported)

    # Hybrid final score
    final = round((r_score * 0.6) + (m_score * 0.4), 1)
    level = risk_level(final)
    explanation = build_explanation(reasons, level)

    # Log to DB
    log_transaction({
        "upi_id":       upi_id,
        "amount":       amount,
        "purpose":      purpose,
        "new_receiver": int(is_new),
        "rule_score":   r_score,
        "ml_score":     m_score,
        "final_score":  final,
        "risk_level":   level,
        "explanation":  explanation,
    })

    return jsonify({
        "risk_score":  final,
        "risk_level":  level,
        "explanation": explanation,
        "rule_score":  r_score,
        "ml_score":    m_score,
        "reported":    reported,
    })


@app.route("/report", methods=["POST"])
def report():
    """
    POST /report
    Body: { upi_id, reason }
    Saves UPI ID as fraudulent.
    """
    data   = request.get_json()
    upi_id = str(data.get("upi_id", "")).strip()
    reason = str(data.get("reason", "Reported by user"))

    if not upi_id or not validate_upi(upi_id):
        return jsonify({"error": "Valid UPI ID required"}), 400

    report_upi(upi_id, reason)
    return jsonify({"status": "reported", "upi_id": upi_id})


@app.route("/check/<upi_id>")
def check(upi_id):
    """
    GET /check/<upi_id>
    Returns whether a UPI ID is in the reported list.
    """
    reported = is_reported(upi_id)
    return jsonify({"upi_id": upi_id, "reported": reported})


@app.route("/logs")
def logs():
    rows = get_recent_logs(50)
    return jsonify([{
        "id":          r[0], "upi_id":      r[1],
        "amount":      r[2], "purpose":     r[3],
        "final_score": r[6], "risk_level":  r[7],
        "explanation": r[8], "checked_at":  r[9],
    } for r in rows])


if __name__ == "__main__":
    app.run(debug=True, port=5000)
