#!/usr/bin/env python3
"""
LLM-Docs Auto-Sync - Watches folder and syncs to Open WebUI Knowledge Base
"""
import os
import sys
import time
import hashlib
import sqlite3
import requests
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Configuration
WATCH_DIR = "/Users/gta/Documents/LLM-Docs"
OPENWEBUI_URL = "http://localhost:8080"
KNOWLEDGE_NAME = "Local Files"
SYNC_DB = "/Users/gta/Documents/LLM-Docs/.sync_state.db"
SUPPORTED_EXTENSIONS = {'.txt', '.md', '.pdf', '.py', '.js', '.ts', '.json', '.yaml', '.yml', '.xml', '.html', '.css', '.sh', '.bash', '.zsh', '.swift', '.go', '.rs', '.java', '.c', '.cpp', '.h', '.hpp', '.sql', '.env', '.csv'}

class SyncState:
    """Track synced files to avoid duplicates"""
    def __init__(self, db_path):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS synced_files (
                path TEXT PRIMARY KEY,
                hash TEXT,
                synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()

    def get_hash(self, filepath):
        with open(filepath, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()

    def needs_sync(self, filepath):
        current_hash = self.get_hash(filepath)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute('SELECT hash FROM synced_files WHERE path = ?', (filepath,))
        row = cursor.fetchone()
        conn.close()
        return row is None or row[0] != current_hash

    def mark_synced(self, filepath):
        current_hash = self.get_hash(filepath)
        conn = sqlite3.connect(self.db_path)
        conn.execute('''
            INSERT OR REPLACE INTO synced_files (path, hash, synced_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', (filepath, current_hash))
        conn.commit()
        conn.close()

    def remove(self, filepath):
        conn = sqlite3.connect(self.db_path)
        conn.execute('DELETE FROM synced_files WHERE path = ?', (filepath,))
        conn.commit()
        conn.close()

class OpenWebUIClient:
    """Client for Open WebUI API"""
    def __init__(self, base_url):
        self.base_url = base_url
        self.session = requests.Session()
        self.api_key = self._get_api_key()
        if self.api_key:
            self.session.headers['Authorization'] = f'Bearer {self.api_key}'

    def _get_api_key(self):
        """Get API key from environment or config"""
        key = os.environ.get('OPENWEBUI_API_KEY')
        if key:
            return key
        # Try to read from config file
        config_path = Path.home() / '.config' / 'openwebui_api_key'
        if config_path.exists():
            return config_path.read_text().strip()
        return None

    def upload_file(self, filepath):
        """Upload a file to Open WebUI"""
        try:
            with open(filepath, 'rb') as f:
                files = {'file': (os.path.basename(filepath), f)}
                response = self.session.post(
                    f"{self.base_url}/api/v1/files/",
                    files=files
                )
                if response.status_code == 200:
                    return response.json()
                else:
                    print(f"[ERROR] Upload failed for {filepath}: {response.status_code}")
                    return None
        except Exception as e:
            print(f"[ERROR] Upload exception for {filepath}: {e}")
            return None

class DocSyncHandler(FileSystemEventHandler):
    """Handle file system events"""
    def __init__(self, sync_state, client):
        self.sync_state = sync_state
        self.client = client
        self.debounce = {}

    def _should_sync(self, filepath):
        ext = Path(filepath).suffix.lower()
        return ext in SUPPORTED_EXTENSIONS

    def _sync_file(self, filepath):
        if not os.path.exists(filepath):
            return
        if not self._should_sync(filepath):
            return
        if not self.sync_state.needs_sync(filepath):
            return

        print(f"[SYNC] Uploading: {filepath}")
        result = self.client.upload_file(filepath)
        if result:
            self.sync_state.mark_synced(filepath)
            print(f"[SYNC] Success: {os.path.basename(filepath)}")

    def on_created(self, event):
        if event.is_directory:
            return
        # Debounce to avoid multiple events
        self.debounce[event.src_path] = time.time()
        time.sleep(0.5)
        if time.time() - self.debounce.get(event.src_path, 0) >= 0.5:
            self._sync_file(event.src_path)

    def on_modified(self, event):
        if event.is_directory:
            return
        self.debounce[event.src_path] = time.time()
        time.sleep(0.5)
        if time.time() - self.debounce.get(event.src_path, 0) >= 0.5:
            self._sync_file(event.src_path)

    def on_deleted(self, event):
        if event.is_directory:
            return
        self.sync_state.remove(event.src_path)
        print(f"[SYNC] Removed from tracking: {event.src_path}")

def initial_sync(watch_dir, sync_state, client):
    """Sync all existing files on startup"""
    print(f"[INIT] Scanning {watch_dir} for files to sync...")
    count = 0
    for root, dirs, files in os.walk(watch_dir):
        # Skip hidden directories
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for filename in files:
            if filename.startswith('.'):
                continue
            filepath = os.path.join(root, filename)
            ext = Path(filepath).suffix.lower()
            if ext in SUPPORTED_EXTENSIONS:
                if sync_state.needs_sync(filepath):
                    print(f"[SYNC] Uploading: {filename}")
                    result = client.upload_file(filepath)
                    if result:
                        sync_state.mark_synced(filepath)
                        count += 1
    print(f"[INIT] Synced {count} files")

def main():
    print("=" * 50)
    print("LLM-Docs Auto-Sync Service")
    print("=" * 50)
    print(f"Watching: {WATCH_DIR}")
    print(f"Target: {OPENWEBUI_URL}")
    print("=" * 50)

    # Ensure watch directory exists
    os.makedirs(WATCH_DIR, exist_ok=True)

    # Initialize components
    sync_state = SyncState(SYNC_DB)
    client = OpenWebUIClient(OPENWEBUI_URL)

    # Check if API key is configured
    if not client.api_key:
        print("\n[WARNING] No API key configured!")
        print("To enable sync, either:")
        print("  1. Set OPENWEBUI_API_KEY environment variable")
        print("  2. Create ~/.config/openwebui_api_key with your key")
        print("\nGet your API key from Open WebUI: Settings → Account → API Keys")
        print("\nContinuing in watch-only mode...")

    # Do initial sync
    if client.api_key:
        initial_sync(WATCH_DIR, sync_state, client)

    # Set up file watcher
    handler = DocSyncHandler(sync_state, client)
    observer = Observer()
    observer.schedule(handler, WATCH_DIR, recursive=True)
    observer.start()

    print(f"\n[WATCH] Monitoring {WATCH_DIR} for changes...")
    print("Press Ctrl+C to stop\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\n[STOP] Sync service stopped")
    observer.join()

if __name__ == "__main__":
    main()
