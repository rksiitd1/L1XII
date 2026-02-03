#!/usr/bin/env python3
"""
NCERT Catalog Scanner
=====================
Scans ncert.nic.in and caches all available books to catalog.json.
Run this periodically (e.g., every 6 months) to update the catalog.

Usage: python scanner.py
"""
import os, sys, json, time, shutil
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import requests
except ImportError:
    os.system(f"{sys.executable} -m pip install requests -q")
    import requests

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════
BASE_URL = "https://ncert.nic.in/textbook/pdf/"
CATALOG_FILE = Path(__file__).parent / "catalog.json"

CLASS_CODES = {1:'a',2:'b',3:'c',4:'d',5:'e',6:'f',7:'g',8:'h',9:'i',10:'j',11:'k',12:'l'}
LANG_CODES = {'e':'English', 'h':'Hindi', 'u':'Urdu'}

# All known subject codes
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
    'fl':'Flamingo','vi':'Vistas','ho':'Hornbill','sn':'Snapshots',
    'kk':'Rimjhim','rl':'Ruchira','dd':'Durva','bh':'Bharati','vs':'Vasant',
    'dr':'Door','hv':'Honeydew','hc':'Honeycomb','ab':'Alien Hand',
    'mr':'Marigold','rw':'Raindrops','ww':'Winds of Change'
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

def url_exists(url):
    try:
        r = requests.head(url, timeout=5, allow_redirects=True)
        return r.status_code == 200
    except: 
        return False

def check_book_exists(class_num, lang, subj_code, part):
    """Check if a book exists (ZIP or chapter 01)."""
    cc = CLASS_CODES[class_num]
    code = f"{cc}{lang}{subj_code}{part}"
    
    zip_url = f"{BASE_URL}{code}dd.zip"
    ch1_url = f"{BASE_URL}{code}01.pdf"
    
    return url_exists(zip_url) or url_exists(ch1_url), code

def scan_chapters(book_code):
    """Scan available chapters for a book."""
    chapters = []
    misses = 0
    
    for ch in range(0, 40):
        ch_str = f"{ch:02d}"
        if url_exists(f"{BASE_URL}{book_code}{ch_str}.pdf"):
            chapters.append(ch_str)
            misses = 0
        else:
            misses += 1
            if misses > 3 and chapters: 
                break
    
    # Check special sections
    for sp in ['ps','an','ap','gl','lp','dd']:
        if url_exists(f"{BASE_URL}{book_code}{sp}.pdf"):
            chapters.append(sp)
    
    return chapters

def banner():
    w = tw()
    print(f"\n{C.C}{C.BD}{'═'*w}{C.E}")
    print(f"{C.C}{C.BD}  📡 NCERT Catalog Scanner{C.E}")
    print(f"{C.C}{C.BD}{'═'*w}{C.E}\n")

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN SCANNER
# ═══════════════════════════════════════════════════════════════════════════════

def scan_all():
    """Scan entire NCERT catalog."""
    banner()
    
    catalog = {
        "last_updated": datetime.now().isoformat(),
        "classes": {}
    }
    
    total_books = 0
    start_time = time.time()
    
    print(f" {C.D}This will take several minutes. Please wait...{C.E}\n")
    
    # Scan each class
    for class_num in range(1, 13):
        print(f"\n{C.Y}{'─'*tw()}{C.E}")
        print(f" {C.BD}{C.G}Class {class_num}{C.E}")
        
        class_data = {}
        
        # Scan each subject
        for subj_code, subj_name in SUBJECT_CODES.items():
            subject_found = False
            subj_data = {"code": subj_code, "languages": {}}
            
            # Check each language
            for lang_code in ['e', 'h', 'u']:
                lang_data = {"parts": {}}
                
                # Check each part (1-4)
                for part in range(1, 5):
                    exists, book_code = check_book_exists(class_num, lang_code, subj_code, part)
                    
                    if exists:
                        subject_found = True
                        print(f"   {C.G}✓{C.E} {subj_name} ({LANG_CODES[lang_code]}) Part {part}", end='', flush=True)
                        
                        # Scan chapters
                        chapters = scan_chapters(book_code)
                        lang_data["parts"][str(part)] = {
                            "code": book_code,
                            "chapters": chapters,
                            "has_zip": url_exists(f"{BASE_URL}{book_code}dd.zip")
                        }
                        
                        print(f" [{len(chapters)} ch]")
                        total_books += 1
                
                if lang_data["parts"]:
                    subj_data["languages"][lang_code] = lang_data
            
            if subject_found:
                class_data[subj_name] = subj_data
        
        if class_data:
            catalog["classes"][str(class_num)] = class_data
    
    # Save catalog
    elapsed = time.time() - start_time
    
    print(f"\n{C.Y}{'═'*tw()}{C.E}")
    print(f" {C.G}✅ Scan complete!{C.E}")
    print(f"    📚 Total books found: {C.BD}{total_books}{C.E}")
    print(f"    ⏱️  Time taken: {C.BD}{elapsed/60:.1f} minutes{C.E}")
    
    # Save to file
    with open(CATALOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)
    
    print(f"    💾 Saved to: {C.C}{CATALOG_FILE.name}{C.E}")
    print(f"{C.Y}{'═'*tw()}{C.E}\n")
    
    return catalog

# ═══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    try:
        scan_all()
    except KeyboardInterrupt:
        print(f"\n {C.Y}⚡ Scan interrupted{C.E}\n")
        sys.exit(1)
