# launcher.py (Final Robust Version with Connection Check)
import webview
import threading
import subprocess
import time
import sys
import os
import requests # <--- NEW IMPORT

# Define the Streamlit server address and port
STREAMLIT_URL = "http://localhost:8501"

def start_streamlit():
    """
    Starts the Streamlit server in the background.
    Uses 'python -m streamlit' to ensure the bundled interpreter runs the module.
    """
    
    # Flags to hide the console window on Windows
    CREATE_NO_WINDOW = 0x08000000 
    
    # CRITICAL FIX: Use 'python', the executable name, to run the Streamlit module
    cmd_list = [
        "python",         # <-- Changed from "streamlit" to "python"
        "-m",             # <-- Added '-m' to run a module
        "streamlit",      # <-- Now running Streamlit as a module
        "run", 
        "app.py", 
        "--server.port", "8501", 
        "--server.headless", "true", 
        "--global.developmentMode", "false"
    ]
    
    if sys.platform.startswith('win'):
        # Pass the command as a list and do NOT use shell=True
        subprocess.Popen(cmd_list, creationflags=CREATE_NO_WINDOW)
    else:
        # Standard Popen call for Unix-like systems
        subprocess.Popen(cmd_list)def check_server_ready(url, timeout=30):
    """Polls the server URL until it responds successfully or the timeout expires."""
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            # Attempt to get a response from the Streamlit server
            response = requests.get(url, timeout=1) 
            if response.status_code == 200:
                print("Streamlit server is ready!")
                return True
        except requests.exceptions.RequestException:
            # Server not up yet, ignore and wait
            pass
        
        # Wait a short period before checking again
        time.sleep(1)
        
    print("Streamlit server failed to start within the timeout.")
    return False

if __name__ == '__main__':
    # CRUCIAL FIX: Check if we are ALREADY running as the subprocess.
    if not os.environ.get('STREAMLIT_SERVER_RUNNING'):
        # Set an environment variable to prevent the subprocess from re-launching the main loop
        os.environ['STREAMLIT_SERVER_RUNNING'] = '1'
        
        # 1. Start Streamlit server in a separate thread
        threading.Thread(target=start_streamlit, daemon=True).start()
        
        # 2. WAIT for the Streamlit server to become ready
        if check_server_ready(STREAMLIT_URL):
            
            # 3. Create the native desktop window using PyWebView
            webview.create_window(
                'XP Tracker Desktop App', 
                url=STREAMLIT_URL, 
                width=1200, 
                height=800,
                resizable=True
            )
            
            # 4. Start the PyWebView main loop
            webview.start()
        else:
            # If the server never started, inform the user (though this console will be hidden)
            print("Application failed to launch because the Streamlit server did not start.")
            # Optionally, you could use a system notification here, but often the console is sufficient
