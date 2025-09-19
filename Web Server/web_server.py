"""
Web Server: static files + upload + gallery
------------------------------------------
- Serves files from 'public/'.
- Upload form at /upload (POST multipart/form-data).
- Uploaded files are saved to 'uploads/'.
- Gallery at /gallery lists upload files with download links.
- Uses dynamic port assignment.
"""

import socket
import os
import mimetypes
import urllib.parse

HOST = "127.0.0.1"
PORT = 0  # OS picks free port
BASE_DIR = os.path.dirname(__file__)
WEB_ROOT = os.path.join(BASE_DIR, "public")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
BUFFER_SIZE = 8192


def ensure_dirs():
    os.makedirs(WEB_ROOT, exist_ok=True)
    os.makedirs(UPLOAD_DIR, exist_ok=True)


def guess_mime(path: str) -> str:
    m, _ = mimetypes.guess_type(path)
    return m or "application/octet-stream"


def read_request(client: socket.socket) -> bytes:
    """
    Read the incoming HTTP request header (until double CRLF).
    Returns raw header bytes. For POST uploads we will read additional body separately.
    """
    data = b""
    while b"\r\n\r\n" not in data:
        chunk = client.recv(1024)
        if not chunk:
            break
        data += chunk
    return data


def parse_headers(header_bytes: bytes) -> dict:
    text = header_bytes.decode("utf-8", errors="ignore")
    lines = text.split("\r\n")
    request_line = lines[0] if lines else ""
    headers = {}
    for line in lines[1:]:
        if ":" in line:
            k, v = line.split(":", 1)
            headers[k.strip().lower()] = v.strip()
    return {"request_line": request_line, "headers": headers, "raw": text}


def send_response(client: socket.socket, status: str, content: bytes, content_type: str = "text/html"):
    headers = (
        f"HTTP/1.1 {status}\r\n"
        f"Content-Type: {content_type}\r\n"
        f"Content-Length: {len(content)}\r\n"
        "Connection: close\r\n"
        "\r\n"
    ).encode("utf-8")
    client.sendall(headers + content)


def handle_get(path: str, client: socket.socket):
    if path == "/":
        path = "/index.html"
    if path == "/gallery":
        files = os.listdir(UPLOAD_DIR)
        body = "<h1>Uploads Gallery</h1><ul>"
        for fn in files:
            esc = urllib.parse.quote(fn)
            body += f'<li><a href="/uploads/{esc}">{fn}</a></li>'
        body += "</ul><p><a href='/'>Back</a></p>"
        send_response(client, "200 OK", body.encode("utf-8"), "text/html")
        return

    # Serve uploads prefixed path /uploads/...
    if path.startswith("/uploads/"):
        filename = path[len("/uploads/"):]
        filename = urllib.parse.unquote(filename)
        fpath = os.path.join(UPLOAD_DIR, filename)
        if os.path.isfile(fpath):
            with open(fpath, "rb") as f:
                data = f.read()
            send_response(client, "200 OK", data, guess_mime(fpath))
            return
        else:
            send_response(client, "404 Not Found", b"<h1>404 Not Found</h1>")
            return

    file_path = os.path.join(WEB_ROOT, path.lstrip("/"))
    if os.path.isfile(file_path):
        with open(file_path, "rb") as f:
            data = f.read()
        send_response(client, "200 OK", data, guess_mime(file_path))
    else:
        send_response(client, "404 Not Found", b"<h1>404 Not Found</h1>")


def handle_post(request_info: dict, client: socket.socket, initial_bytes: bytes):
    req_line = request_info["request_line"]
    parts = req_line.split(" ")
    if len(parts) < 2:
        send_response(client, "400 Bad Request", b"<h1>400 Bad Request</h1>")
        return
    path = parts[1]
    headers = request_info["headers"]
    content_type = headers.get("content-type", "")
    content_length = int(headers.get("content-length", "0"))

    # Only handle multipart/form-data for /upload
    if path == "/upload" and "multipart/form-data" in content_type:
        boundary = content_type.split("boundary=")[1]
        # initial_bytes contains header + maybe some body bytes; extract body start
        sep = b"\r\n\r\n"
        pos = initial_bytes.find(sep)
        body = initial_bytes[pos+4:] if pos != -1 else b""
        remaining = content_length - len(body)
        while remaining > 0:
            chunk = client.recv(min(BUFFER_SIZE, remaining))
            if not chunk:
                break
            body += chunk
            remaining -= len(chunk)

        # Very simplified multipart parser: find filename and content
        # Search for filename="..."\r\n\r\n then file bytes until boundary
        fname_marker = b'filename="'
        idx = body.find(fname_marker)
        if idx == -1:
            send_response(client, "400 Bad Request", b"<h1>No file in upload</h1>")
            return
        start = idx + len(fname_marker)
        end = body.find(b'"', start)
        filename = body[start:end].decode("utf-8")
        # find start of file bytes
        file_start = body.find(b"\r\n\r\n", end) + 4
        boundary_bytes = ("--" + boundary).encode("utf-8")
        file_end = body.rfind(boundary_bytes) - 2  # strip trailing \r\n before boundary
        file_content = body[file_start:file_end]
        safe_name = os.path.basename(filename)
        save_path = os.path.join(UPLOAD_DIR, safe_name)
        with open(save_path, "wb") as f:
            f.write(file_content)
        resp_body = f"<h1>Uploaded {safe_name}</h1><p><a href='/gallery'>Gallery</a></p>".encode("utf-8")
        send_response(client, "200 OK", resp_body)
    else:
        send_response(client, "415 Unsupported Media Type", b"<h1>Unsupported</h1>")


def start_server():
    ensure_dirs()
    # create a simple index.html if missing
    index_path = os.path.join(WEB_ROOT, "index.html")
    if not os.path.exists(index_path):
        with open(index_path, "w", encoding="utf-8") as f:
            f.write("""<!doctype html>
<html><head><title>My Web Server</title></head><body>
<h1>Welcome</h1>
<p><a href="/upload">Upload a file</a></p>
<p><a href="/gallery">View uploads</a></p>
<form enctype="multipart/form-data" method="POST" action="/upload">
  <input type="file" name="file">
  <input type="submit" value="Upload">
</form>
</body></html>""")
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    assigned_port = server.getsockname()[1]
    server.listen(10)
    print(f"🌍 Web server running at http://{HOST}:{assigned_port}")
    print(f"📂 Public: {WEB_ROOT}")
    print(f"📥 Uploads: {UPLOAD_DIR}")

    while True:
        client, addr = server.accept()
        try:
            header_bytes = read_request(client)
            if not header_bytes:
                client.close()
                continue
            req_info = parse_headers(header_bytes)
            method = req_info["request_line"].split(" ")[0]
            if method == "GET":
                path = req_info["request_line"].split(" ")[1]
                handle_get(path, client)
            elif method == "POST":
                handle_post(req_info, client, header_bytes)
            else:
                send_response(client, "405 Method Not Allowed", b"<h1>405</h1>")
        except Exception as e:
            print("Request handling error:", e)
            try:
                send_response(client, "500 Internal Server Error", b"<h1>500</h1>")
            except Exception:
                pass
        finally:
            client.close()


if __name__ == "__main__":
    start_server()
