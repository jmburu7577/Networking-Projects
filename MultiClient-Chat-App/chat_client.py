"""
Multi-Client Chat Client (with file send)
-----------------------------------------
- Connects to the chat server.
- Sends/receives messages.
- Use command: /sendfile <path>  to send a file to the server.
- On server-side the file is saved to ChatUploads/.
"""

import socket
import threading
import os
import sys

HOST = "127.0.0.1"
PORT = 0  # leave zero -> prompt user to supply port or auto-detect below
BUFFER_SIZE = 4096


def prompt_server_info():
    """Prompt user for server port if PORT is 0."""
    global PORT
    if PORT == 0:
        try:
            PORT = int(input("Enter server port (from server console): ").strip())
        except Exception:
            print("Invalid port. Exiting.")
            sys.exit(1)


def receive_loop(sock: socket.socket):
    """Receive and print messages from server."""
    try:
        while True:
            data = sock.recv(BUFFER_SIZE)
            if not data:
                print("🔌 Disconnected from server")
                break
            print(data.decode("utf-8", errors="ignore").rstrip())
    except Exception as e:
        print("Receive error:", e)
    finally:
        sock.close()


def send_file(sock: socket.socket, filepath: str):
    """Send a file to the server using header protocol."""
    if not os.path.isfile(filepath):
        print("⚠️ File not found:", filepath)
        return
    filename = os.path.basename(filepath)
    size = os.path.getsize(filepath)
    header = f"FILE|{filename}|{size}\n".encode("utf-8")
    sock.sendall(header)
    with open(filepath, "rb") as f:
        while chunk := f.read(BUFFER_SIZE):
            sock.sendall(chunk)
    print(f"✅ Sent file: {filename} ({size} bytes)")


def send_loop(sock: socket.socket, nickname: str):
    """Read input from user and send either text or file command."""
    try:
        while True:
            line = input()
            if not line:
                continue
            if line.startswith("/sendfile "):
                _, path = line.split(" ", 1)
                send_file(sock, path.strip())
            else:
                # send as normal chat message
                message = f"{nickname}: {line}\n".encode("utf-8")
                sock.sendall(message)
    except Exception as e:
        print("Send error:", e)
    finally:
        sock.close()


if __name__ == "__main__":
    nickname = input("Choose your nickname: ").strip()
    if not nickname:
        nickname = "Anonymous"
    prompt_server_info()
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((HOST, PORT))
    # Wait for NICK request or send nickname immediately
    first = client.recv(BUFFER_SIZE).decode("utf-8", errors="ignore")
    if first.strip() == "NICK":
        client.sendall(nickname.encode("utf-8"))
    else:
        # Unexpected server, but send nickname anyway
        client.sendall(nickname.encode("utf-8"))

    # Start receiver and sender threads
    threading.Thread(target=receive_loop, args=(client,), daemon=True).start()
    send_loop(client, nickname)
