"""
File Sharing Server
-------------------
- Multi-client server: supports upload and download commands.
- Protocol (text control lines, then raw bytes):
    UPLOAD|<filename>|<size>\n  -> then <size> bytes follow
    DOWNLOAD|<filename>\n      -> server responds FOUND|<size>\n then <size> bytes; or NOTFOUND\n
- Files saved under 'shared/' directory.
"""

import socket
import threading
import os

HOST = "127.0.0.1"
PORT = 0  # OS picks free port
BUFFER_SIZE = 4096
SHARED_DIR = os.path.join(os.path.dirname(__file__), "shared")
lock = threading.Lock()


def ensure_shared_dir():
    os.makedirs(SHARED_DIR, exist_ok=True)


def recv_all(sock: socket.socket, size: int) -> bytes:
    """Receive exactly size bytes from socket."""
    data = b""
    while len(data) < size:
        packet = sock.recv(min(BUFFER_SIZE, size - len(data)))
        if not packet:
            break
        data += packet
    return data


def handle_client(conn: socket.socket, addr):
    """Per-client loop to process upload/download commands."""
    print(f"🟢 Client connected: {addr}")
    try:
        while True:
            header = b""
            # Read until newline
            while b"\n" not in header:
                chunk = conn.recv(1)
                if not chunk:
                    return
                header += chunk
            header_line = header.decode("utf-8").strip()
            if header_line.startswith("UPLOAD|"):
                # UPLOAD|filename|size
                _, filename, size_str = header_line.split("|", 2)
                size = int(size_str)
                print(f"⬆️ Upload request: {filename} ({size} bytes) from {addr}")
                file_bytes = recv_all(conn, size)
                safe_name = os.path.basename(filename)
                save_path = os.path.join(SHARED_DIR, safe_name)
                with open(save_path, "wb") as f:
                    f.write(file_bytes)
                conn.sendall(f"OK|{safe_name}\n".encode("utf-8"))

            elif header_line.startswith("DOWNLOAD|"):
                _, filename = header_line.split("|", 1)
                safe_name = os.path.basename(filename)
                file_path = os.path.join(SHARED_DIR, safe_name)
                if not os.path.isfile(file_path):
                    conn.sendall(b"NOTFOUND\n")
                else:
                    size = os.path.getsize(file_path)
                    conn.sendall(f"FOUND|{size}\n".encode("utf-8"))
                    with open(file_path, "rb") as f:
                        while chunk := f.read(BUFFER_SIZE):
                            conn.sendall(chunk)
            elif header_line == "LIST":
                # send list of files, newline separated, end with DONE
                files = os.listdir(SHARED_DIR)
                payload = "\n".join(files) + "\nDONE\n"
                conn.sendall(payload.encode("utf-8"))
            else:
                # Unknown command
                conn.sendall(b"ERROR|Unknown command\n")
    except Exception as e:
        print("Client handler error:", e)
    finally:
        conn.close()
        print(f"🔴 Client disconnected: {addr}")


def start_server():
    ensure_shared_dir()
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    assigned_port = server.getsockname()[1]
    server.listen(10)
    print(f"📡 File server running on {HOST}:{assigned_port}")
    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()


if __name__ == "__main__":
    start_server()
