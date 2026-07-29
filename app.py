import io
import os
import uuid
import sqlite3
import mimetypes
from datetime import datetime

from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template, abort, send_file, redirect
from storage import create_storage

load_dotenv()

app = Flask(__name__)
ACCESS_CODE = os.environ.get("ACCESS_CODE", "123456")
DB_PATH = os.environ.get("DB_PATH", "data/files.db")
MAX_SIZE = int(os.environ.get("MAX_UPLOAD_SIZE", str(50 * 1024 * 1024)))

storage = create_storage()
os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    # files table
    conn.execute(
        "CREATE TABLE IF NOT EXISTS files ("
        "  id TEXT PRIMARY KEY,"
        "  filename TEXT NOT NULL,"
        "  upload_time TEXT NOT NULL,"
        "  size INTEGER NOT NULL,"
        "  folder_id TEXT DEFAULT NULL"
        ")"
    )
    # folders table
    conn.execute(
        "CREATE TABLE IF NOT EXISTS folders ("
        "  id TEXT PRIMARY KEY,"
        "  name TEXT NOT NULL,"
        "  parent_id TEXT DEFAULT NULL,"
        "  created_at TEXT NOT NULL"
        ")"
    )
    # compatibility: add folder_id column if missing (old db)
    try:
        conn.execute("ALTER TABLE files ADD COLUMN folder_id TEXT DEFAULT NULL")
    except sqlite3.OperationalError:
        pass  # column already exists
    conn.commit()
    return conn


def check_code():
    return request.headers.get("X-Access-Code") == ACCESS_CODE


def need_auth():
    return request.args.get("code") == ACCESS_CODE or check_code()


# ─────────────────── Routes ───────────────────


@app.route("/api/config", methods=["GET"])
def get_config():
    return jsonify({
        "max_upload_size": MAX_SIZE,
    })


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/verify", methods=["POST"])
def verify():
    data = request.get_json()
    if data and data.get("code") == ACCESS_CODE:
        return jsonify({"ok": True})
    return jsonify({"ok": False}), 403


# ───── Folders ─────


@app.route("/api/folders", methods=["GET"])
def list_folders():
    if not check_code():
        return jsonify({"ok": False}), 403
    parent = request.args.get("parent_id")  # null = root
    conn = get_db()
    if parent:
        rows = conn.execute(
            "SELECT * FROM folders WHERE parent_id = ? ORDER BY name",
            (parent,),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM folders WHERE parent_id IS NULL ORDER BY name"
        ).fetchall()
    conn.close()
    return jsonify({
        "ok": True,
        "folders": [
            {"id": r["id"], "name": r["name"], "parent_id": r["parent_id"], "created_at": r["created_at"]}
            for r in rows
        ],
    })


@app.route("/api/folders", methods=["POST"])
def create_folder():
    if not check_code():
        return jsonify({"ok": False}), 403
    data = request.get_json()
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"ok": False, "error": "Name required"}), 400
    parent_id = data.get("parent_id") or None
    folder_id = uuid.uuid4().hex[:12]
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    conn = get_db()
    conn.execute(
        "INSERT INTO folders (id, name, parent_id, created_at) VALUES (?, ?, ?, ?)",
        (folder_id, name, parent_id, now),
    )
    conn.commit()
    conn.close()
    return jsonify({"ok": True, "id": folder_id})


@app.route("/api/folders/<folder_id>", methods=["DELETE"])
def delete_folder(folder_id):
    if not check_code():
        return jsonify({"ok": False}), 403
    conn = get_db()
    all_ids = set()

    def collect(fid):
        all_ids.add(fid)
        children = conn.execute(
            "SELECT id FROM folders WHERE parent_id = ?", (fid,)
        ).fetchall()
        for c in children:
            collect(c["id"])

    collect(folder_id)

    placeholders = ",".join("?" for _ in all_ids)
    conn.execute(
        f"UPDATE files SET folder_id = NULL WHERE folder_id IN ({placeholders})",
        tuple(all_ids),
    )
    conn.execute(
        f"DELETE FROM folders WHERE id IN ({placeholders})",
        tuple(all_ids),
    )
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


# ───── Files ─────


@app.route("/api/files", methods=["GET"])
def list_files():
    if not check_code():
        return jsonify({"ok": False}), 403
    folder_id = request.args.get("folder_id") or None
    conn = get_db()
    if folder_id:
        rows = conn.execute(
            "SELECT * FROM files WHERE folder_id = ? ORDER BY upload_time DESC",
            (folder_id,),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM files WHERE folder_id IS NULL ORDER BY upload_time DESC"
        ).fetchall()
    conn.close()
    return jsonify({
        "ok": True,
        "files": [
            {"id": r["id"], "name": r["filename"], "time": r["upload_time"],
             "size": r["size"], "folder_id": r["folder_id"]}
            for r in rows
        ],
    })


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
    if len(data) == 0:
        return jsonify({"ok": False, "error": "Empty file"}), 400
    if len(data) > MAX_SIZE:
        return jsonify({"ok": False, "error": "File too large (max 50MB)"}), 400

    file_id = uuid.uuid4().hex[:12]
    orig_name = f.filename or "unnamed"
    folder_id = request.form.get("folder_id") or None

    storage.save(file_id, data)

    conn = get_db()
    conn.execute(
        "INSERT INTO files (id, filename, upload_time, size, folder_id) VALUES (?, ?, ?, ?, ?)",
        (file_id, orig_name, datetime.now().strftime("%Y-%m-%d %H:%M"), len(data), folder_id),
    )
    conn.commit()
    conn.close()
    return jsonify({"ok": True, "id": file_id})


@app.route("/api/file/<file_id>/move", methods=["PUT"])
def move_file(file_id):
    if not check_code():
        return jsonify({"ok": False}), 403
    data = request.get_json()
    folder_id = data.get("folder_id") or None

    conn = get_db()
    row = conn.execute("SELECT * FROM files WHERE id = ?", (file_id,)).fetchone()
    if not row:
        conn.close()
        return jsonify({"ok": False, "error": "Not found"}), 404
    conn.execute("UPDATE files SET folder_id = ? WHERE id = ?", (folder_id, file_id))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


@app.route("/api/file/<file_id>", methods=["GET"])
def download(file_id):
    inline = request.args.get("inline")
    if not need_auth():
        return abort(403)

    conn = get_db()
    row = conn.execute("SELECT * FROM files WHERE id = ?", (file_id,)).fetchone()
    conn.close()
    if not row:
        return abort(404)

    # OSS mode: sign URL and redirect (inline only works for local)
    if not inline:
        url = storage.get_url(file_id)
        if url:
            return redirect(url)

    local_data = storage.get_data(file_id)
    if local_data is None:
        return abort(404)

    filename = row["filename"]
    mimetype, _ = mimetypes.guess_type(filename)
    if not mimetype:
        mimetype = "application/octet-stream"

    return send_file(
        io.BytesIO(local_data),
        download_name=filename,
        as_attachment=not inline,
        mimetype=mimetype,
    )


TEXT_EXTS = {'txt','md','json','xml','yaml','yml','ini','cfg','log',
             'py','js','ts','html','css','sh','bat','ps1','csv','env','gitignore'}


@app.route("/api/file/<file_id>/content", methods=["PUT"])
def update_file_content(file_id):
    if not check_code():
        return jsonify({"ok": False}), 403

    data = request.get_json()
    content = data.get("content")
    if content is None:
        return jsonify({"ok": False, "error": "Content required"}), 400

    conn = get_db()
    row = conn.execute("SELECT * FROM files WHERE id = ?", (file_id,)).fetchone()
    if not row:
        conn.close()
        return jsonify({"ok": False, "error": "Not found"}), 404

    # only allow editing text files
    ext = row["filename"].rsplit(".", 1)[-1].lower() if "." in row["filename"] else ""
    if ext not in TEXT_EXTS:
        conn.close()
        return jsonify({"ok": False, "error": "Not a text file"}), 400

    new_data = content.encode("utf-8")
    storage.save(file_id, new_data)
    conn.execute(
        "UPDATE files SET size = ? WHERE id = ?",
        (len(new_data), file_id),
    )
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


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
    storage.delete(file_id)
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)