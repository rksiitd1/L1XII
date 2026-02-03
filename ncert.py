#!/usr/bin/env python3
"""
NCERT Textbook Downloader - Scans ncert.nic.in for available books
"""
import os, sys, time, zipfile, shutil, re
from pathlib import Path
from typing import Optional, List, Tuple, Dict

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
TEXTBOOK_PAGE = "https://ncert.nic.in/textbook.php"

CLASS_CODES = {1:'a',2:'b',3:'c',4:'d',5:'e',6:'f',7:'g',8:'h',9:'i',10:'j',11:'k',12:'l'}
LANG_CODES = {'e':'English', 'h':'Hindi', 'u':'Urdu'}

# Known subject codes (will be validated by scanning)
SUBJECT_CODES = {
    'mh':'Mathematics','ph':'Physics','ch':'Chemistry','bo':'Biology',
    'sc':'Science','ss':'Social Science','en':'English','hi':'Hindi',
    'sk':'Sanskrit','ec':'Economics','ac':'Accountancy','bs':'Business Studies',
    'hy':'History','gy':'Geography','ps':'Political Science','py':'Psychology',
    'so':'Sociology','cs':'Computer Science','ip':'Informatics Practices',
    'st':'Statistics','fa':'Fine Arts','hs':'Home Science','ev':'EVS',
    'ci':'Civics','he':'Health Education','le':'Legal Studies',
    'ms':'Mass Media','mu':'Music','th':'Theatre','an':'Anthropology',
    'hu':'Human Ecology','bt':'Biotechnology','ee':'Entrepreneurship',
    'kk':'Rimjhim','rl':'Ruchira','dd':'Durva' # Hindi language books
}

# Colors
C = type('C', (), {
    'R':'\033[91m','G':'\033[92m','Y':'\033[93m','B':'\033[94m',
    'M':'\033[95m','C':'\033[96m','W':'\033[97m','D':'\033[90m',
    'BD':'\033[1m','E':'\033[0m'
})()

# ═══════════════════════════════════════════════════════════════════════════════
# UTILITIES
# ═══════════════════════════════════════════════════════════════════════════════
def tw(): 
    try: return shutil.get_terminal_size().columns
    except: return 80

def cls(): os.system('cls' if os.name=='nt' else 'clear')

def url_exists(url):
    try:
        r = requests.head(url, timeout=5, allow_redirects=True)
        return r.status_code == 200
    except: return False

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
    
    # Calculate column width
    max_len = max(len(str(o)) for o in options) + 6  # [XX] option
    w = tw() - 2
    cols = max(1, min(cols, w // max_len))
    col_w = w // cols
    
    # Print grid
    for i, opt in enumerate(options):
        idx = f"[{i+1:2d}]" if len(options) > 9 else f"[{i+1}]"
        cell = f" {C.C}{idx}{C.E} {opt}"
        # Calculate visible length (without color codes)
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
# SCANNING FUNCTIONS - Discovers what's available on NCERT website
# ═══════════════════════════════════════════════════════════════════════════════

def scan_subjects(class_num: int) -> Dict[str, str]:
    """Scan available subjects for a class."""
    print(f"\n {C.D}Scanning subjects for Class {class_num}...{C.E}", end=' ', flush=True)
    
    cc = CLASS_CODES[class_num]
    found = {}
    
    # Try all known subject codes with all languages
    for sc, name in SUBJECT_CODES.items():
        for lang in ['e', 'h']:  # English and Hindi are most common
            for part in [1, 2]:
                code = f"{cc}{lang}{sc}{part}"
                # Check if ZIP or chapter 01 exists
                if url_exists(f"{BASE_URL}{code}dd.zip") or url_exists(f"{BASE_URL}{code}01.pdf"):
                    if sc not in found:
                        found[sc] = name
                        print(f"{C.G}✓{C.E}", end='', flush=True)
                    break
            if sc in found:
                break
    
    print(f" ({len(found)} found)")
    return found

def scan_languages(class_num: int, subject_code: str) -> List[str]:
    """Scan available languages for a subject."""
    print(f" {C.D}Scanning languages...{C.E}", end=' ', flush=True)
    
    cc = CLASS_CODES[class_num]
    found = []
    
    for lang_code, lang_name in LANG_CODES.items():
        for part in [1, 2]:
            code = f"{cc}{lang_code}{subject_code}{part}"
            if url_exists(f"{BASE_URL}{code}dd.zip") or url_exists(f"{BASE_URL}{code}01.pdf"):
                found.append(lang_code)
                print(f"{C.G}{lang_name}{C.E}", end=' ', flush=True)
                break
    
    print()
    return found

def scan_parts(class_num: int, lang_code: str, subject_code: str) -> List[int]:
    """Scan available parts for a book."""
    print(f" {C.D}Scanning parts...{C.E}", end=' ', flush=True)
    
    cc = CLASS_CODES[class_num]
    found = []
    
    for part in range(1, 5):
        code = f"{cc}{lang_code}{subject_code}{part}"
        if url_exists(f"{BASE_URL}{code}dd.zip") or url_exists(f"{BASE_URL}{code}01.pdf"):
            found.append(part)
            print(f"{C.G}Part {part}{C.E}", end=' ', flush=True)
    
    print()
    return found if found else [1]

def scan_chapters(book_code: str) -> List[str]:
    """Scan available chapters."""
    print(f" {C.D}Scanning chapters...{C.E}", end=' ', flush=True)
    
    found = []
    misses = 0
    
    for ch in range(0, 40):
        ch_str = f"{ch:02d}"
        if url_exists(f"{BASE_URL}{book_code}{ch_str}.pdf"):
            found.append(ch_str)
            print(f"{C.G}{ch}{C.E}", end=' ', flush=True)
            misses = 0
        else:
            misses += 1
            if misses > 3 and found: break
    
    # Check special sections
    for sp in ['ps','an','ap','gl','lp']:
        if url_exists(f"{BASE_URL}{book_code}{sp}.pdf"):
            found.append(sp)
            print(f"{C.M}{sp}{C.E}", end=' ', flush=True)
    
    print()
    return found

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

def download_zip(class_num, lang, subject, subject_code, part):
    code = f"{CLASS_CODES[class_num]}{lang}{subject_code}{part}"
    url = f"{BASE_URL}{code}dd.zip"
    
    if not url_exists(url):
        print(f" {C.R}✗ ZIP not available{C.E}")
        return False
    
    folder = make_folder(class_num, subject)
    path = folder / f"{code}dd.zip"
    
    if download(url, path):
        if input(f" Extract? (y/n): ").lower() == 'y':
            try:
                with zipfile.ZipFile(path, 'r') as z:
                    z.extractall(folder / code)
                print(f" {C.G}✓ Extracted to {code}/{C.E}")
            except: print(f" {C.R}✗ Extract failed{C.E}")
        return True
    return False

def download_chapter(class_num, lang, subject, subject_code, part, chapters):
    code = f"{CLASS_CODES[class_num]}{lang}{subject_code}{part}"
    
    # Let user select chapter
    labels = []
    for ch in chapters:
        if ch.isdigit() or (len(ch)==2 and ch[0]=='0'):
            labels.append(f"Ch {int(ch)}")
        else:
            labels.append(ch.upper())
    
    idx = grid_menu(f"Select Chapter ({len(chapters)} available)", labels)
    if idx is None: return False
    
    ch = chapters[idx]
    url = f"{BASE_URL}{code}{ch}.pdf"
    folder = make_folder(class_num, subject, True)
    return download(url, folder / f"{code}{ch}.pdf")

def download_all_chapters(class_num, lang, subject, subject_code, part, chapters):
    code = f"{CLASS_CODES[class_num]}{lang}{subject_code}{part}"
    folder = make_folder(class_num, subject, True)
    
    print(f"\n {C.G}Downloading {len(chapters)} files...{C.E}")
    ok = 0
    for ch in chapters:
        path = folder / f"{code}{ch}.pdf"
        if path.exists():
            print(f" {C.Y}⏭ {path.name} exists{C.E}")
            ok += 1
        elif download(f"{BASE_URL}{code}{ch}.pdf", path):
            ok += 1
        time.sleep(0.2)
    
    print(f"\n {C.G}✓ {ok}/{len(chapters)} downloaded{C.E}")
    return ok > 0

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN FLOW
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    while True:
        cls()
        banner()
        
        # 1. Select Class
        classes = [f"Class {i}" for i in range(1, 13)]
        idx = grid_menu("Select Class", classes)
        if idx is None: break
        class_num = idx + 1
        
        # 2. Scan & Select Subject
        subjects = scan_subjects(class_num)
        if not subjects:
            input(f" {C.R}No subjects found. Press Enter...{C.E}")
            continue
        
        subj_list = list(subjects.items())  # [(code, name), ...]
        subj_names = [s[1] for s in subj_list]
        idx = grid_menu(f"Subjects for Class {class_num}", subj_names, cols=3)
        if idx is None: continue
        subject_code, subject_name = subj_list[idx]
        
        # 3. Scan & Select Language
        languages = scan_languages(class_num, subject_code)
        if not languages:
            input(f" {C.R}No languages found. Press Enter...{C.E}")
            continue
        
        if len(languages) == 1:
            lang = languages[0]
            print(f" {C.D}Only {LANG_CODES[lang]} available{C.E}")
        else:
            lang_names = [LANG_CODES[l] for l in languages]
            idx = grid_menu("Select Language", lang_names)
            if idx is None: continue
            lang = languages[idx]
        
        # 4. Scan & Select Part
        parts = scan_parts(class_num, lang, subject_code)
        if len(parts) == 1:
            part = parts[0]
            print(f" {C.D}Only Part {part} available{C.E}")
        else:
            part_names = [f"Part {p}" for p in parts]
            idx = grid_menu("Select Part", part_names)
            if idx is None: continue
            part = parts[idx]
        
        # 5. Download Type
        book_code = f"{CLASS_CODES[class_num]}{lang}{subject_code}{part}"
        
        print(f"\n{C.Y}{'─'*tw()}{C.E}")
        print(f" {C.BD}{C.G}Class {class_num} │ {LANG_CODES[lang]} │ {subject_name} │ Part {part}{C.E}")
        print(f" {C.D}Code: {book_code}{C.E}")
        
        dl_opts = ["📦 Complete Book (ZIP)", "📄 Single Chapter", "📥 All Chapters"]
        idx = grid_menu("Download Type", dl_opts, cols=1)
        if idx is None: continue
        
        if idx == 0:
            download_zip(class_num, lang, subject_name, subject_code, part)
        else:
            chapters = scan_chapters(book_code)
            if not chapters:
                print(f" {C.R}No chapters found{C.E}")
            elif idx == 1:
                download_chapter(class_num, lang, subject_name, subject_code, part, chapters)
            else:
                download_all_chapters(class_num, lang, subject_name, subject_code, part, chapters)
        
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
