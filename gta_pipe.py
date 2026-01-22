"""
GTA - All-in-One: Smart Router + File Access + Web Search
"""
from pydantic import BaseModel, Field
from typing import Generator
import requests
import json
import re
import os
from pathlib import Path

class Pipe:
    class Valves(BaseModel):
        OLLAMA_BASE_URL: str = Field(default="http://localhost:11434")
        TEXT_MODEL: str = Field(default="gpt-oss:120b")
        VISION_MODEL: str = Field(default="llama3.2-vision:90b")
        TEXT_CTX_SIZE: int = Field(default=32768)
        VISION_CTX_SIZE: int = Field(default=131072)
        DOCS_DIR: str = Field(default="/Users/gta/Documents/LLM-Docs")
        SERPAPI_KEY: str = Field(default="7fb623579ec799a4f091288f2c25a158c1ad5510f8fca745780641c02657b194")

    def __init__(self):
        self.valves = self.Valves()
        self.name = "GTA"

    def pipes(self) -> list[dict]:
        return [{"id": "gta", "name": "GTA"}]

    def _list_files(self) -> str:
        docs_dir = Path(self.valves.DOCS_DIR)
        if not docs_dir.exists():
            return f"Directory {docs_dir} does not exist"
        files = []
        for root, dirs, filenames in os.walk(docs_dir):
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            for filename in filenames:
                if filename.startswith('.'):
                    continue
                filepath = Path(root) / filename
                rel_path = filepath.relative_to(docs_dir)
                size = filepath.stat().st_size
                size_str = f"{size:,}B" if size < 1024 else f"{size/1024:.1f}KB"
                files.append(f"- {rel_path} ({size_str})")
        return f"Files in {docs_dir}:\n" + "\n".join(files) if files else "No files found"

    def _read_file(self, filename: str) -> str:
        docs_dir = Path(self.valves.DOCS_DIR)
        filepath = docs_dir / filename
        if not filepath.exists():
            for root, dirs, filenames in os.walk(docs_dir):
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                if filename in filenames:
                    filepath = Path(root) / filename
                    break
        if not filepath.exists():
            return f"File '{filename}' not found"
        if filepath.stat().st_size > 500 * 1024:
            return "File too large (max 500KB)"
        try:
            return f"=== {filepath.name} ===\n\n{filepath.read_text(encoding='utf-8', errors='replace')}"
        except Exception as e:
            return f"Error: {e}"

    def _write_file(self, filename: str, content: str) -> str:
        docs_dir = Path(self.valves.DOCS_DIR)
        filepath = docs_dir / filename
        try:
            filepath.parent.mkdir(parents=True, exist_ok=True)
            filepath.write_text(content, encoding='utf-8')
            return f"Successfully wrote to {filename}"
        except Exception as e:
            return f"Error writing file: {e}"

    def _web_search(self, query: str) -> str:
        # Use Google (SerpAPI) if key is set, otherwise DuckDuckGo
        if self.valves.SERPAPI_KEY:
            return self._google_search(query)
        return self._ddg_search(query)

    def _google_search(self, query: str) -> str:
        try:
            from serpapi import GoogleSearch
            params = {
                "q": query,
                "api_key": self.valves.SERPAPI_KEY,
                "num": 5
            }
            search = GoogleSearch(params)
            results = search.get_dict().get("organic_results", [])
            if not results:
                return "No Google results found."
            output = []
            for i, r in enumerate(results[:5], 1):
                output.append(f"**[{i}] {r.get('title', 'No title')}**")
                output.append(f"{r.get('snippet', 'No description')}")
                output.append(f"URL: {r.get('link', '')}\n")
            return "\n".join(output)
        except Exception as e:
            return f"Google search error: {e}"

    def _ddg_search(self, query: str) -> str:
        try:
            from ddgs import DDGS
            results = DDGS().text(query, max_results=5)
            if not results:
                return "No search results found."
            output = []
            for i, r in enumerate(results, 1):
                output.append(f"**[{i}] {r.get('title', 'No title')}**")
                output.append(f"{r.get('body', 'No description')}")
                output.append(f"URL: {r.get('href', '')}\n")
            return "\n".join(output)
        except Exception as e:
            return f"DuckDuckGo search error: {e}"

    def _check_special_request(self, text: str) -> tuple[str, str, str]:
        text = text.strip()
        text_lower = text.lower()

        # Web search triggers
        for prefix in ['google:', 'web:', 'search:', 'find online:', 'lookup:']:
            if text_lower.startswith(prefix):
                query = text[len(prefix):].strip()
                if query:
                    return 'web', query, ''

        # Also handle without colon for some
        if text_lower.startswith('lookup '):
            return 'web', text[7:].strip(), ''
        if text_lower.startswith('find online '):
            return 'web', text[12:].strip(), ''

        # List files
        if any(phrase in text_lower for phrase in ['list files', 'list my files', 'what files', 'show files', 'files in folder', 'my documents', 'local files']):
            return 'list', '', ''

        # Read file
        read_patterns = [
            r'read (?:the )?(?:file )?["\']?([^"\']+\.[a-z]+)["\']?',
            r'show (?:me )?(?:the )?(?:contents of )?(?:file )?["\']?([^"\']+\.[a-z]+)["\']?',
            r'open ["\']?([^"\']+\.[a-z]+)["\']?',
            r'contents of ["\']?([^"\']+\.[a-z]+)["\']?',
        ]
        for pattern in read_patterns:
            match = re.search(pattern, text_lower)
            if match:
                return 'read', match.group(1).strip(), ''

        # Write file - use write: command
        if text_lower.startswith('write: '):
            # Format: write: filename.txt content here
            parts = text[7:].strip().split(' ', 1)
            if len(parts) == 2 and '.' in parts[0]:
                return 'write', parts[0], parts[1]

        # Also detect "save file.txt: content"
        write_match = re.search(r'(?:write|save|create)(?: file)? ([^\s]+\.[a-z]+)[:\s]+(.+)', text, re.DOTALL | re.IGNORECASE)
        if write_match:
            return 'write', write_match.group(1).strip(), write_match.group(2).strip()

        return '', '', ''

    def pipe(self, body: dict) -> Generator:
        messages = body.get("messages", [])
        if not messages:
            yield "No messages provided"
            return

        last_msg = messages[-1]
        content = last_msg.get("content", "")
        has_image = False
        images = []
        text_content = ""

        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict):
                    if item.get("type") == "image_url":
                        has_image = True
                        image_url = item.get("image_url", {})
                        url = image_url.get("url", "") if isinstance(image_url, dict) else ""
                        if url.startswith("data:"):
                            match = re.search(r'base64,(.+)', url)
                            if match:
                                images.append(match.group(1))
                    elif item.get("type") == "text":
                        text_content += item.get("text", "")
                elif isinstance(item, str):
                    text_content += item
        else:
            text_content = content

        # Check for special operations first
        op, arg1, arg2 = self._check_special_request(text_content)

        if op == 'web':
            engine = "Google" if self.valves.SERPAPI_KEY else "DuckDuckGo"
            yield f"🔍 *Searching {engine}...*\n\n"
            search_results = self._web_search(arg1)

            from datetime import datetime
            today = datetime.now().strftime("%B %d, %Y")

            # Feed search results to LLM for intelligent summary
            search_prompt = f"""You have access to live web search. The following search results were JUST retrieved from {engine} on {today}. These are REAL, CURRENT results - not simulated.

USER'S SEARCH QUERY: "{arg1}"

LIVE {engine.upper()} SEARCH RESULTS (retrieved just now on {today}):
{search_results}

INSTRUCTIONS:
- Summarize and answer based on THESE search results above
- These results are LIVE and CURRENT - do NOT say you cannot access the internet
- Be specific, cite the sources, mention relevant details from the snippets
- If the results show current events, weather, news, etc., report them as current information"""

            search_messages = [{"role": "user", "content": search_prompt}]

            try:
                response = requests.post(
                    f"{self.valves.OLLAMA_BASE_URL}/api/chat",
                    json={"model": self.valves.TEXT_MODEL, "messages": search_messages, "stream": True},
                    stream=True,
                    timeout=300
                )

                if response.status_code == 200:
                    for line in response.iter_lines():
                        if line:
                            try:
                                data = json.loads(line)
                                chunk = data.get("message", {}).get("content", "")
                                if chunk:
                                    yield chunk
                            except:
                                continue
                else:
                    yield f"Error getting response: {response.status_code}"
            except Exception as e:
                yield f"Error: {e}"

            yield f"\n\n---\n*{engine} search results processed by {self.valves.TEXT_MODEL}*"
            return
        if op == 'list':
            yield f"**[Local Files]**\n\n{self._list_files()}"
            return
        if op == 'read':
            yield f"**[Reading: {arg1}]**\n\n{self._read_file(arg1)}"
            return
        if op == 'write':
            yield f"**[Writing: {arg1}]**\n\n{self._write_file(arg1, arg2)}"
            return

        model = self.valves.VISION_MODEL if has_image else self.valves.TEXT_MODEL
        ctx_size = self.valves.VISION_CTX_SIZE if has_image else self.valves.TEXT_CTX_SIZE

        if has_image:
            ollama_messages = [{"role": "user", "content": text_content, "images": images}]
        else:
            ollama_messages = []
            for m in messages:
                c = m.get("content", "")
                if isinstance(c, list):
                    c = " ".join([i.get("text", "") if isinstance(i, dict) else str(i) for i in c])
                ollama_messages.append({"role": m.get("role", "user"), "content": c})

        try:
            response = requests.post(
                f"{self.valves.OLLAMA_BASE_URL}/api/chat",
                json={"model": model, "messages": ollama_messages, "stream": True},
                stream=True,
                timeout=600
            )

            if response.status_code != 200:
                yield f"Error: {response.status_code}"
                return

            stats = {}
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        chunk = data.get("message", {}).get("content", "")
                        if chunk:
                            yield chunk
                        if data.get("done"):
                            stats = {
                                "model": model,
                                "total_duration": data.get("total_duration", 0),
                                "prompt_tokens": data.get("prompt_eval_count", 0),
                                "completion_tokens": data.get("eval_count", 0),
                                "prompt_time": data.get("prompt_eval_duration", 0),
                                "eval_time": data.get("eval_duration", 0),
                                "ctx_size": ctx_size
                            }
                    except:
                        continue

            if stats:
                total_sec = stats["total_duration"] / 1e9
                prompt_sec = stats["prompt_time"] / 1e9 if stats["prompt_time"] else 0.001
                eval_sec = stats["eval_time"] / 1e9 if stats["eval_time"] else 0.001
                prompt_tps = stats["prompt_tokens"] / prompt_sec
                gen_tps = stats["completion_tokens"] / eval_sec
                total_tokens = stats["prompt_tokens"] + stats["completion_tokens"]
                ctx_used = (total_tokens / stats["ctx_size"]) * 100
                ctx_bar_filled = int(ctx_used / 5)
                ctx_bar = "█" * ctx_bar_filled + "░" * (20 - ctx_bar_filled)

                yield f"\n\n<details>\n<summary>ℹ️ {stats['model']} • {total_sec:.1f}s • {total_tokens:,} tokens</summary>\n\n"
                yield f"| Metric | Value |\n|--------|-------|\n"
                yield f"| Model | `{stats['model']}` |\n"
                yield f"| Total Time | {total_sec:.1f}s |\n"
                yield f"| Prompt | {stats['prompt_tokens']:,} tokens @ {prompt_tps:.1f} t/s |\n"
                yield f"| Generated | {stats['completion_tokens']:,} tokens @ {gen_tps:.1f} t/s |\n"
                yield f"| Context | {ctx_bar} {ctx_used:.1f}% ({total_tokens:,}/{stats['ctx_size']:,}) |\n"
                yield f"\n</details>"

        except Exception as e:
            yield f"\n\nError: {str(e)}"
