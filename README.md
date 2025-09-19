# Networking Projects

## Overview

This project is a collection of networking applications that I built to strengthen my skills as a software engineer in socket programming, client-server communication, and real-world systems development.  

The suite includes:  
- **Multi-Client Chat Application** – enables real-time text communication between multiple clients.  
- **File Sharing System** – allows clients to upload, download, and list files from a central server.  
- **Basic Web Server** – serves static files and handles file uploads.  

The purpose of creating this software was to gain practical experience in designing, implementing, and testing different types of network applications that handle real-time communication, file transfer, and web-based interactions. Each component demonstrates core networking concepts such as TCP sockets, concurrency, and request/response protocols.  

## Features

- **Chat Application**
  - Multi-client chat server with broadcast functionality.
  - Chat client with nickname support.
  - Handles multiple users concurrently using threads.

- **File Sharing**
  - Upload files to the server.
  - Download files from the server.
  - List all available files.
  - Graceful connect and disconnect.

- **Web Server**
  - Serves static HTML, CSS, and JS files.
  - Handles file uploads and stores them in an uploads directory.
  - Provides clean logging of requests.

## Development Environment

- **Programming Language:** Python 3.12  
- **Libraries & Tools:**  
  - `socket` – low-level networking  
  - `threading` – concurrency with multiple clients  
  - `os` and `pathlib` – file handling and management  
  - `http.server` – lightweight HTTP server functionality  
- **Editor/IDE:** Visual Studio Code  
- **Version Control:** Git & GitHub  
- **Operating System:** Windows 10  

## Useful Websites

These resources were very helpful while working on this project:  
* [Python Socket Programming HOWTO](https://docs.python.org/3/howto/sockets.html)  
* [Real Python – Socket Programming in Python](https://realpython.com/python-sockets/)  
* [Python Official Documentation – http.server](https://docs.python.org/3/library/http.server.html)  
* [GeeksforGeeks – Multi-threaded Socket Programming](https://www.geeksforgeeks.org/socket-programming-multi-threading-python/)  
