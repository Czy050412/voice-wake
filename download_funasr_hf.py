# -*- coding: utf-8 -*-
"""
Download FunASR model from HuggingFace (hf-mirror)
With resume support and progress bar
"""
import os
import sys
import time
import hashlib

APP_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(APP_DIR, ".funasr_cache_hf")
os.makedirs(CACHE_DIR, exist_ok=True)

# Model files needed from HuggingFace FunASR
MODEL_REPO = "funasr/speech_paraformer-large-vad-punc_asr_nat-zh-cn-16k-common-vocab8404-pytorch"
HF_MIRROR = "https://hf-mirror.com"

# Required files (we'll discover them)
REQUIRED_FILES = [
    "model.pb",
    "am.mvn",
    "config.yaml",
    "tokens.txt",
]

def download_file(url, local_path, chunk_size=8192):
    """Download with resume support"""
    import requests
    
    headers = {}
    existing_size = 0
    if os.path.exists(local_path):
        existing_size = os.path.getsize(local_path)
        headers["Range"] = "bytes={}-".format(existing_size)
    
    try:
        resp = requests.get(url, headers=headers, stream=True, timeout=60)
        if resp.status_code == 416:  # Range not satisfiable = already complete
            return True
        if resp.status_code not in (200, 206):
            print("  HTTP {}".format(resp.status_code))
            return False
        
        mode = "ab" if resp.status_code == 206 else "wb"
        total = int(resp.headers.get("content-length", 0)) + existing_size
        downloaded = existing_size
        
        with open(local_path, mode) as f:
            for chunk in resp.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total > 0:
                        pct = downloaded * 100 // total
                        print("\r  Progress: {}% ({}/{} bytes)".format(
                            pct, downloaded, total), end="", flush=True)
        
        print()  # newline
        return True
        
    except Exception as e:
        print("  Error: {}".format(e))
        return False

def download_model():
    """Download the model files"""
    import requests
    
    print("=" * 60)
    print("  FunASR Model Download (HF Mirror)")
    print("  Cache: {}".format(CACHE_DIR))
    print("=" * 60)
    
    # First, try to get the list of files in the repo
    api_url = "{}/api/models/{}".format(HF_MIRROR, MODEL_REPO)
    try:
        resp = requests.get(api_url, timeout=30)
        if resp.status_code != 200:
            print("[WARN] Cannot list files via API, trying manual download...")
            files_to_try = REQUIRED_FILES
        else:
            data = resp.json()
            files_to_try = [s["path"] for s in data.get("siblings", [])]
            print("Found {} files in repo".format(len(files_to_try)))
    except Exception as e:
        print("[WARN] API error: {}, trying manual...".format(e))
        files_to_try = REQUIRED_FILES
    
    success_count = 0
    for fname in files_to_try:
        if fname.endswith("/"):
            continue
        
        url = "{}/{}/resolve/main/{}".format(HF_MIRROR, MODEL_REPO, fname)
        local = os.path.join(CACHE_DIR, fname)
        os.makedirs(os.path.dirname(local), exist_ok=True)
        
        if os.path.exists(local) and os.path.getsize(local) > 0:
            print("[SKIP] {} (already exists, {} bytes)".format(
                fname, os.path.getsize(local)))
            success_count += 1
            continue
        
        print("[DOWNLOAD] {}".format(fname))
        if download_file(url, local):
            success_count += 1
        else:
            print("[FAIL] {}".format(fname))
        time.sleep(0.5)
    
    print()
    print("=" * 60)
    print("  Downloaded: {}/{} files".format(success_count, len(files_to_try)))
    total_size = sum(os.path.getsize(os.path.join(CACHE_DIR, f)) 
                     for f in os.listdir(CACHE_DIR) 
                     if os.path.isfile(os.path.join(CACHE_DIR, f)))
    print("  Total size: {} MB".format(total_size // (1024*1024)))
    print("=" * 60)
    
    return success_count > 0

if __name__ == "__main__":
    download_model()
