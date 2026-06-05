# -*- coding: utf-8 -*-
"""
Download FunASR Paraformer model using modelscope
With extended timeout and retry logic
"""
import os
import sys
import time

APP_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(APP_DIR, ".funasr_cache")

os.environ["MODELSCOPE_CACHE"] = CACHE_DIR

def download_with_retry():
    try:
        from modelscope import snapshot_download
        
        print("=" * 60)
        print("  Downloading FunASR Paraformer Model")
        print("  Model: iic/speech_paraformer-large-vad-punc_asr_nat-zh-cn-16k-common-vocab8404-pytorch")
        print("  Size: ~944MB")
        print("  Cache: {}".format(CACHE_DIR))
        print("=" * 60)
        print()
        
        # This will download the model from ModelScope
        # It supports resumable download
        model_dir = snapshot_download(
            "iic/speech_paraformer-large-vad-punc_asr_nat-zh-cn-16k-common-vocab8404-pytorch",
            cache_dir=CACHE_DIR,
            revision="master",
        )
        
        print()
        print("=" * 60)
        print("  DOWNLOAD COMPLETE!")
        print("  Model saved to: {}".format(model_dir))
        print("=" * 60)
        return True
        
    except Exception as e:
        print("[ERROR] Download failed: {}".format(e))
        print()
        print("Trying alternative model (medium size, ~200MB)...")
        try:
            from modelscope import snapshot_download
            model_dir = snapshot_download(
                "iic/speech_paraformer-medium-asr_nat-zh-cn-16k-common-vocab8404",
                cache_dir=CACHE_DIR,
            )
            print("Medium model downloaded to: {}".format(model_dir))
            return True
        except Exception as e2:
            print("[ERROR] Alternative also failed: {}".format(e2))
            return False

if __name__ == "__main__":
    download_with_retry()
