import subprocess
import os

MENU = """
🔹 Networking Projects Launcher 🔹

Choose an option:
1. Start Chat Server
2. Start Chat Client
3. Start File Server
4. Start File Client
5. Start Web Server
0. Exit
"""

def run_script(path):
    """Run a Python script in the same interpreter."""
    try:
        subprocess.run(["python", path])
    except KeyboardInterrupt:
        print("\n⛔ Process stopped.")
    except FileNotFoundError:
        print(f"❌ Error: {path} not found.")

def main():
    base = os.path.dirname(__file__)
    while True:
        print(MENU)
        choice = input("Enter choice: ").strip()
        
        if choice == "1":
            run_script(os.path.join(base, "MultiClient-Chat-App", "chat_server.py"))
        elif choice == "2":
            run_script(os.path.join(base, "MultiClient-Chat-App", "chat_client.py"))
        elif choice == "3":
            run_script(os.path.join(base, "Sharing-App", "file_server.py"))
        elif choice == "4":
            run_script(os.path.join(base, "Sharing-App", "file_client.py"))
        elif choice == "5":
            run_script(os.path.join(base, "Web Server", "web_server.py"))
        elif choice == "0":
            print("👋 Exiting. Bye!")
            break
        else:
            print("⚠️ Invalid choice. Try again.\n")

if __name__ == "__main__":
    main()
