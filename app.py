import os
import subprocess
import tempfile
from flask import Flask, render_template, jsonify, request, send_file, after_this_request
from werkzeug.utils import secure_filename

app = Flask(__name__, template_folder="app/templates")

app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024

ALLOWED_EXTENSIONS = {"mp4", "mov", "mkv", "avi", "webm", "m4v"}


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


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
        "version": "2.0.0",
        "message": "Your content. Powered by AI."
    })


@app.post("/api/create-reel")
def create_reel():
    if "video" not in request.files:
        return jsonify({
            "error": "No video file uploaded"
        }), 400

    video = request.files["video"]

    if video.filename == "":
        return jsonify({
            "error": "No video selected"
        }), 400

    if not allowed_file(video.filename):
        return jsonify({
            "error": "Unsupported video format"
        }), 400

    input_file = None
    output_file = None

    try:
        extension = os.path.splitext(
            secure_filename(video.filename)
        )[1].lower()

        input_fd, input_file = tempfile.mkstemp(
            suffix=extension
        )
        os.close(input_fd)

        output_fd, output_file = tempfile.mkstemp(
            suffix=".mp4"
        )
        os.close(output_fd)

        video.save(input_file)

        command = [
            "ffmpeg",
            "-y",
            "-i",
            input_file,
            "-vf",
            "scale=1080:1920:force_original_aspect_ratio=increase,"
            "crop=1080:1920",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "23",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-movflags",
            "+faststart",
            output_file
        ]

        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        if result.returncode != 0:
            return jsonify({
                "error": "Video processing failed",
                "details": result.stderr[-1000:]
            }), 500

        @after_this_request
        def cleanup(response):
            for path in [input_file, output_file]:
                try:
                    if path and os.path.exists(path):
                        os.remove(path)
                except Exception:
                    pass
            return response

        return send_file(
            output_file,
            as_attachment=True,
            download_name="reelforge-reel.mp4",
            mimetype="video/mp4"
        )

    except Exception as e:
        for path in [input_file, output_file]:
            try:
                if path and os.path.exists(path):
                    os.remove(path)
            except Exception:
                pass

        return jsonify({
            "error": str(e)
        }), 500


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 10000))
        )
