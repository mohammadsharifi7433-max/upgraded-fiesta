import os
from flask import Flask, render_template, jsonify

app = Flask(__name__, template_folder="app/templates")


@app.get("/")
def home():
    return render_template("index.html")


@app.get("/api/health")
def health():
    return jsonify({
        "status": "ok",
        "service": "ReelForge AI"
    })


@app.get("/api/info")
def info():
    return jsonify({
        "name": "ReelForge AI",
        "version": "1.0.0",
        "message": "Your content. Powered by AI."
    })


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 10000))
    )
