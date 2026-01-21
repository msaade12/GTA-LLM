# Local LLM Setup Documentation

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           MAC STUDIO M3 ULTRA                                │
│                             512GB Unified Memory                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────┐     ┌─────────────────┐     ┌──────────────────┐          │
│  │   Ollama    │────►│   Open WebUI    │────►│   Cloudflare     │          │
│  │  :11434     │     │     :8080       │     │     Tunnel       │          │
│  │             │     │                 │     │                  │          │
│  │ - DeepSeek  │     │ - Chat UI       │     │ - HTTPS          │          │
│  │   R1 671B   │     │ - RAG/Docs      │     │ - Reverse Proxy  │          │
│  │ - GPT-OSS   │     │ - Web Search    │     │ - DDoS Protect   │          │
│  │ - Llama     │     │ - Multi-user    │     │ - Hide IP        │          │
│  │   Vision    │     │ - Multi-model   │     │ - Bot Protection │          │
│  └─────────────┘     └─────────────────┘     └────────┬─────────┘          │
│                                                        │                    │
└────────────────────────────────────────────────────────┼────────────────────┘
                                                         │
                                                         │ Outbound Connection
                                                         │ (No open ports)
                                                         ▼
                                              ┌──────────────────┐
                                              │    CLOUDFLARE    │
                                              │     SERVERS      │
                                              │                  │
                                              │  Public URL:     │
                                              │  gta.ironlink    │
                                              │  connect.com     │
                                              └────────┬─────────┘
                                                       │
                                                       │ HTTPS (443)
                                                       ▼
                                    ┌─────────────────────────────────┐
                                    │          INTERNET               │
                                    │                                 │
                                    │  ┌─────────┐    ┌─────────┐    │
                                    │  │ Android │    │   iOS   │    │
                                    │  │  Phone  │    │  Phone  │    │
                                    │  └─────────┘    └─────────┘    │
                                    │                                 │
                                    │  ┌─────────┐    ┌─────────┐    │
                                    │  │  Web    │    │ Custom  │    │
                                    │  │ Browser │    │   App   │    │
                                    │  └─────────┘    └─────────┘    │
                                    └─────────────────────────────────┘
```

---

## Hardware

| Component | Specification |
|-----------|---------------|
| Machine | Mac Studio |
| Chip | Apple M3 Ultra |
| Memory | 512GB Unified Memory |
| Memory Bandwidth | ~800 GB/s |
| OS | macOS 15.6.0 |

---

## Installed Software

### 1. Ollama (LLM Runtime)
- **Version**: 0.14.2
- **Location**: `/opt/homebrew/bin/ollama`
- **Service**: `brew services start ollama`
- **Port**: 11434
- **Config**: Listening on `0.0.0.0:11434` (all interfaces)
- **Keep Alive**: Models stay loaded indefinitely (`OLLAMA_KEEP_ALIVE=-1`)

### 2. Open WebUI (Chat Interface)
- **Version**: 0.7.2
- **Location**: `/Users/gta/.local/bin/open-webui`
- **Port**: 8080
- **Data Directory**: `/Users/gta/Open-WebUI/`
- **Installed via**: pipx with Python 3.12

### 3. Cloudflared (Tunnel)
- **Version**: 2026.1.1
- **Location**: `/opt/homebrew/bin/cloudflared`
- **Mode**: Managed Tunnel (permanent URL)
- **Domain**: `ironlinkconnect.com`
- **Subdomain**: `gta`

---

## Downloaded Models

| Model | Size | Purpose | Vision | Status |
|-------|------|---------|--------|--------|
| DeepSeek-R1 671B | 404GB | Smartest reasoning, coding, math | No | ✅ Ready |
| GPT-OSS 120B | 65GB | Fast general chat, agentic tasks, 128K context | No | ✅ Ready |
| Llama 3.2 Vision 90B | 54GB | Image/document understanding | **Yes** | ✅ Ready |

### Model Usage Guide

| Use Case | Recommended Model |
|----------|-------------------|
| Complex reasoning, math, coding | `deepseek-r1:671b` |
| Fast general chat, quick questions | `gpt-oss:120b` |
| Image analysis, screenshots, photos | `llama3.2-vision:90b` |
| Scanned PDFs (images of text) | `llama3.2-vision:90b` |
| Text PDFs, Word docs | Any model |

### Running Multiple Models

With 512GB RAM, you can run multiple models simultaneously:
- DeepSeek-R1 (404GB) + Llama Vision (54GB) = 458GB ✅
- All three models won't fit simultaneously

**To pre-load models:**
```bash
ollama run deepseek-r1:671b ""      # Load DeepSeek
ollama run llama3.2-vision:90b ""   # Load Vision model
```

**Check loaded models:**
```bash
ollama ps
```

**Unload a model:**
```bash
ollama stop deepseek-r1:671b
```

---

## Features

### Web Search
- **Engine**: DuckDuckGo (no API key required)
- **How to use**: Type `#web` before your question
- **Example**: `#web what are the top restaurants in NYC`
- **Package**: `ddgs` (installed via pipx inject)

### Document Upload
- **Supported**: PDF, Word, text files, images
- **How to use**: Click `+` → `Upload Files` in chat
- **Storage**: `/Users/gta/Open-WebUI/uploads/`

### Knowledge Base (RAG)
- **Location**: Workspace → Knowledge
- **Create collections** of documents for persistent access
- **Attach to chats**: Click `+` → `Attach Knowledge`
- **Vector DB**: `/Users/gta/Open-WebUI/vector_db/`

### Local File Access (GTA File Reader Tool)
The LLM can read files directly from your Mac without uploading them.

**Folder**: `/Users/gta/Documents/LLM-Docs`

**Setup**:
1. Go to Admin → Tools → Add Tool
2. Paste the code from `/Users/gta/SRC/Local LLM/gta_file_reader_tool.py`
3. Save and enable the tool

**How to Use**:
Just ask the LLM naturally:
- "List the files in my documents folder"
- "Read the file config.py"
- "Search for files containing 'database'"

**Available Commands** (the LLM calls these automatically):
| Command | What it does |
|---------|--------------|
| `list_files()` | Shows all files in LLM-Docs folder |
| `read_file(filename)` | Reads contents of a specific file |
| `search_files(query)` | Finds files containing specific text |

**Drop files here**: `/Users/gta/Documents/LLM-Docs/`
The LLM can immediately see and read them - no upload needed.

### Multi-Model Chat
- Select multiple models in the model selector (top left)
- Get parallel responses from different models
- Compare reasoning between models

### GTA Smart Router (Custom Function)
Auto-routes requests to the right model based on content.

**How it works**:
- **Image/screenshot detected** → Uses `llama3.2-vision:90b`
- **Text only** → Uses `gpt-oss:120b`

**Setup**:
1. Go to Admin → Functions → Add Function
2. Paste the code from `/Users/gta/SRC/Local LLM/gta_pipe.py`
3. Save and enable

**Select "GTA"** from the model dropdown to use it.

**Stats**: Click the ℹ️ dropdown at the end of each response to see:
- Model used
- Total time
- Tokens per second
- Context window usage

---

## Network Configuration

### Local Access
```
http://localhost:8080          # From the Mac itself
http://192.168.0.113:8080      # From devices on home network
```

### Remote Access (via Cloudflare Tunnel)
```
https://gta.ironlinkconnect.com
```

**Permanent URL**: `https://gta.ironlinkconnect.com`

> ✅ This URL is permanent and will not change.

---

## Data Storage

### Open WebUI Data
```
/Users/gta/Open-WebUI/
├── webui.db          # Database (users, chats, settings)
├── uploads/          # Uploaded files
├── cache/            # Temporary cache
└── vector_db/        # Document embeddings for RAG
```

### Ollama Models
```
/Users/gta/.ollama/models/     # Downloaded model files (~520GB total)
```

### Logs
```
/tmp/open-webui.log            # Open WebUI logs
/tmp/cloudflared.log           # Tunnel logs (if using quick tunnel)
```

---

## Connection Flow

### How a request flows from phone to LLM:

```
1. Phone Browser
   │
   │  HTTPS request to:
   │  https://gta.ironlinkconnect.com
   │
   ▼
2. Cloudflare Edge Server
   │
   │  Receives on port 443 (HTTPS)
   │  Decrypts SSL
   │  Applies security (WAF, DDoS, Bot protection)
   │
   ▼
3. Cloudflare Tunnel
   │
   │  Forwards through the tunnel that YOUR Mac
   │  created (outbound connection)
   │
   ▼
4. cloudflared on Mac
   │
   │  Receives from Cloudflare
   │  Forwards to localhost:8080
   │
   ▼
5. Open WebUI (:8080)
   │
   │  Handles authentication
   │  Processes chat request
   │  Web search (if #web used)
   │  Document retrieval (if RAG)
   │  Calls Ollama API
   │
   ▼
6. Ollama (:11434)
   │
   │  Loads model into memory (if not already loaded)
   │  Runs inference on M3 Ultra GPU
   │  Streams response back
   │
   ▼
7. Response flows back through the same path
```

---

## Security Layers

| Layer | Protection | Notes |
|-------|------------|-------|
| **Cloudflare** | HTTPS, DDoS, WAF, Bot Fight Mode | All traffic encrypted |
| **No Open Ports** | Firewall closed | Tunnel is outbound only |
| **Permanent URL** | Known endpoint | No random URL changes |
| **Open WebUI Auth** | Username/Password | Admin account created |
| **Local Network** | Router NAT | Additional isolation |

---

## Auto-Start Services

### Launch Agents (start on login)

| Service | Plist Location | Type |
|---------|----------------|------|
| Ollama | `brew services` (homebrew.mxcl.ollama) | Homebrew |
| Open WebUI | `~/Library/LaunchAgents/com.openwebui.serve.plist` | User |
| Cloudflared | `/Library/LaunchDaemons/com.cloudflare.cloudflared.plist` | System |

### Service Commands

```bash
# Check all services
launchctl list | grep -E "ollama|openwebui|cloudflared"
brew services list

# Restart Open WebUI
launchctl stop com.openwebui.serve
launchctl start com.openwebui.serve

# Restart Ollama
brew services restart ollama

# View logs
tail -f /tmp/open-webui.log
```

---

## Configuration Files

### Open WebUI LaunchAgent
**File**: `~/Library/LaunchAgents/com.openwebui.serve.plist`

**Environment Variables**:
| Variable | Value | Purpose |
|----------|-------|---------|
| `PATH` | `/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin` | Find executables |
| `DATA_DIR` | `/Users/gta/Open-WebUI` | Database & uploads |
| `DOCS_DIR` | `/Users/gta/Documents/LLM-Docs` | Document folder access |
| `HOME` | `/Users/gta` | Home directory |

### Ollama Configuration
**Keep models loaded**: `OLLAMA_KEEP_ALIVE=-1` (set via launchctl)

---

## Useful Commands

### Model Management
```bash
ollama list                    # List downloaded models
ollama ps                      # Show loaded models (in memory)
ollama stop <model>            # Unload model from memory
ollama pull <model>            # Download a model
ollama rm <model>              # Delete a model
```

### Service Management
```bash
brew services list             # Homebrew services
brew services restart ollama   # Restart Ollama

launchctl stop com.openwebui.serve    # Stop Open WebUI
launchctl start com.openwebui.serve   # Start Open WebUI
```

### Network Diagnostics
```bash
lsof -i :8080                  # Check Open WebUI port
lsof -i :11434                 # Check Ollama port
curl http://localhost:11434/api/tags   # Test Ollama API
curl http://localhost:8080/api/version # Test Open WebUI API
```

---

## Access URLs Summary

| Location | Open WebUI URL | Ollama API |
|----------|----------------|------------|
| On Mac | http://localhost:8080 | http://localhost:11434 |
| Home Network | http://192.168.0.113:8080 | http://192.168.0.113:11434 |
| Anywhere | https://gta.ironlinkconnect.com | N/A (use Open WebUI) |

---

## Troubleshooting

### Open WebUI not loading
```bash
# Check if running
pgrep -f open-webui

# Restart
launchctl stop com.openwebui.serve
launchctl start com.openwebui.serve

# Check logs
tail -50 /tmp/open-webui.log
```

### Web Search not working
```bash
# Reinstall search package
pipx inject open-webui ddgs --force

# Restart Open WebUI
launchctl stop com.openwebui.serve
launchctl start com.openwebui.serve
```

### Models loading slowly
```bash
# Check if model is already loaded
ollama ps

# Pre-load frequently used models
ollama run deepseek-r1:671b ""
ollama run llama3.2-vision:90b ""
```

### Tunnel not working
```bash
# Check cloudflared status
sudo launchctl list | grep cloudflare

# Restart tunnel
sudo launchctl stop com.cloudflare.cloudflared
sudo launchctl start com.cloudflare.cloudflared
```

### Ollama not responding
```bash
# Check status
brew services list | grep ollama

# Restart
brew services restart ollama

# Check if listening
lsof -i :11434
```

---

## Files & Locations Summary

```
# Binaries
/opt/homebrew/bin/ollama              # Ollama
/opt/homebrew/bin/cloudflared         # Cloudflare tunnel
/Users/gta/.local/bin/open-webui      # Open WebUI

# Data
/Users/gta/Open-WebUI/                # Open WebUI data (database, uploads)
/Users/gta/.ollama/models/            # Downloaded LLM models
/Users/gta/Documents/LLM-Docs/        # Shared documents folder

# Logs
/tmp/open-webui.log                   # Open WebUI logs
/tmp/cloudflared.log                  # Tunnel logs

# Config
~/Library/LaunchAgents/com.openwebui.serve.plist        # Open WebUI auto-start
/Library/LaunchDaemons/com.cloudflare.cloudflared.plist # Tunnel auto-start

# Custom Functions (paste into Open WebUI)
/Users/gta/SRC/Local LLM/gta_pipe.py                    # GTA Smart Router function
/Users/gta/SRC/Local LLM/gta_file_reader_tool.py        # GTA File Reader tool
```

---

## Completed Setup

- [x] Install Ollama via Homebrew
- [x] Download DeepSeek-R1 671B (404GB)
- [x] Download GPT-OSS 120B (65GB)
- [x] Download Llama 3.2 Vision 90B (54GB)
- [x] Install Open WebUI via pipx
- [x] Configure auto-start for all services
- [x] Set up permanent Cloudflare tunnel (gta.ironlinkconnect.com)
- [x] Enable web search (DuckDuckGo)
- [x] Configure multi-model support
- [x] Move data to clean location (/Users/gta/Open-WebUI/)
- [x] Enable Bot Fight Mode on Cloudflare
- [x] Configure SSL/HTTPS (Always Use HTTPS)
- [x] GTA Smart Router (auto vision/text model selection)
- [x] GTA File Reader Tool (direct folder access)

## Optional Future Enhancements

- [ ] Configure Cloudflare Access for additional security
- [ ] Build React Native app for iOS/Android
- [ ] Set up Cloudflare rate limiting (requires paid plan for >10s)
- [ ] Add more models (Qwen 3 72B for faster chat)

---

*Last updated: 2026-01-21*
