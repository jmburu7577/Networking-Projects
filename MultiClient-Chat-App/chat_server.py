"""
Multi-Client Chat Server (with file receive)
--------------------------------------------
- Accepts multiple clients (thread per client).
- Supports text messages broadcast.
- Supports file uploads from clients using a simple header protocol:
    FILE|<filename>|<size>\n  followed by raw bytes of <size>.
- Received files are saved to ChatUploads/ folder.
"""

import socket
import threading
import os

HOST = "127.0.0.1"
PORT = 0  # Let OS assign a free port
BUFFER_SIZE = 4096
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "ChatUploads")

clients = []
nicknames = []
lock = threading.Lock()


def ensure_upload_dir():
    os.makedirs(UPLOAD_DIR, exist_ok=True)


def broadcast(message: str, exclude: socket.socket = None) -> None:
    """Send a message (string) to all connected clients (optionally excluding one)."""
    with lock:
        for client in clients:
            if client is not exclude:
                try:
                    client.send(message.encode("utf-8"))
                except Exception:
                    # Ignore send errors; client handler will clean up
                    pass


def receive_file(client_socket: socket.socket, filename: str, size: int) -> str:
    """
    Receive exactly `size` bytes from client_socket and save to UPLOAD_DIR.
    Returns the saved file path.
    """
    ensure_upload_dir()
    safe_name = os.path.basename(filename)
    out_path = os.path.join(UPLOAD_DIR, safe_name)
    remaining = size
    with open(out_path, "wb") as f:
        while remaining > 0:
            chunk = client_socket.recv(min(BUFFER_SIZE, remaining))
            if not chunk:
                break
            f.write(chunk)
            remaining -= len(chunk)
    return out_path


def handle_client(client_socket: socket.socket) -> None:
    """Handle messages (and file uploads) from a single client."""
    try:
        while True:
            data = client_socket.recv(BUFFER_SIZE)
            if not data:
                break

            # Check for file header (ASCII text)
            if data.startswith(b"FILE|"):
                try:
                    header, rest = data.split(b"\n", 1)
                except ValueError:
                    header = data.strip()
                    rest = b""

                parts = header.decode("utf-8").split("|", 2)
                if len(parts) != 3:
                    client_socket.send("ERROR|Invalid file header\n".encode("utf-8"))
                    continue
                _, filename, size_str = parts
                try:
                    size = int(size_str)
                except ValueError:
                    client_socket.send("ERROR|Invalid file size\n".encode("utf-8"))
                    continue

                temp_path = receive_file_with_initial(client_socket, filename, size, rest)

                with lock:
                    try:
                        idx = clients.index(client_socket)
                        sender = nicknames[idx]
                    except ValueError:
                        sender = "Unknown"

                msg = f"🔔 {sender} uploaded file: {os.path.basename(temp_path)} ({size} bytes)\n"
                broadcast(msg)
                continue

            # Normal broadcast message
            try:
                decoded = data.decode("utf-8")
            except UnicodeDecodeError:
                decoded = "<Invalid UTF-8 data>"
            broadcast(decoded)
    finally:
        remove_client(client_socket)


def receive_file_with_initial(client_socket: socket.socket, filename: str, size: int, initial_bytes: bytes) -> str:
    """Write `initial_bytes` then read remaining bytes from socket."""
    ensure_upload_dir()
    safe_name = os.path.basename(filename)
    out_path = os.path.join(UPLOAD_DIR, safe_name)
    remaining = size
    with open(out_path, "wb") as f:
        if initial_bytes:
            f.write(initial_bytes)
            remaining -= len(initial_bytes)
        while remaining > 0:
            chunk = client_socket.recv(min(BUFFER_SIZE, remaining))
            if not chunk:
                break
            f.write(chunk)
            remaining -= len(chunk)
    return out_path


def remove_client(client_socket: socket.socket) -> None:
    """Remove client from lists and broadcast leave message."""
    with lock:
        if client_socket in clients:
            idx = clients.index(client_socket)
            nickname = nicknames[idx]
            try:
                clients.remove(client_socket)
                nicknames.pop(idx)
                client_socket.close()
            except Exception:
                pass
            broadcast(f"⚠️ {nickname} left the chat.\n")


def accept_connections(server_socket: socket.socket) -> None:
    """Main loop: accept new clients and start a handler thread for each."""
    print("Server is waiting for connections...")
    while True:
        client_socket, addr = server_socket.accept()
        print(f"✅ Connected: {addr}")

        client_socket.send("NICK\n".encode("utf-8"))
        nick = client_socket.recv(BUFFER_SIZE).decode("utf-8").strip()

        with lock:
            clients.append(client_socket)
            nicknames.append(nick)

        print(f"🎉 Nickname: {nick}")
        broadcast(f"🎉 {nick} joined the chat.\n")
        client_socket.send("✅ Connected to chat server.\n".encode("utf-8"))

        thread = threading.Thread(target=handle_client, args=(client_socket,), daemon=True)
        thread.start()


def start_server():
    """Create server socket, bind, and start accepting clients."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    assigned_port = server.getsockname()[1]
    server.listen(10)
    print(f"📡 Chat server running on {HOST}:{assigned_port}")
    accept_connections(server)


if __name__ == "__main__":
    start_server()
