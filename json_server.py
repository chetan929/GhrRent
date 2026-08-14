import json
from flask import Flask, request, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

# Load db.json
DB_FILE = "db.json"


def load_db():
    """Load data from db.json"""
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    return {"tenants": [], "payments": [], "reminders": []}


def save_db(data):
    """Save data to db.json"""
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=2)


# Tenants endpoints
@app.route("/tenants", methods=["GET"])
def get_tenants():
    db = load_db()
    return jsonify(db.get("tenants", []))


@app.route("/tenants", methods=["POST"])
def add_tenant():
    db = load_db()
    data = request.get_json()
    tenants = db.get("tenants", [])

    # Generate new ID
    new_id = max([t.get("id", 0) for t in tenants], default=0) + 1
    data["id"] = new_id

    tenants.append(data)
    db["tenants"] = tenants
    save_db(db)

    return jsonify(data), 201


@app.route("/tenants/<int:tenant_id>", methods=["GET"])
def get_tenant(tenant_id):
    db = load_db()
    tenant = next((t for t in db.get("tenants", []) if t["id"] == tenant_id), None)
    if tenant:
        return jsonify(tenant)
    return jsonify({"error": "Tenant not found"}), 404


@app.route("/tenants/<int:tenant_id>", methods=["PUT"])
def update_tenant(tenant_id):
    db = load_db()
    tenants = db.get("tenants", [])
    tenant = next((t for t in tenants if t["id"] == tenant_id), None)

    if not tenant:
        return jsonify({"error": "Tenant not found"}), 404

    data = request.get_json()
    tenant.update(data)
    save_db(db)

    return jsonify(tenant)


@app.route("/tenants/<int:tenant_id>", methods=["DELETE"])
def delete_tenant(tenant_id):
    db = load_db()
    tenants = db.get("tenants", [])
    db["tenants"] = [t for t in tenants if t["id"] != tenant_id]
    save_db(db)

    return "", 204


# Payments endpoints
@app.route("/payments", methods=["GET"])
def get_payments():
    db = load_db()
    return jsonify(db.get("payments", []))


@app.route("/payments", methods=["POST"])
def add_payment():
    db = load_db()
    data = request.get_json()
    payments = db.get("payments", [])

    new_id = max([p.get("id", 0) for p in payments], default=0) + 1
    data["id"] = new_id

    payments.append(data)
    db["payments"] = payments
    save_db(db)

    return jsonify(data), 201


@app.route("/payments/<int:payment_id>", methods=["DELETE"])
def delete_payment(payment_id):
    db = load_db()
    payments = db.get("payments", [])
    db["payments"] = [p for p in payments if p["id"] != payment_id]
    save_db(db)

    return "", 204


# Reminders endpoints
@app.route("/reminders", methods=["GET"])
def get_reminders():
    db = load_db()
    return jsonify(db.get("reminders", []))


@app.route("/reminders", methods=["POST"])
def add_reminder():
    db = load_db()
    data = request.get_json()
    reminders = db.get("reminders", [])

    new_id = max([r.get("id", 0) for r in reminders], default=0) + 1
    data["id"] = new_id

    reminders.append(data)
    db["reminders"] = reminders
    save_db(db)

    return jsonify(data), 201


if __name__ == "__main__":
    print("JSON Server running on http://127.0.0.1:3000")
    app.run(debug=True, port=3000, host="127.0.0.1")
