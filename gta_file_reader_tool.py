"""
GTA File Reader - Lets the LLM read files directly from /Users/gta/Documents/LLM-Docs
Install as a TOOL in Open WebUI: Admin → Tools → Add Tool
"""
import os
from pathlib import Path
from pydantic import BaseModel, Field
from typing import Optional

class Tools:
    class Valves(BaseModel):
        DOCS_DIR: str = Field(default="/Users/gta/Documents/LLM-Docs")

    def __init__(self):
        self.valves = self.Valves()

    def list_files(self) -> str:
        """
        List all files available in the LLM-Docs folder.
        Call this first to see what files are available to read.
        """
        docs_dir = Path(self.valves.DOCS_DIR)
        if not docs_dir.exists():
            return f"Error: Directory {docs_dir} does not exist"

        files = []
        for root, dirs, filenames in os.walk(docs_dir):
            # Skip hidden directories
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            for filename in filenames:
                if filename.startswith('.'):
                    continue
                filepath = Path(root) / filename
                rel_path = filepath.relative_to(docs_dir)
                size = filepath.stat().st_size
                size_str = f"{size:,} bytes" if size < 1024 else f"{size/1024:.1f} KB"
                files.append(f"- {rel_path} ({size_str})")

        if not files:
            return f"No files found in {docs_dir}"

        return f"Files in {docs_dir}:\n" + "\n".join(files)

    def read_file(self, filename: str) -> str:
        """
        Read the contents of a file from the LLM-Docs folder.

        :param filename: The name or relative path of the file to read
        :return: The contents of the file
        """
        docs_dir = Path(self.valves.DOCS_DIR)
        filepath = docs_dir / filename

        # Security: ensure we're not reading outside the docs directory
        try:
            filepath = filepath.resolve()
            docs_dir_resolved = docs_dir.resolve()
            if not str(filepath).startswith(str(docs_dir_resolved)):
                return "Error: Cannot read files outside of LLM-Docs directory"
        except Exception as e:
            return f"Error resolving path: {e}"

        if not filepath.exists():
            # Try to find the file by name anywhere in the directory
            for root, dirs, filenames in os.walk(docs_dir):
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                if filename in filenames:
                    filepath = Path(root) / filename
                    break

        if not filepath.exists():
            return f"Error: File '{filename}' not found in {docs_dir}"

        # Check file size (limit to 500KB to avoid memory issues)
        if filepath.stat().st_size > 500 * 1024:
            return f"Error: File too large ({filepath.stat().st_size:,} bytes). Maximum is 500KB."

        try:
            content = filepath.read_text(encoding='utf-8', errors='replace')
            return f"=== Contents of {filepath.name} ===\n\n{content}"
        except Exception as e:
            return f"Error reading file: {e}"

    def search_files(self, query: str) -> str:
        """
        Search for files containing specific text.

        :param query: The text to search for
        :return: List of files containing the query and matching lines
        """
        docs_dir = Path(self.valves.DOCS_DIR)
        results = []
        query_lower = query.lower()

        text_extensions = {'.txt', '.md', '.py', '.js', '.ts', '.json', '.yaml', '.yml',
                         '.xml', '.html', '.css', '.sh', '.swift', '.go', '.rs', '.java',
                         '.c', '.cpp', '.h', '.sql', '.env', '.csv', '.log'}

        for root, dirs, filenames in os.walk(docs_dir):
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            for filename in filenames:
                if filename.startswith('.'):
                    continue
                filepath = Path(root) / filename
                if filepath.suffix.lower() not in text_extensions:
                    continue
                if filepath.stat().st_size > 500 * 1024:
                    continue

                try:
                    content = filepath.read_text(encoding='utf-8', errors='replace')
                    if query_lower in content.lower():
                        rel_path = filepath.relative_to(docs_dir)
                        # Find matching lines
                        matches = []
                        for i, line in enumerate(content.split('\n'), 1):
                            if query_lower in line.lower():
                                matches.append(f"  L{i}: {line[:100]}...")
                                if len(matches) >= 3:
                                    break
                        results.append(f"📄 {rel_path}\n" + "\n".join(matches))
                except:
                    continue

        if not results:
            return f"No files found containing '{query}'"

        return f"Files containing '{query}':\n\n" + "\n\n".join(results)
