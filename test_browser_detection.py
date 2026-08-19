"""Test browser detection on Windows"""
import os
from pathlib import Path

def find_browser_executable(browser_name: str):
    """Find browser executable on Windows"""
    browser_paths = {
        "chrome": [
            Path(os.environ.get("PROGRAMFILES", "C:\\Program Files")) / "Google" / "Chrome" / "Application" / "chrome.exe",
            Path(os.environ.get("PROGRAMFILES(X86)", "C:\\Program Files (x86)")) / "Google" / "Chrome" / "Application" / "chrome.exe",
            Path(os.environ.get("LOCALAPPDATA", "")) / "Google" / "Chrome" / "Application" / "chrome.exe",
        ],
        "edge": [
            Path(os.environ.get("PROGRAMFILES", "C:\\Program Files")) / "Microsoft" / "Edge" / "Application" / "msedge.exe",
            Path(os.environ.get("PROGRAMFILES(X86)", "C:\\Program Files (x86)")) / "Microsoft" / "Edge" / "Application" / "msedge.exe",
        ],
        "firefox": [
            Path(os.environ.get("PROGRAMFILES", "C:\\Program Files")) / "Mozilla Firefox" / "firefox.exe",
            Path(os.environ.get("PROGRAMFILES(X86)", "C:\\Program Files (x86)")) / "Mozilla Firefox" / "firefox.exe",
        ],
    }
    
    for path in browser_paths.get(browser_name.lower(), []):
        print(f"Checking: {path}")
        if path.exists():
            print(f"✓ FOUND: {path}")
            return str(path)
    
    print(f"✗ NOT FOUND: {browser_name}")
    return None

if __name__ == "__main__":
    print("=" * 60)
    print("BROWSER DETECTION TEST")
    print("=" * 60)
    
    browsers = ["chrome", "edge", "firefox"]
    found_browsers = []
    
    for browser in browsers:
        print(f"\n--- Testing {browser.upper()} ---")
        result = find_browser_executable(browser)
        if result:
            found_browsers.append(browser)
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Found browsers: {', '.join(found_browsers) if found_browsers else 'NONE'}")
    
    if found_browsers:
        print(f"\n✅ SUCCESS: Will use {found_browsers[0]} for cookie extraction")
    else:
        print("\n❌ FAILED: No browsers found - YouTube downloads will fail")
