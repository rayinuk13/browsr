#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════╗
║           B R O W S R                        ║
║   AI-powered Helium script generator         ║
║   Type a task → get Helium Python code       ║
╚══════════════════════════════════════════════╝
"""

import os
import sys
import json
import base64
import getpass
import hashlib
import argparse
import textwrap
import subprocess
import urllib.request
import urllib.error
from pathlib import Path

# ─── Optional deps check ──────────────────────────────────────────────────────

def require(package, pip_name=None):
    import importlib
    try:
        return importlib.import_module(package)
    except ImportError:
        name = pip_name or package
        print(f"  ❌  Missing package: {name}")
        print(f"  Run: pip install {name}")
        sys.exit(1)

# ─── Constants ────────────────────────────────────────────────────────────────

BROWSR_DIR  = Path.home() / ".browsr"
CONFIG_FILE = BROWSR_DIR / "config.enc"
VERSION     = "1.2.0"
PYPI_URL    = "https://pypi.org/pypi/browsr/json"

BANNER = """
╔══════════════════════════════════════════════╗
║  B R O W S R  •  Helium Script Generator    ║
║  v{ver:<39}║
╚══════════════════════════════════════════════╝
""".format(ver=VERSION)

DIVIDER = "─" * 52

# ─── AES-256-GCM Encryption ───────────────────────────────────────────────────
# AES-256-GCM authenticated encryption + PBKDF2-HMAC-SHA256 key derivation
# Each write generates a fresh random salt (32B) and IV (12B).
# Config is machine-locked: derived from MAC address + hostname.
# File permissions: chmod 600 (owner read/write only).

def _get_machine_secret() -> bytes:
    import platform, uuid
    sources = [
        str(uuid.getnode()),
        platform.node(),
        str(Path.home()),
        "browsr-aes256gcm-v1",
    ]
    return hashlib.sha256("|".join(sources).encode()).digest()

def _derive_key(password: bytes, salt: bytes) -> bytes:
    """PBKDF2-HMAC-SHA256 — 310,000 iterations (OWASP 2023)."""
    return hashlib.pbkdf2_hmac("sha256", password, salt, 310_000)

def encrypt_data(plaintext: str) -> bytes:
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    except ImportError:
        print("  ❌  cryptography package required.\n  Run: pip install cryptography")
        sys.exit(1)
    salt   = os.urandom(32)
    iv     = os.urandom(12)
    key    = _derive_key(_get_machine_secret(), salt)
    token  = AESGCM(key).encrypt(iv, plaintext.encode(), None)
    return base64.b64encode(salt + iv + token)

def decrypt_data(token: bytes) -> str:
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        from cryptography.exceptions import InvalidTag
    except ImportError:
        print("  ❌  cryptography package required.\n  Run: pip install cryptography")
        sys.exit(1)
    try:
        raw  = base64.b64decode(token)
        salt, iv, ct = raw[:32], raw[32:44], raw[44:]
        key  = _derive_key(_get_machine_secret(), salt)
        return AESGCM(key).decrypt(iv, ct, None).decode()
    except Exception:
        print("  ❌  Decryption failed. Config may be corrupted or from another machine.")
        sys.exit(1)

# ─── Config ───────────────────────────────────────────────────────────────────

def load_config() -> dict:
    if not CONFIG_FILE.exists():
        return {}
    try:
        return json.loads(decrypt_data(CONFIG_FILE.read_bytes()))
    except Exception:
        return {}

def save_config(config: dict):
    BROWSR_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_bytes(encrypt_data(json.dumps(config)))
    CONFIG_FILE.chmod(0o600)

def get_api_key(args_key=None):
    if args_key: return args_key
    return os.environ.get("OPENAI_API_KEY") or os.environ.get("BROWSR_API_KEY") or load_config().get("api_key")

def get_model(args_model=None):
    return args_model or load_config().get("model", "gpt-4o")

def get_base_url(args_url=None):
    return args_url or load_config().get("base_url")

# ─── Helium system prompt (complete official API v7.0.0) ─────────────────────

HELIUM_SYSTEM_PROMPT = """You are Browsr — an expert at writing Helium Python automation scripts.
Helium is a high-level Python browser automation library built on Selenium.
You have deep knowledge of the complete Helium v7.0.0 API.

════════════════════════════════════════════════
 COMPLETE HELIUM API REFERENCE (v7.0.0)
════════════════════════════════════════════════

IMPORT:
  from helium import *

──────────────────────────────────────────────
 BROWSER CONTROL
──────────────────────────────────────────────

start_chrome(url=None, headless=False, maximize=False, options=None)
  # Start Chrome. Auto-downloads ChromeDriver if needed (Selenium Manager).
  start_chrome()
  start_chrome('google.com')
  start_chrome(headless=True)
  start_chrome('google.com', headless=True)
  start_chrome(maximize=True)
  # Advanced — with ChromeOptions:
  from selenium.webdriver import ChromeOptions
  options = ChromeOptions()
  options.add_argument('--proxy-server=1.2.3.4:5678')
  start_chrome(options=options)

start_firefox(url=None, headless=False, options=None, profile=None)
  # Start Firefox.
  start_firefox()
  start_firefox('google.com')
  start_firefox(headless=True)
  # Advanced — with FirefoxOptions:
  from selenium.webdriver import FirefoxOptions
  options = FirefoxOptions()
  options.add_argument('--width=2560')
  start_firefox(options=options)
  # Advanced — with FirefoxProfile (proxy, user-agent, etc.):
  from selenium.webdriver import FirefoxProfile
  profile = FirefoxProfile()
  profile.set_preference('general.useragent.override', 'Mozilla/5.0 ...')
  start_firefox(profile=profile)

go_to(url)
  go_to('google.com')
  go_to('https://github.com/login')

refresh()
  # Refreshes / reloads the current page.
  refresh()

kill_browser()
  # Closes the browser and cleans up all resources.
  kill_browser()

get_driver()
  # Returns the underlying Selenium WebDriver instance.
  # Use for any Selenium-level operation Helium doesn't cover.
  driver = get_driver()
  driver.execute_script("alert('hi')")
  driver.save_screenshot('shot.png')

set_driver(driver)
  # Set the Selenium WebDriver Helium should use.
  # Useful when you create your own driver instance.
  from selenium import webdriver
  driver = webdriver.Chrome()
  set_driver(driver)

──────────────────────────────────────────────
 INTERACTION
──────────────────────────────────────────────

click(element)
  # Click by visible text, element type, Point, or WebElement.
  click('Sign in')
  click(Button('OK'))
  click(Link('Download'))
  click(Image('logo'))
  click(CheckBox('Remember me'))
  click(Point(200, 300))
  click(ComboBox('File type').top_left + (50, 0))

doubleclick(element)
  # NOTE: the function name is doubleclick (NOT double_click)
  doubleclick('item')
  doubleclick(Image('icon'))
  doubleclick(Point(200, 300))
  doubleclick(TextField('Username').top_left - (0, 20))

rightclick(element)
  # NOTE: the function name is rightclick (NOT right_click)
  rightclick('element')
  rightclick(Point(200, 300))
  rightclick(Image('captcha'))

hover(element)
  hover('File size')
  hover(Button('OK'))
  hover(Link('Download'))
  hover(Point(200, 300))
  hover(ComboBox('File type').top_left + (50, 0))

write(text, into=None)
  write('Hello World!')
  write('user@email.com', into='Email')
  write('password123', into=TextField('Password'))
  write('Michael', into=Alert('Please enter your name'))

press(key)
  # Keys available: ENTER, TAB, ESCAPE, SPACE, BACK_SPACE, DELETE,
  # CONTROL, ALT, SHIFT, COMMAND, F1–F12, ARROW_UP, ARROW_DOWN,
  # ARROW_LEFT, ARROW_RIGHT, HOME, END, PAGE_UP, PAGE_DOWN, INSERT
  press(ENTER)
  press(TAB)
  press(ESCAPE)
  press(CONTROL + 'a')     # Select all
  press(CONTROL + 'c')     # Copy
  press(CONTROL + 'v')     # Paste
  press(CONTROL + 'z')     # Undo
  press(CONTROL + 't')     # New tab
  press(CONTROL + 'w')     # Close tab
  press(CONTROL + SHIFT + 't')  # Reopen closed tab
  press(ALT + ARROW_LEFT)  # Browser back
  press(ALT + ARROW_RIGHT) # Browser forward
  press(F5)                # Refresh

select(combo_box, value)
  # Select a value from a ComboBox / <select> dropdown.
  select('Language', 'English')
  select(ComboBox('Country'), 'United States')

drag(element, to)
  # Drag element inside the page.
  drag('Drag me!', to='Drop here.')
  drag(Image('card'), to=Text('Target zone'))

drag_file(filename, to)
  # Drag a file FROM DISK onto a browser element (e.g. upload zone).
  drag_file('/path/to/file.pdf', to='Drop files here')

attach_file(filename, to=None)
  # Attach a file to a file-input element.
  attach_file('/path/to/file.jpg', to='Profile picture')
  attach_file('/path/to/doc.pdf', to=TextField('Upload'))

scroll_down(num_pixels=100)
  scroll_down(200)

scroll_up(num_pixels=100)
  scroll_up(200)

scroll_right(num_pixels=100)
  scroll_right(300)

scroll_left(num_pixels=100)
  scroll_left(300)

highlight(element)
  # Highlights an element visually (useful for debugging scripts).
  highlight('Username')
  highlight(Button('Submit'))
  highlight(Link('About'))

──────────────────────────────────────────────
 ELEMENT TYPES
──────────────────────────────────────────────

All elements support:
  element.exists()          # True/False — check if on page
  element.web_element       # Underlying Selenium WebElement
  element.x, element.y     # Coordinates
  element.top_left          # Point at top-left corner (useful for offsets)

Text('visible text')
  Text('Accept cookies?').exists()
  name = Text(to_right_of='Name:', below=Image(alt='Profile')).value

Link('text')
  Link('Sign in').exists()
  Link('Download').href      # Get the href URL

Button('text')
  Button('Submit').exists()
  Button('Submit').is_enabled()   # True if clickable

TextField('label')
  TextField('Search').value       # Get current value
  TextField('Email').is_enabled()
  TextField('Email').is_editable()

ComboBox('label')
  ComboBox('Country').value       # Current selected value
  ComboBox('Country').options     # List of all available options
  ComboBox('Country').is_editable() # True if user can type into it

CheckBox('label')
  CheckBox('Remember me').is_enabled()
  CheckBox('Remember me').is_checked()  # True if ticked

RadioButton('label')
  RadioButton('Option A').is_selected() # True if selected

Image(alt='text')
  Image(alt='Logo').exists()

ListItem('text')
  # Matches <li> items
  ListItem('First item').exists()
  find_all(ListItem())  # Get all list items

Window(title=None)
  # Represents a browser window/tab.
  Window('Page title').exists()
  Window('Page title').title    # Window title string
  Window('Page title').handle   # Selenium window handle
  find_all(Window())            # Get all open windows/tabs

Alert()
  Alert().text          # Text shown in the popup
  Alert().accept()      # Click OK
  Alert().dismiss()     # Click Cancel
  write('value', into=Alert())  # Type into a prompt dialog

S(selector)
  # Selector — CSS, XPath, or HTML name
  S('#myId')            # CSS id
  S('.myClass')         # CSS class
  S('table > tr > td')  # CSS selector
  S('//div[@id="x"]')   # XPath (starts with //)
  S('@inputName')       # HTML name attribute (starts with @)

Point(x, y)
  p = Point(100, 200)
  click(p)
  click(Point(100, 200) + (20, -10))  # Offset arithmetic
  p.x   # x coordinate
  p.y   # y coordinate

──────────────────────────────────────────────
 FINDING ELEMENTS RELATIVE TO OTHERS
──────────────────────────────────────────────

# Use above=, below=, to_left_of=, to_right_of= to narrow searches
Text(above='Balance', below='Transactions').value
Link(to_right_of='Invoice:')
Image(to_right_of=Link('Sign in', below=Text('Navigation')))
Button(to_right_of=Text('Delete'), above=Link('Cancel'))

──────────────────────────────────────────────
 FIND ALL
──────────────────────────────────────────────

find_all(predicate)
  # Returns a list of all matching elements
  find_all(Button('Open'))
  find_all(Window())
  find_all(TextField('Address line 1'))
  find_all(S('table > tr > td', below='Email'))

  # Sort by position:
  buttons = find_all(Button('Open'))
  leftmost = sorted(buttons, key=lambda b: b.x)[0]
  topmost  = sorted(buttons, key=lambda b: b.y)[0]

  # Extract text from all cells:
  cells  = find_all(S('td'))
  values = [c.web_element.text for c in cells]

──────────────────────────────────────────────
 WAITING
──────────────────────────────────────────────

wait_until(condition, timeout_secs=10, interval_secs=0.5)
  wait_until(Button('Download').exists)
  wait_until(Text('Success').exists)
  wait_until(lambda: TextField('Balance').value == '$2M')
  wait_until(lambda: len(find_all(S('tr'))) > 5)

Config.implicit_wait_secs = 10   # Default wait for elements (seconds)
Config.implicit_wait_secs = 30   # Increase for slow pages

──────────────────────────────────────────────
 WINDOW & TAB MANAGEMENT
──────────────────────────────────────────────

# Helium's switch_to() — switch by window title
switch_to('Page title')
switch_to(Window('Gmail'))

# Selenium-level tab operations (via get_driver()):
driver = get_driver()
driver.execute_script("window.open('https://example.com')")  # Open new tab
driver.switch_to.window(driver.window_handles[0])            # Switch to tab by index
driver.switch_to.window(driver.window_handles[-1])           # Switch to last tab
len(driver.window_handles)                                    # Count open tabs

# Open N tabs:
for i in range(9):
    press(CONTROL + 't')

# Close current tab:
press(CONTROL + 'w')

──────────────────────────────────────────────
 SCREENSHOT & DEBUGGING
──────────────────────────────────────────────

get_driver().save_screenshot('screenshot.png')
highlight(Button('Login'))    # Yellow highlight for visual debugging

──────────────────────────────────────────────
 MIXING HELIUM + SELENIUM
──────────────────────────────────────────────

# Get Selenium WebDriver from Helium:
driver = get_driver()

# Run JavaScript:
driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
driver.execute_script("return document.title")

# Get Selenium WebElement from Helium element:
el = Button('Submit').web_element
el.get_attribute('class')
el.get_attribute('data-id')
el.is_displayed()
el.is_enabled()

# ActionChains for complex interactions:
from selenium.webdriver.common.action_chains import ActionChains
ActionChains(driver).move_to_element(Link('Menu').web_element).perform()

════════════════════════════════════════════════
 GENERATION RULES
════════════════════════════════════════════════

1.  Always start with: from helium import *
2.  Always end with: kill_browser()  — unless user says keep it open
3.  Use high-level Helium commands first; fall back to Selenium only when needed
4.  ALWAYS use doubleclick() not double_click(), rightclick() not right_click()
5.  For multi-tab work use driver = get_driver() + window_handles
6.  Add clear # comments explaining each step
7.  Import extra stdlib modules as needed (time, os, re, etc.)
8.  Use wait_until() instead of time.sleep() wherever possible
9.  Only use time.sleep() for unavoidable timing gaps
10. Output ONLY valid Python code — NO markdown fences, NO explanations
11. Write clean, readable, production-quality code
12. Check element existence before interacting when appropriate:
      if Button('Accept').exists(): click('Accept')
13. For data extraction use find_all() + .web_element.text
14. For form automation use write() + select() + click()
15. For file operations use attach_file() or drag_file()
16. For popups/alerts always use Alert() class
17. For ComboBox (dropdowns) use select() or ComboBox().options to list choices
"""

# ─── Code generation ──────────────────────────────────────────────────────────

def generate_helium_code(prompt: str, api_key: str, model: str, base_url: str = None) -> str:
    from openai import OpenAI
    kwargs = {"api_key": api_key}
    if base_url:
        kwargs["base_url"] = base_url
    client   = OpenAI(**kwargs)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": HELIUM_SYSTEM_PROMPT},
            {"role": "user",   "content": f"Write a Helium Python script that does:\n\n{prompt}"}
        ],
        temperature=0.2,
    )
    code = response.choices[0].message.content.strip()
    if code.startswith("```"):
        lines = code.split("\n")
        end   = -1 if lines[-1].strip() == "```" else len(lines)
        code  = "\n".join(lines[1:end])
        if code.startswith("python\n"):
            code = code[7:]
    return code

# ─── Output ───────────────────────────────────────────────────────────────────

def print_code(code: str, task: str):
    print(BANNER)
    print(f"  Task: {task}")
    print(DIVIDER)
    print()
    print(code)
    print()
    print(DIVIDER)

def save_code(code: str, output_path: str):
    with open(output_path, "w") as f:
        f.write(code)
    print(f"  ✅  Saved to: {output_path}")

# ─── Menu ─────────────────────────────────────────────────────────────────────

def show_menu():
    print(BANNER)
    print("  COMMANDS")
    print(DIVIDER)
    print()
    print("  browsr                         Interactive REPL mode")
    print("  browsr \"<task>\"                One-shot script generation")
    print("  browsr \"<task>\" -o file.py     Generate + save to file")
    print()
    print("  browsr menu                    Show this menu")
    print("  browsr key                     Set or update API key (hidden + encrypted)")
    print("  browsr update                  Update Browsr to latest version")
    print()
    print("  browsr config --show           View current config")
    print("  browsr config --key <key>      Set API key")
    print("  browsr config --model <model>  Set LLM model")
    print("  browsr config --base-url <url> Set custom API base URL")
    print()
    print("  REPL SHORTCUTS")
    print(DIVIDER)
    print()
    print("  save <file.py> <task>          Generate + save in one go")
    print("  <task> --save <file.py>        Alternative save syntax")
    print("  menu                           Show this menu in REPL")
    print("  key                            Change API key in REPL")
    print("  update                         Update Browsr in REPL")
    print("  exit / quit / q               Exit REPL")
    print()
    print("  EXAMPLES")
    print(DIVIDER)
    print()
    print('  browsr "open 10 tabs in chrome and load google.com in each"')
    print('  browsr "login to github with my credentials" -o login.py')
    print('  browsr "scrape all product names and prices from a page"')
    print('  browsr "fill out a contact form with fake data"')
    print('  browsr "take a screenshot of apple.com homepage"')
    print('  browsr "wait for a loading spinner to disappear then click Download"')
    print()
    print("  FREE API PROVIDERS")
    print(DIVIDER)
    print()
    print("  Groq (14,400 req/day):  https://console.groq.com")
    print("    --base-url https://api.groq.com/openai/v1")
    print("    --model llama-3.3-70b-versatile")
    print()
    print("  Cerebras (1M tok/day):  https://cloud.cerebras.ai")
    print("    --base-url https://api.cerebras.ai/v1")
    print("    --model llama3.1-8b")
    print()
    print("  OpenRouter (free models): https://openrouter.ai")
    print("    --base-url https://openrouter.ai/api/v1")
    print("    --model google/gemma-3-27b-it:free")
    print()
    print("  Google AI Studio (free): https://aistudio.google.com")
    print("    --base-url https://generativelanguage.googleapis.com/v1beta/openai")
    print("    --model gemini-2.0-flash")
    print()
    print(DIVIDER)
    print(f"  Version    : {VERSION}")
    print(f"  Config     : {CONFIG_FILE}")
    print(f"  Encryption : AES-256-GCM + PBKDF2-HMAC-SHA256 (310k iterations)")
    print(f"  Helium API : v7.0.0 (complete)")
    print()

# ─── browsr key ───────────────────────────────────────────────────────────────

def cmd_key():
    print(BANNER)
    config  = load_config()
    existing = config.get("api_key", "")
    if existing:
        masked = existing[:8] + "..." + existing[-4:]
        print(f"  Current key: {masked}")
        print()
    print("  Enter your new API key (input is hidden):")
    print("  Works with: OpenAI, Groq, OpenRouter, Cerebras, Mistral, Google AI...\n")
    try:
        key = getpass.getpass("  API Key: ").strip()
    except KeyboardInterrupt:
        print("\n\n  Cancelled.\n"); return
    if not key:
        print("\n  ⚠️  No key entered. Aborted.\n"); return
    config["api_key"] = key
    save_config(config)
    masked = key[:8] + "..." + key[-4:] if len(key) > 12 else "****"
    print(f"\n  ✅  API key saved & encrypted (AES-256-GCM): {masked}")
    print(f"  📁  Config: {CONFIG_FILE}\n")

# ─── browsr update ────────────────────────────────────────────────────────────

def cmd_update():
    print(BANNER)
    print(f"  Current version : {VERSION}")
    print(f"  Checking for updates...\n")
    latest = None
    try:
        req = urllib.request.Request(PYPI_URL, headers={"User-Agent": "browsr-updater"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            latest = json.loads(resp.read())["info"]["version"]
    except Exception:
        pass
    if latest:
        print(f"  Latest version  : {latest}")
        if latest == VERSION:
            print(f"\n  ✅  Already up to date!\n"); return
        print(f"  🆕  Update available: {VERSION} → {latest}\n")
    else:
        print("  ℹ️  Could not check PyPI — running upgrade anyway.\n")
    print("  Running: pip install --upgrade browsr\n")
    print(DIVIDER)
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "browsr"], check=True)
        print(DIVIDER)
        print("\n  ✅  Browsr updated! Restart your terminal to use the new version.\n")
    except subprocess.CalledProcessError:
        print(DIVIDER)
        print("\n  ❌  Update failed. Try: pip install --upgrade browsr\n")
    except FileNotFoundError:
        print("\n  ❌  pip not found. Install pip and try again.\n")

# ─── REPL ─────────────────────────────────────────────────────────────────────

def run_repl(api_key: str, model: str, base_url: str = None):
    print(BANNER)
    print(f"  Model : {model}")
    if base_url:
        print(f"  API   : {base_url}")
    print(f"\n  Describe a browser task in plain English.")
    print(f"  Type 'menu' for all commands, 'exit' to quit.\n")
    print(DIVIDER)

    while True:
        try:
            task = input("\n  🌐 Task > ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\n  Bye! 👋\n"); break

        if not task: continue
        if task.lower() in ("exit", "quit", "q"):
            print("\n  Bye! 👋\n"); break
        if task.lower() == "menu":
            show_menu(); continue
        if task.lower() == "key":
            cmd_key()
            api_key = get_api_key(); continue
        if task.lower() == "update":
            cmd_update(); continue

        save_path = None
        if task.lower().startswith("save "):
            parts = task.split(" ", 2)
            if len(parts) >= 3:
                save_path, task = parts[1], parts[2]
            else:
                print("  ⚠️  Usage: save <filename.py> <task description>"); continue
        elif " --save " in task:
            parts = task.split(" --save ")
            task, save_path = parts[0].strip(), parts[1].strip()

        print(f"\n  ⏳ Generating...")
        try:
            code = generate_helium_code(task, api_key, model, base_url)
            print_code(code, task)
            if save_path:
                save_code(code, save_path)
            else:
                try:
                    ans = input("  💾 Save to file? Enter filename or press Enter to skip: ").strip()
                    if ans: save_code(code, ans)
                except (KeyboardInterrupt, EOFError):
                    print()
        except Exception as e:
            print(f"\n  ❌  Error: {e}\n")

# ─── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        prog="browsr",
        description="Browsr — AI-powered Helium Python script generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
        Commands:
          browsr                          Interactive REPL
          browsr "task description"       One-shot generation
          browsr "task" -o script.py      Generate + save
          browsr menu                     Show all commands
          browsr key                      Set/change API key (encrypted)
          browsr update                   Update to latest version
          browsr config --show            View config
          browsr config --key <key>       Set API key
          browsr config --model <model>   Set model
          browsr config --base-url <url>  Set API base URL
        """)
    )

    sub = parser.add_subparsers(dest="command")

    cfg = sub.add_parser("config", help="Configure Browsr")
    cfg.add_argument("--key");  cfg.add_argument("--model")
    cfg.add_argument("--base-url", dest="base_url")
    cfg.add_argument("--show", action="store_true")

    sub.add_parser("menu",   help="Show command menu")
    sub.add_parser("key",    help="Set/update API key securely")
    sub.add_parser("update", help="Update Browsr to latest version")

    parser.add_argument("task", nargs="?")
    parser.add_argument("-k", "--key")
    parser.add_argument("-m", "--model")
    parser.add_argument("-o", "--output")
    parser.add_argument("--base-url", dest="base_url")

    args = parser.parse_args()

    if args.command == "menu":
        show_menu(); return
    if args.command == "key":
        cmd_key(); return
    if args.command == "update":
        cmd_update(); return

    if args.command == "config":
        config  = load_config()
        changed = False
        if args.key:
            config["api_key"] = args.key
            print("  ✅  API key saved & encrypted."); changed = True
        if args.model:
            config["model"] = args.model
            print(f"  ✅  Model set to: {args.model}"); changed = True
        if args.base_url:
            config["base_url"] = args.base_url
            print(f"  ✅  Base URL set to: {args.base_url}"); changed = True
        if args.show or not changed:
            k = config.get("api_key", "")
            masked = (k[:8] + "..." + k[-4:]) if len(k) > 12 else ("set" if k else "not set")
            print(f"\n  API key    : {masked}")
            print(f"  Model      : {config.get('model', 'gpt-4o (default)')}")
            print(f"  Base URL   : {config.get('base_url', 'https://api.openai.com/v1 (default)')}")
            print(f"  Config     : {CONFIG_FILE}")
            print(f"  Encryption : AES-256-GCM + PBKDF2-HMAC-SHA256 (310k iterations)\n")
        if changed:
            save_config(config)
        return

    api_key  = get_api_key(getattr(args, "key", None))
    model    = get_model(getattr(args, "model", None))
    base_url = get_base_url(getattr(args, "base_url", None))

    if not api_key:
        print(BANNER)
        print("  ❌  No API key found.\n")
        print("  Quick setup:")
        print("    browsr key               ← recommended (hidden input)")
        print("    browsr config --key sk-XX\n")
        sys.exit(1)

    if args.task:
        print(f"\n  ⏳ Generating Helium script...")
        try:
            code = generate_helium_code(args.task, api_key, model, base_url)
            print_code(code, args.task)
            if args.output:
                save_code(code, args.output)
        except Exception as e:
            print(f"\n  ❌  Error: {e}\n"); sys.exit(1)
        return

    run_repl(api_key, model, base_url)


if __name__ == "__main__":
    main()
