#!/usr/bin/env python3
"""
NCERT Textbook Downloader
=========================
Interactive CLI tool to download NCERT textbooks (PDFs/ZIPs)
from ncert.nic.in with organized folder structure.

Author: Gurukulam Project
"""

import os
import sys
import time
import zipfile
import shutil
from pathlib import Path
from typing import Optional, List, Tuple

try:
    import requests
except ImportError:
    print("❌ 'requests' module not found. Installing...")
    os.system(f"{sys.executable} -m pip install requests")
    import requests

try:
    from tqdm import tqdm
except ImportError:
    print("❌ 'tqdm' module not found. Installing...")
    os.system(f"{sys.executable} -m pip install tqdm")
    from tqdm import tqdm


# ══════════════════════════════════════════════════════════════════════════════
# CONSTANTS & MAPPINGS
# ══════════════════════════════════════════════════════════════════════════════

BASE_URL = "https://ncert.nic.in/textbook/pdf/"

# Class codes (1-12 → a-l)
CLASSES = {
    1: 'a', 2: 'b', 3: 'c', 4: 'd', 5: 'e', 6: 'f',
    7: 'g', 8: 'h', 9: 'i', 10: 'j', 11: 'k', 12: 'l'
}

# Language codes
LANGUAGES = {
    'English': 'e',
    'Hindi': 'h',
    'Urdu': 'u'
}

# Subject codes - comprehensive mapping by class groups
SUBJECTS = {
    # Primary (Class 1-5)
    'primary': {
        'Mathematics': 'mh',
        'English': 'en',
        'Hindi': 'hi',
        'EVS': 'ev',
    },
    # Middle (Class 6-8)
    'middle': {
        'Mathematics': 'mh',
        'Science': 'sc',
        'Social Science': 'ss',
        'English': 'en',
        'Hindi': 'hi',
        'Sanskrit': 'sk',
    },
    # Secondary (Class 9-10)
    'secondary': {
        'Mathematics': 'mh',
        'Science': 'sc',
        'Social Science': 'ss',
        'English': 'en',
        'Hindi': 'hi',
        'Sanskrit': 'sk',
        'Economics': 'ec',
        'History': 'hy',
        'Geography': 'gy',
        'Political Science': 'ps',
    },
    # Senior Secondary (Class 11-12)
    'senior': {
        'Mathematics': 'mh',
        'Physics': 'ph',
        'Chemistry': 'ch',
        'Biology': 'bo',
        'English': 'en',
        'Hindi': 'hi',
        'Sanskrit': 'sk',
        'Economics': 'ec',
        'Accountancy': 'ac',
        'Business Studies': 'bs',
        'History': 'hy',
        'Geography': 'gy',
        'Political Science': 'ps',
        'Psychology': 'py',
        'Sociology': 'so',
        'Computer Science': 'cs',
        'Informatics': 'ip',
        'Statistics': 'st',
        'Fine Arts': 'fa',
        'Home Science': 'hs',
    }
}

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    MAGENTA = '\033[35m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    END = '\033[0m'


# ══════════════════════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def get_terminal_width() -> int:
    """Get terminal width, default to 80."""
    try:
        return shutil.get_terminal_size().columns
    except:
        return 80


def clear_screen():
    """Clear terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')


def print_banner():
    """Display the application banner."""
    width = get_terminal_width()
    banner = f"""
{Colors.CYAN}{Colors.BOLD}
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║   ███╗   ██╗ ██████╗███████╗██████╗ ████████╗                    ║
║   ████╗  ██║██╔════╝██╔════╝██╔══██╗╚══██╔══╝                    ║
║   ██╔██╗ ██║██║     █████╗  ██████╔╝   ██║                       ║
║   ██║╚██╗██║██║     ██╔══╝  ██╔══██╗   ██║                       ║
║   ██║ ╚████║╚██████╗███████╗██║  ██║   ██║                       ║
║   ╚═╝  ╚═══╝ ╚═════╝╚══════╝╚═╝  ╚═╝   ╚═╝                       ║
║                                                                  ║
║              📚 NCERT Textbook Downloader 📚                     ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
{Colors.END}
"""
    print(banner)


def print_header(text: str):
    """Print a styled header."""
    width = min(get_terminal_width(), 70)
    print(f"\n{Colors.YELLOW}{'─' * width}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.GREEN}  {text}{Colors.END}")
    print(f"{Colors.YELLOW}{'─' * width}{Colors.END}\n")


def print_menu_grid(title: str, options: list, show_back: bool = True, cols: int = 0) -> int:
    """Display options in a grid layout for better visibility."""
    print_header(title)
    
    # Calculate optimal columns based on terminal width and option lengths
    term_width = get_terminal_width() - 4
    max_opt_len = max(len(opt) for opt in options) + 6  # [N] option
    
    if cols == 0:
        cols = max(1, min(4, term_width // max_opt_len))
    
    col_width = term_width // cols
    
    # Print options in grid
    for i, option in enumerate(options, 1):
        label = f"{Colors.CYAN}[{i:2d}]{Colors.END} {option}"
        padding = col_width - len(f"[{i:2d}] {option}")
        
        print(f"  {label}{' ' * max(0, padding)}", end='')
        
        if i % cols == 0:
            print()  # New line after each row
    
    # Add newline if last row wasn't complete
    if len(options) % cols != 0:
        print()
    
    if show_back:
        print(f"\n  {Colors.RED}[0]{Colors.END} ← Back / Exit")
    
    print()
    
    while True:
        try:
            choice = input(f"  {Colors.BOLD}Enter choice: {Colors.END}").strip()
            if choice == '':
                continue
            choice = int(choice)
            if show_back and choice == 0:
                return 0
            if 1 <= choice <= len(options):
                return choice
            print(f"  {Colors.RED}Invalid choice. Try again.{Colors.END}")
        except ValueError:
            print(f"  {Colors.RED}Please enter a number.{Colors.END}")


def get_subject_group(class_num: int) -> str:
    """Get subject group based on class number."""
    if class_num <= 5:
        return 'primary'
    elif class_num <= 8:
        return 'middle'
    elif class_num <= 10:
        return 'secondary'
    else:
        return 'senior'


def build_book_code(class_num: int, language: str, subject_code: str, part: int) -> str:
    """Build the book code from selections."""
    class_code = CLASSES[class_num]
    lang_code = LANGUAGES[language]
    return f"{class_code}{lang_code}{subject_code}{part}"


def build_download_url(book_code: str, chapter: Optional[str] = None) -> str:
    """Build the download URL."""
    if chapter:
        return f"{BASE_URL}{book_code}{chapter}.pdf"
    else:
        return f"{BASE_URL}{book_code}dd.zip"


def create_download_folder(class_num: int, subject: str, chapter: bool = False) -> Path:
    """Create and return the download folder path."""
    base_dir = Path(__file__).parent / "NCERT" / f"Class_{class_num}" / subject.replace(" ", "_")
    
    if chapter:
        base_dir = base_dir / "chapters"
    
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir


def check_url_exists(url: str) -> Tuple[bool, int]:
    """Check if a URL exists and return status."""
    try:
        response = requests.head(url, timeout=10, allow_redirects=True)
        return response.status_code == 200, response.status_code
    except requests.RequestException:
        return False, 0


def download_file(url: str, save_path: Path, max_retries: int = 3) -> bool:
    """Download a file with progress bar and retry logic."""
    for attempt in range(max_retries):
        try:
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            size_mb = total_size / (1024*1024)
            
            print(f"\n  {Colors.CYAN}📥 {save_path.name}{Colors.END} ({size_mb:.2f} MB)")
            
            with open(save_path, 'wb') as f:
                with tqdm(total=total_size, unit='B', unit_scale=True, 
                         desc="     ", bar_format='{l_bar}{bar:30}| {n_fmt}/{total_fmt} [{rate_fmt}]',
                         ncols=70) as pbar:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            pbar.update(len(chunk))
            
            print(f"  {Colors.GREEN}✅ Done!{Colors.END}")
            return True
            
        except requests.RequestException as e:
            print(f"  {Colors.RED}❌ Attempt {attempt + 1} failed: {e}{Colors.END}")
            if attempt < max_retries - 1:
                print(f"  {Colors.YELLOW}   Retrying...{Colors.END}")
                time.sleep(2)
    
    print(f"  {Colors.RED}❌ Failed after {max_retries} attempts.{Colors.END}")
    return False


def extract_zip(zip_path: Path, extract_to: Path) -> bool:
    """Extract a ZIP file."""
    try:
        print(f"\n  {Colors.CYAN}📦 Extracting...{Colors.END}")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        print(f"  {Colors.GREEN}✅ Extracted to: {extract_to.name}/{Colors.END}")
        return True
    except zipfile.BadZipFile:
        print(f"  {Colors.RED}❌ Invalid ZIP file.{Colors.END}")
        return False


def find_available_parts(class_num: int, language: str, subject_code: str) -> List[int]:
    """Find available parts by checking URLs."""
    print(f"\n  {Colors.DIM}Checking available parts...{Colors.END}", end=' ', flush=True)
    
    available = []
    for part in range(1, 5):  # Check up to 4 parts
        book_code = build_book_code(class_num, language, subject_code, part)
        # Check if either ZIP or chapter 01 exists
        zip_url = build_download_url(book_code)
        ch1_url = build_download_url(book_code, "01")
        
        zip_exists, _ = check_url_exists(zip_url)
        ch1_exists, _ = check_url_exists(ch1_url)
        
        if zip_exists or ch1_exists:
            available.append(part)
            print(f"{Colors.GREEN}Part {part} ✓{Colors.END}", end=' ', flush=True)
        else:
            # Stop if we hit a gap after finding some parts
            if available:
                break
    
    print()  # New line
    return available if available else [1]  # Default to Part 1


def find_available_chapters(book_code: str) -> List[str]:
    """Find available chapters for a book by checking URLs."""
    print(f"\n  {Colors.DIM}Scanning chapters...{Colors.END} ", end='', flush=True)
    available = []
    consecutive_misses = 0
    
    # First, try common chapter patterns
    for ch in range(0, 50):  # Start from 0 for prelims, go up to 50
        chapter_str = f"{ch:02d}"
        url = build_download_url(book_code, chapter_str)
        
        try:
            response = requests.head(url, timeout=5, allow_redirects=True)
            if response.status_code == 200:
                available.append(chapter_str)
                print(f"{Colors.GREEN}{ch}{Colors.END} ", end='', flush=True)
                consecutive_misses = 0
            else:
                consecutive_misses += 1
        except:
            consecutive_misses += 1
        
        # Stop after 5 consecutive misses if we've found some chapters
        if consecutive_misses >= 5 and len(available) > 0:
            break
        
        # Stop early if no chapters found in first 10
        if ch >= 10 and len(available) == 0:
            break
    
    # Also check for special codes like ps (preliminary section), an (answers)
    for special in ['ps', 'an', 'ap', 'gl']:  # preliminaries, answers, appendix, glossary
        url = f"{BASE_URL}{book_code}{special}.pdf"
        try:
            response = requests.head(url, timeout=3, allow_redirects=True)
            if response.status_code == 200:
                available.append(special)
                print(f"{Colors.MAGENTA}{special}{Colors.END} ", end='', flush=True)
        except:
            pass
    
    print(f"\n  {Colors.GREEN}Found {len(available)} items{Colors.END}")
    return available


# ══════════════════════════════════════════════════════════════════════════════
# MAIN MENU FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def select_class() -> Optional[int]:
    """Select class number."""
    options = [f"Class {i}" for i in range(1, 13)]
    choice = print_menu_grid("📚 Select Class", options, cols=4)
    return choice if choice > 0 else None


def select_language() -> Optional[str]:
    """Select language."""
    options = list(LANGUAGES.keys())
    choice = print_menu_grid("🌐 Select Language", options, cols=3)
    return options[choice - 1] if choice > 0 else None


def select_subject(class_num: int) -> Optional[Tuple[str, str]]:
    """Select subject for the given class."""
    group = get_subject_group(class_num)
    subjects = SUBJECTS[group]
    options = list(subjects.keys())
    
    choice = print_menu_grid(f"📖 Subjects for Class {class_num}", options, cols=3)
    if choice > 0:
        subject_name = options[choice - 1]
        return subject_name, subjects[subject_name]
    return None


def select_part(available_parts: List[int]) -> Optional[int]:
    """Select book part from available options."""
    if len(available_parts) == 1:
        print(f"\n  {Colors.DIM}Only Part {available_parts[0]} available.{Colors.END}")
        return available_parts[0]
    
    options = [f"Part {p}" for p in available_parts]
    choice = print_menu_grid("📑 Select Part", options, cols=4)
    return available_parts[choice - 1] if choice > 0 else None


def select_download_type() -> Optional[int]:
    """Select download type."""
    options = [
        "📦 Complete Book (ZIP)",
        "📄 Single Chapter (PDF)",
        "📥 All Chapters (PDFs)"
    ]
    choice = print_menu_grid("⬇️  Download Type", options, cols=1)
    return choice if choice > 0 else None


def download_complete_book(class_num: int, language: str, subject: str, 
                           subject_code: str, part: int) -> bool:
    """Download the complete book as ZIP."""
    book_code = build_book_code(class_num, language, subject_code, part)
    url = build_download_url(book_code)
    
    print(f"\n  {Colors.DIM}Code: {book_code} | URL: {url}{Colors.END}")
    
    # Check if URL exists
    exists, status = check_url_exists(url)
    if not exists:
        print(f"\n  {Colors.RED}❌ Book ZIP not found (Status: {status}){Colors.END}")
        print(f"  {Colors.YELLOW}   Try downloading individual chapters instead.{Colors.END}")
        return False
    
    # Create folder and download
    folder = create_download_folder(class_num, subject)
    filename = f"{book_code}dd.zip"
    save_path = folder / filename
    
    if save_path.exists():
        print(f"\n  {Colors.YELLOW}⚠️  File exists: {save_path.name}{Colors.END}")
        overwrite = input(f"  Overwrite? (y/n): ").strip().lower()
        if overwrite != 'y':
            return False
    
    success = download_file(url, save_path)
    
    if success:
        extract = input(f"\n  Extract ZIP? (y/n): ").strip().lower()
        if extract == 'y':
            extract_to = folder / book_code
            extract_zip(save_path, extract_to)
    
    return success


def download_single_chapter(class_num: int, language: str, subject: str,
                            subject_code: str, part: int) -> bool:
    """Download a single chapter."""
    book_code = build_book_code(class_num, language, subject_code, part)
    
    # Find available chapters
    chapters = find_available_chapters(book_code)
    
    if not chapters:
        print(f"\n  {Colors.RED}❌ No chapters found.{Colors.END}")
        return False
    
    # Create display labels
    def chapter_label(ch):
        if ch.isdigit() or (len(ch) == 2 and ch[0] == '0'):
            return f"Chapter {int(ch)}"
        return ch.upper()
    
    options = [chapter_label(ch) for ch in chapters]
    choice = print_menu_grid(f"📄 Select Chapter ({len(chapters)} available)", options, cols=4)
    
    if choice == 0:
        return False
    
    # Get the actual chapter code (fix: use choice-1 as index)
    chapter = chapters[choice - 1]
    url = build_download_url(book_code, chapter)
    
    print(f"\n  {Colors.DIM}Downloading: {book_code}{chapter}.pdf{Colors.END}")
    
    folder = create_download_folder(class_num, subject, chapter=True)
    filename = f"{book_code}{chapter}.pdf"
    save_path = folder / filename
    
    return download_file(url, save_path)


def download_all_chapters(class_num: int, language: str, subject: str,
                          subject_code: str, part: int) -> bool:
    """Download all available chapters."""
    book_code = build_book_code(class_num, language, subject_code, part)
    
    # Find available chapters
    chapters = find_available_chapters(book_code)
    
    if not chapters:
        print(f"\n  {Colors.RED}❌ No chapters found.{Colors.END}")
        return False
    
    print(f"\n  {Colors.GREEN}Downloading {len(chapters)} files...{Colors.END}")
    
    folder = create_download_folder(class_num, subject, chapter=True)
    success_count = 0
    
    for chapter in chapters:
        url = build_download_url(book_code, chapter)
        filename = f"{book_code}{chapter}.pdf"
        save_path = folder / filename
        
        if save_path.exists():
            print(f"\n  {Colors.YELLOW}⏭️  Skip (exists): {filename}{Colors.END}")
            success_count += 1
            continue
        
        if download_file(url, save_path):
            success_count += 1
        
        time.sleep(0.3)  # Small delay between downloads
    
    print(f"\n  {Colors.GREEN}✅ Downloaded {success_count}/{len(chapters)} files.{Colors.END}")
    return success_count > 0


def show_summary(class_num: int, language: str, subject: str, part: int):
    """Show selection summary."""
    width = min(get_terminal_width(), 70)
    print(f"\n{Colors.BOLD}{'═' * width}{Colors.END}")
    print(f"  {Colors.GREEN}📚 Class {class_num} │ {language} │ {subject} │ Part {part}{Colors.END}")
    print(f"{'═' * width}")


def main_flow():
    """Main application flow."""
    while True:
        clear_screen()
        print_banner()
        
        # Step 1: Select Class
        class_num = select_class()
        if not class_num:
            print(f"\n  {Colors.GREEN}👋 Goodbye!{Colors.END}\n")
            break
        
        # Step 2: Select Language
        language = select_language()
        if not language:
            continue
        
        # Step 3: Select Subject
        result = select_subject(class_num)
        if not result:
            continue
        subject, subject_code = result
        
        # Step 4: Find and select available parts
        available_parts = find_available_parts(class_num, language, subject_code)
        part = select_part(available_parts)
        if not part:
            continue
        
        # Step 5: Select Download Type
        download_type = select_download_type()
        if not download_type:
            continue
        
        # Show summary
        show_summary(class_num, language, subject, part)
        
        # Execute download
        if download_type == 1:
            download_complete_book(class_num, language, subject, subject_code, part)
        elif download_type == 2:
            download_single_chapter(class_num, language, subject, subject_code, part)
        elif download_type == 3:
            download_all_chapters(class_num, language, subject, subject_code, part)
        
        # Ask to continue
        print(f"\n{Colors.YELLOW}{'─' * 50}{Colors.END}")
        again = input(f"  Download more? (y/n): ").strip().lower()
        if again != 'y':
            print(f"\n  {Colors.GREEN}👋 Goodbye!{Colors.END}\n")
            break


# ══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    try:
        main_flow()
    except KeyboardInterrupt:
        print(f"\n\n  {Colors.YELLOW}⚡ Interrupted.{Colors.END}")
        print(f"  {Colors.GREEN}👋 Goodbye!{Colors.END}\n")
        sys.exit(0)
