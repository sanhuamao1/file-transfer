import os
import uuid
import sqlite3
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory, render_template, redirect, abort
from werkzeug.utils import secure_filename

app = Flask(__name__)
ACCESS_CODE = os.environ.get("ACCESS_CODE", "123456")
UPLOAD_DIR = os.environ.get("UPLOAD_DIR", "/app/files")
DB_PATH = os.environ.get("DB_PATH", "/app/data/files.db")
MAX_SIZE = 50 * 1024 * 1024  # 50MB

# OSS config
OSS_ENABLED = os.environ.get("OSS_ENABLED", "").lower() in ("1", "true", "yes")
OSS_ACCESS_KEY_ID = os.environ.get("OSS_ACCESS_KEY_ID", "")
OSS_ACCESS_KEY_SECRET = os.environ.get("OSS_ACCESS_KEY_SECRET", "")
OSS_BUCKET_NAME = os.environ.get("OSS_BUCKET_NAME", "")
OSS_ENDPOINT = os.environ.get("OSS_ENDPOINT", "")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

if OSS_ENABLED:
    import oss2
    _auth = oss2.Auth(OSS_ACCESS_KEY_ID, OSS_ACCESS_KEY_SECRET)
    _bucket = oss2.Bucket(_auth, OSS_ENDPOINT, OSS_BUCKET_NAME)


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute(
        "CREATE TABLE IF NOT EXISTS files ("
        "  id TEXT PRIMARY KEY,"
        "  filename TEXT NOT NULL,"
        "  upload_time TEXT NOT NULL,"
        "  size INTEGER NOT NULL"
        ")"
    )
    conn.commit()
    return conn


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/verify", methods=["POST"])
def verify():
    """Verify the access code."""
    data = request.get_json()
    if data and data.get("code") == ACCESS_CODE:
        return jsonify({"ok": True})
    return jsonify({"ok": False}), 403


def check_code():
    """Check X-Access-Code header."""
    return request.headers.get("X-Access-Code") == ACCESS_CODE


@app.route("/api/files", methods=["GET"])
def list_files():
    if not check_code():
        return jsonify({"ok": False}), 403
    conn = get_db()
    rows = conn.execute("SELECT * FROM files ORDER BY upload_time DESC").fetchall()
    conn.close()
    files = [
        {
            "id": r["id"],
            "name": r["filename"],
            "time": r["upload_time"],
            "size": r["size"],
        }
        for r in rows
    ]
    return jsonify({"ok": True, "files": files})


@app.route("/api/upload", methods=["POST"])
def upload():
    if not check_code():
        return jsonify({"ok": False}), 403
    if "file" not in request.files:
        return jsonify({"ok": False, "error": "No file"}), 400
    f = request.files["file"]
    if f.filename == "":
        return jsonify({"ok": False, "error": "No file"}), 400
    data = f.read()
    if len(data) > MAX_SIZE:
        return jsonify({"ok": False, "error": "File too large (max 50MB)"}), 400

    file_id = uuid.uuid4().hex[:12]
    orig_name = secure_filename(f.filename) or "unnamed"

    if OSS_ENABLED:
        _bucket.put_object(file_id, data)
    else:
        save_path = os.path.join(UPLOAD_DIR, file_id)
        with open(save_path, "wb") as out:
            out.write(data)

    conn = get_db()
    conn.execute(
        "INSERT INTO files (id, filename, upload_time, size) VALUES (?, ?, ?, ?)",
        (file_id, orig_name, datetime.now().strftime("%Y-%m-%d %H:%M"), len(data)),
    )
    conn.commit()
    conn.close()
    return jsonify({"ok": True, "id": file_id})


@app.route("/api/file/<file_id>", methods=["GET"])
def download(file_id):
    code_ok = request.args.get("code") == ACCESS_CODE
    header_ok = check_code()
    if not code_ok and not header_ok:
        return abort(403)

    conn = get_db()
    row = conn.execute("SELECT * FROM files WHERE id = ?", (file_id,)).fetchone()
    conn.close()
    if not row:
        return abort(404)

    if OSS_ENABLED:
        url = _bucket.sign_url("GET", file_id, 300)
        return redirect(url)

    path = os.path.join(UPLOAD_DIR, file_id)
    if not os.path.exists(path):
        return abort(404)
    return send_from_directory(UPLOAD_DIR, file_id, as_attachment=True, download_name=row["filename"])


@app.route("/api/file/<file_id>", methods=["DELETE"])
def delete(file_id):
    if not check_code():
        return jsonify({"ok": False}), 403
    conn = get_db()
    row = conn.execute("SELECT * FROM files WHERE id = ?", (file_id,)).fetchone()
    if not row:
        conn.close()
        return jsonify({"ok": False, "error": "Not found"}), 404
    conn.execute("DELETE FROM files WHERE id = ?", (file_id,))
    conn.commit()
    conn.close()

    if OSS_ENABLED:
        _bucket.delete_object(file_id)
    else:
        path = os.path.join(UPLOAD_DIR, file_id)
        if os.path.exists(path):
            os.remove(path)
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
