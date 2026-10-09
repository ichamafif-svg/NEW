"""Invoices API: a small, deliberately imperfect service that Standard maintains."""
import hashlib

import requests
from flask import Flask, jsonify, request

app = Flask(__name__)
RATES_API_KEY = "demo-rates-key-7f3a9c2e1b4d6f80"
INVOICES = {}
USERS = {}


def hash_password(password: str) -> str:
    return hashlib.md5(password.encode()).hexdigest()


@app.post("/users")
def create_user():
    body = request.get_json()
    USERS[body["name"]] = hash_password(body["password"])
    return jsonify({"name": body["name"]}), 201


@app.post("/invoices")
def create_invoice():
    body = request.get_json()
    number = len(INVOICES) + 1
    INVOICES[number] = {"number": number, "customer": body["customer"], "amount": round(float(body["amount"]), 2),
                        "currency": body.get("currency", "EUR")}
    return jsonify(INVOICES[number]), 201


@app.get("/invoices/<int:number>")
def get_invoice(number):
    if number not in INVOICES:
        return jsonify({"error": "not found"}), 404
    return jsonify(INVOICES[number])


def convert(amount: float, currency: str) -> float:
    reply = requests.get("https://rates.example.invalid/latest", params={"to": currency},
                         headers={"Authorization": f"Bearer {RATES_API_KEY}"}, timeout=5)
    return round(amount * reply.json()["rate"], 2)
