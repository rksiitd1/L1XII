#!/usr/bin/env python3
"""
NCERT Textbook Downloader
=========================
Downloads NCERT textbooks using cached catalog from scanner.py.
Run 'python scanner.py' first to build the catalog.
"""
import os, sys, json, time, zipfile, shutil
from pathlib import Path
from typing import Optional, List, Dict

try:
    import requests
except ImportError:
    os.system(f"{sys.executable} -m pip install requests -q")
    import requests

try:
    from tqdm import tqdm
except ImportError:
    os.system(f"{sys.executable} -m pip install tqdm -q")
    from tqdm import tqdm

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════
BASE_URL = "https://ncert.nic.in/textbook/pdf/"
CATALOG_FILE = Path(__file__).parent / "catalog.json"

LANG_NAMES = {'e':'English', 'h':'Hindi', 'u':'Urdu'}

# Colors
C = type('C', (), {
    'R':'\033[91m','G':'\033[92m','Y':'\033[93m','B':'\033[94m',
    'M':'\033[95m','C':'\033[96m','W':'\033[97m','D':'\033[90m',
    'BD':'\033[1m','E':'\033[0m'
})()

# ═══════════════════════════════════════════════════════════════════════════════
# CATALOG LOADING
# ═══════════════════════════════════════════════════════════════════════════════
def load_catalog() -> Optional[Dict]:
    """Load catalog from JSON file."""
    if not CATALOG_FILE.exists():
        return None
    try:
        with open(CATALOG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return None

# ═══════════════════════════════════════════════════════════════════════════════
# UTILITIES
# ═══════════════════════════════════════════════════════════════════════════════
def tw(): 
    try: return shutil.get_terminal_size().columns
    except: return 80

def cls(): 
    os.system('cls' if os.name=='nt' else 'clear')

def banner():
    w = tw()
    print(f"{C.C}{C.BD}")
    print(f"┌{'─'*(w-2)}┐")
    art = [
        "  ███╗   ██╗ ██████╗███████╗██████╗ ████████╗",
        "  ████╗  ██║██╔════╝██╔════╝██╔══██╗╚══██╔══╝",
        "  ██╔██╗ ██║██║     █████╗  ██████╔╝   ██║   ",
        "  ██║╚██╗██║██║     ██╔══╝  ██╔══██╗   ██║   ",
        "  ██║ ╚████║╚██████╗███████╗██║  ██║   ██║   ",
        "  ╚═╝  ╚═══╝ ╚═════╝╚══════╝╚═╝  ╚═╝   ╚═╝   ",
    ]
    for line in art:
        pad = (w - 2 - len(line)) // 2
        print(f"│{' '*pad}{line}{' '*(w-2-pad-len(line))}│")
    title = "📚 NCERT Textbook Downloader 📚"
    pad = (w - 2 - len(title)) // 2
    print(f"│{' '*pad}{title}{' '*(w-2-pad-len(title))}│")
    print(f"└{'─'*(w-2)}┘{C.E}")

def hdr(txt):
    print(f"\n{C.Y}{'─'*tw()}{C.E}")
    print(f"{C.BD}{C.G} {txt}{C.E}")

def grid_menu(title, options, cols=4):
    """Display options in a compact grid."""
    hdr(title)
    if not options:
        print(f"  {C.R}No options available{C.E}")
        return None
    
    max_len = max(len(str(o)) for o in options) + 6
    w = tw() - 2
    cols = max(1, min(cols, w // max_len))
    col_w = w // cols
    
    for i, opt in enumerate(options):
        idx = f"[{i+1:2d}]" if len(options) > 9 else f"[{i+1}]"
        cell = f" {C.C}{idx}{C.E} {opt}"
        vis_len = len(idx) + len(str(opt)) + 2
        padding = col_w - vis_len
        print(cell + ' '*max(0,padding), end='')
        if (i+1) % cols == 0: print()
    if len(options) % cols != 0: print()
    
    print(f"\n {C.R}[0]{C.E} Back/Exit")
    
    while True:
        try:
            ch = input(f" {C.BD}►{C.E} ").strip()
            if ch == '': continue
            n = int(ch)
            if n == 0: return None
            if 1 <= n <= len(options): return n - 1
            print(f" {C.R}Invalid{C.E}", end='\r')
        except ValueError:
            print(f" {C.R}Number please{C.E}", end='\r')

# ═══════════════════════════════════════════════════════════════════════════════
# DOWNLOAD FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════
def make_folder(class_num: int, subject: str, is_chapter=False) -> Path:
    folder = Path(__file__).parent / "NCERT" / f"Class_{class_num}" / subject.replace(' ','_')
    if is_chapter: folder = folder / "chapters"
    folder.mkdir(parents=True, exist_ok=True)
    return folder

def download(url: str, path: Path) -> bool:
    try:
        r = requests.get(url, stream=True, timeout=30)
        r.raise_for_status()
        size = int(r.headers.get('content-length', 0))
        
        print(f"\n {C.C}⬇ {path.name}{C.E} ({size/(1024*1024):.1f} MB)")
        
        with open(path, 'wb') as f:
            with tqdm(total=size, unit='B', unit_scale=True, ncols=50, 
                     bar_format=' {bar}| {n_fmt}/{total_fmt} [{rate_fmt}]') as pb:
                for chunk in r.iter_content(8192):
                    f.write(chunk)
                    pb.update(len(chunk))
        
        print(f" {C.G}✓ Done{C.E}")
        return True
    except Exception as e:
        print(f" {C.R}✗ Failed: {e}{C.E}")
        return False

def download_zip(class_num, subject, book_code):
    url = f"{BASE_URL}{book_code}dd.zip"
    folder = make_folder(class_num, subject)
    path = folder / f"{book_code}dd.zip"
    
    if download(url, path):
        if input(f" Extract? (y/n): ").lower() == 'y':
            try:
                with zipfile.ZipFile(path, 'r') as z:
                    z.extractall(folder / book_code)
                print(f" {C.G}✓ Extracted to {book_code}/{C.E}")
            except: 
                print(f" {C.R}✗ Extract failed{C.E}")
        return True
    return False

def download_chapter(class_num, subject, book_code, chapters):
    labels = []
    for ch in chapters:
        if ch.isdigit() or (len(ch)==2 and ch[0]=='0'):
            labels.append(f"Ch {int(ch)}")
        else:
            labels.append(ch.upper())
    
    idx = grid_menu(f"Select Chapter ({len(chapters)} available)", labels)
    if idx is None: return False
    
    ch = chapters[idx]
    url = f"{BASE_URL}{book_code}{ch}.pdf"
    folder = make_folder(class_num, subject, True)
    return download(url, folder / f"{book_code}{ch}.pdf")

def download_all_chapters(class_num, subject, book_code, chapters):
    folder = make_folder(class_num, subject, True)
    
    print(f"\n {C.G}Downloading {len(chapters)} files...{C.E}")
    ok = 0
    for ch in chapters:
        path = folder / f"{book_code}{ch}.pdf"
        if path.exists():
            print(f" {C.Y}⏭ {path.name} exists{C.E}")
            ok += 1
        elif download(f"{BASE_URL}{book_code}{ch}.pdf", path):
            ok += 1
        time.sleep(0.2)
    
    print(f"\n {C.G}✓ {ok}/{len(chapters)} downloaded{C.E}")
    return ok > 0

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN FLOW (USING CATALOG)
# ═══════════════════════════════════════════════════════════════════════════════
def main():
    catalog = load_catalog()
    
    if not catalog:
        cls()
        banner()
        print(f"\n {C.R}❌ Catalog not found!{C.E}")
        print(f" {C.Y}Please run 'python scanner.py' first to build the catalog.{C.E}\n")
        return
    
    last_updated = catalog.get("last_updated", "Unknown")[:10]
    
    while True:
        cls()
        banner()
        print(f" {C.D}Catalog: {last_updated}{C.E}")
        
        # 1. Select Class
        available_classes = sorted(catalog["classes"].keys(), key=int)
        class_options = [f"Class {c}" for c in available_classes]
        idx = grid_menu("Select Class", class_options)
        if idx is None: break
        class_num = available_classes[idx]
        class_data = catalog["classes"][class_num]
        
        # 2. Select Subject
        subjects = list(class_data.keys())
        idx = grid_menu(f"Subjects for Class {class_num}", subjects, cols=3)
        if idx is None: continue
        subject = subjects[idx]
        subj_data = class_data[subject]
        
        # 3. Select Language
        languages = list(subj_data["languages"].keys())
        if len(languages) == 1:
            lang = languages[0]
            print(f" {C.D}Only {LANG_NAMES[lang]} available{C.E}")
        else:
            lang_names = [LANG_NAMES[l] for l in languages]
            idx = grid_menu("Select Language", lang_names)
            if idx is None: continue
            lang = languages[idx]
        
        lang_data = subj_data["languages"][lang]
        
        # 4. Select Part
        parts = list(lang_data["parts"].keys())
        if len(parts) == 1:
            part = parts[0]
            print(f" {C.D}Only Part {part} available{C.E}")
        else:
            part_names = [f"Part {p}" for p in parts]
            idx = grid_menu("Select Part", part_names)
            if idx is None: continue
            part = parts[idx]
        
        part_data = lang_data["parts"][part]
        book_code = part_data["code"]
        chapters = part_data["chapters"]
        has_zip = part_data.get("has_zip", False)
        
        # Show summary
        print(f"\n{C.Y}{'─'*tw()}{C.E}")
        print(f" {C.BD}{C.G}Class {class_num} │ {LANG_NAMES[lang]} │ {subject} │ Part {part}{C.E}")
        print(f" {C.D}Code: {book_code} │ Chapters: {len(chapters)}{C.E}")
        
        # 5. Download Type
        dl_opts = []
        if has_zip:
            dl_opts.append("📦 Complete Book (ZIP)")
        dl_opts.extend(["📄 Single Chapter", "📥 All Chapters"])
        
        idx = grid_menu("Download Type", dl_opts, cols=1)
        if idx is None: continue
        
        # Adjust index if ZIP not available
        if has_zip:
            if idx == 0:
                download_zip(int(class_num), subject, book_code)
            elif idx == 1:
                download_chapter(int(class_num), subject, book_code, chapters)
            else:
                download_all_chapters(int(class_num), subject, book_code, chapters)
        else:
            if idx == 0:
                download_chapter(int(class_num), subject, book_code, chapters)
            else:
                download_all_chapters(int(class_num), subject, book_code, chapters)
        
        # Continue?
        print(f"\n{C.Y}{'─'*tw()}{C.E}")
        if input(f" Download more? (y/n): ").lower() != 'y':
            break
    
    print(f"\n {C.G}👋 Goodbye!{C.E}\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n {C.Y}Interrupted{C.E}\n")
