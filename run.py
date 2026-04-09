#!/usr/bin/env python3
"""Citations Automation Tool - Entry point"""
import uvicorn
import webbrowser
import threading
import time

def open_browser():
    time.sleep(1.5)
    webbrowser.open("http://localhost:8000")

if __name__ == "__main__":
    print("\n  Citations Automation Tool")
    print("  http://localhost:8000\n")
    threading.Thread(target=open_browser, daemon=True).start()
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
