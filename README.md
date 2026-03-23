# 🌐 Browsr

> AI-powered [Helium](https://github.com/mherrmann/helium) script generator for your terminal.

Describe what you want the browser to do in plain English — Browsr writes the Helium Python code instantly.

```
╔══════════════════════════════════════════════╗
║  B R O W S R  •  Helium Script Generator    ║
╚══════════════════════════════════════════════╝

  🌐 Task > open 10 tabs in chrome and load google.com in each

  from helium import *
  import time

  driver = start_chrome('https://google.com')

  for i in range(9):
      press(CONTROL + 't')
      go_to('https://google.com')
      time.sleep(0.5)

  kill_browser()
```

---

## ✨ Features

- **Interactive REPL** — type tasks, get Helium scripts instantly
- **One-shot mode** — pipe tasks in scripts or CI
- **Save scripts** — output directly to `.py` files
- **Works with any OpenAI-compatible API** — OpenAI, OpenRouter, Groq, Mistral, Cerebras, etc.
- **AES-256-GCM encryption** — your API key and config are encrypted at rest with bank-grade security
- **Auto-updater** — `browsr update` pulls the latest version

---

## 🔐 Security

Your API key and all config data are encrypted using:

- **AES-256-GCM** — authenticated encryption (prevents tampering)
- **PBKDF2-HMAC-SHA256** — 310,000 iterations (OWASP 2023 standard)
- **Machine-locked** — derived from your MAC address + hostname, so the encrypted file can't be decrypted on another machine
- **Permissions** — config file is `chmod 600` (owner-only read/write)

Config is stored at: `~/.browsr/config.enc`

---

## 🚀 Installation

### Clone and install

```bash
git clone https://github.com/yourusername/browsr.git
cd browsr
pip install -e .
```

### Virtual environment (recommended)

```bash
git clone https://github.com/yourusername/browsr.git
cd browsr
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

You'll also need Chrome or Firefox installed, plus ChromeDriver/GeckoDriver on your PATH.

---

## 📋 Commands

| Command | Description |
|---|---|
| `browsr` | Start interactive REPL |
| `browsr "task"` | Generate script for a task (one-shot) |
| `browsr "task" -o file.py` | Generate + save to file |
| `browsr menu` | Show all commands and help |
| `browsr key` | Set or change your API key (hidden input, encrypted) |
| `browsr update` | Update Browsr to the latest version |
| `browsr config --show` | View current config |
| `browsr config --key <key>` | Set API key via flag |
| `browsr config --model <model>` | Set LLM model |
| `browsr config --base-url <url>` | Set custom API base URL |

---

## ⚙️ Setup

### Step 1 — Set your API key

The recommended way (hidden input, encrypted with AES-256-GCM):

```bash
browsr key
```

Or via config flag:

```bash
browsr config --key sk-YOUR_API_KEY_HERE
```

### Step 2 — (Optional) Set model and API base

```bash
browsr config --model gpt-4o
browsr config --base-url https://openrouter.ai/api/v1
```

### View your config

```bash
browsr config --show
```

---

## 🆓 Using free APIs

**Groq** (fast + free, 14,400 req/day):
```bash
browsr config --key gsk_YOUR_GROQ_KEY
browsr config --base-url https://api.groq.com/openai/v1
browsr config --model llama-3.3-70b-versatile
```

**OpenRouter** (free models):
```bash
browsr config --key sk-or-YOUR_KEY
browsr config --base-url https://openrouter.ai/api/v1
browsr config --model google/gemma-3-27b-it:free
```

**Cerebras** (very fast + free, 1M tokens/day):
```bash
browsr config --key csk-YOUR_KEY
browsr config --base-url https://api.cerebras.ai/v1
browsr config --model llama3.1-8b
```

---

## 💬 Usage

### Interactive mode

```bash
browsr
```

```
🌐 Task > open 10 tabs in chrome
🌐 Task > login to github with username johndoe
🌐 Task > go to reddit, open the first 5 posts in new tabs
🌐 Task > fill in a contact form with name "John" email "john@example.com"
🌐 Task > take a screenshot of apple.com
```

**REPL shortcuts:**

```
save login.py login to github          # Generate + save directly
task description --save output.py      # Alternative save syntax
menu                                   # Show help in REPL
key                                    # Change API key in REPL
update                                 # Update in REPL
exit                                   # Quit
```

### One-shot mode

```bash
browsr "open google and search for cats"
browsr "fill in a contact form" -o contact_form.py
browsr "search google" --key sk-OTHER --model gpt-4-turbo
```

### Updating

```bash
browsr update
```

Checks PyPI for the latest version and runs `pip install --upgrade browsr` automatically.

---

## 🔧 Helium quick reference

```python
from helium import *

start_chrome('google.com')        # Open Chrome
go_to('url')                      # Navigate
write('text', into='Field')       # Type into field
click('Button Text')              # Click by visible text
press(ENTER)                      # Press key
press(CONTROL + 't')              # New tab
scroll_down(200)                  # Scroll
wait_until(Button('X').exists)    # Wait for element
find_all(S('a'))                  # Find all elements
get_driver().save_screenshot('s.png')  # Screenshot
kill_browser()                    # Close browser
```

Full cheatsheet: https://github.com/mherrmann/helium/blob/master/docs/cheatsheet.md

---

## 📄 License

MIT
