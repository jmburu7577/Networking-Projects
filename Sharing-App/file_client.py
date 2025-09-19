"""
File Sharing Client
-------------------
- CLI client to upload / download / list files from file_server.py.
- Example commands:
    upload <local_path>
    download <filename_on_server>
    list
    quit
"""

import socket
import os
import sys

HOST = "127.0.0.1"
PORT = 0  # prompt user
BUFFER_SIZE = 4096


def prompt_server_port():
    global PORT
    if PORT == 0:
        try:
            PORT = int(input("Enter file server port: ").strip())
        except Exception:
            print("Invalid port; exiting.")
            sys.exit(1)


def upload(sock: socket.socket, local_path: str):
    if not os.path.isfile(local_path):
        print("⚠️ Local file not found.")
        return
    filename = os.path.basename(local_path)
    size = os.path.getsize(local_path)
    header = f"UPLOAD|{filename}|{size}\n".encode("utf-8")
    sock.sendall(header)
    with open(local_path, "rb") as f:
        while chunk := f.read(BUFFER_SIZE):
            sock.sendall(chunk)
    resp = sock.recv(BUFFER_SIZE).decode("utf-8").strip()
    print("Server:", resp)


def download(sock: socket.socket, filename: str):
    header = f"DOWNLOAD|{filename}\n".encode("utf-8")
    sock.sendall(header)
    resp = b""
    # read single line response (FOUND|size or NOTFOUND)
    while b"\n" not in resp:
        chunk = sock.recv(1)
        if not chunk:
            print("No response.")
            return
        resp += chunk
    line = resp.decode("utf-8").strip()
    if line == "NOTFOUND":
        print("⚠️ File not found on server.")
        return
    if line.startswith("FOUND|"):
        size = int(line.split("|", 1)[1])
        remaining = size
        out_path = os.path.join(os.getcwd(), filename)
        with open(out_path, "wb") as f:
            while remaining > 0:
                chunk = sock.recv(min(BUFFER_SIZE, remaining))
                if not chunk:
                    break
                f.write(chunk)
                remaining -= len(chunk)
        print("✅ Download complete:", out_path)


def list_files(sock: socket.socket):
    sock.sendall(b"LIST\n")
    data = b""
    while True:
        chunk = sock.recv(BUFFER_SIZE)
        if not chunk:
            break
        data += chunk
        if b"\nDONE\n" in data:
            break
    text = data.decode("utf-8")
    files = text.replace("\nDONE\n", "").strip()
    print("--- Files on server ---")
    if files:
        print(files)
    else:
        print("(no files)")


def interactive_client():
    prompt_server_port()
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))
    print("Connected to file server.")
    try:
        while True:
            cmd = input("file-client> ").strip()
            if not cmd:
                continue
            parts = cmd.split(" ", 1)
            action = parts[0].lower()
            arg = parts[1] if len(parts) > 1 else None
            if action == "upload" and arg:
                upload(s, arg)
            elif action == "download" and arg:
                download(s, arg)
            elif action == "list":
                list_files(s)
            elif action in ("quit", "exit"):
                print("Closing connection.")
                break
            else:
                print("Commands: upload <path>, download <filename>, list, quit")
    finally:
        s.close()


if __name__ == "__main__":
    interactive_client()
