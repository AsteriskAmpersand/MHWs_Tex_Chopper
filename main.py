# -*- coding: utf-8 -*-
"""
Created on Mon Apr  5 11:46:20 2021

@author: AsteriskAmpersand
"""
import sys
from pathlib import Path
from tex import convertFromTex, convertToTex

def main():
    compress = True
    nibbleSet = 0
    for path in sys.argv[1:]:
        if path == "-C":
            print("Compression %s"%("Disabled" if compress else "Enabled"))
            compress = not compress
        elif len(path)>2 and path[:2] == "-N":
            nibbleSet = int(path[2:])
        elif ".tex" in path:
            convertFromTex(path)
        elif ".dds" in path:
            convertToTex(path,compress = compress,nibbles = nibbleSet)
        else:
            if Path(path).is_dir():
                for spath in Path(path).rglob("*.tex*"):
                    convertFromTex(spath)
                for spath in Path(path).rglob("*.dds"):
                    convertToTex(spath,compress = compress,nibbles = nibbleSet)

if __name__ in "__main__":
    main()