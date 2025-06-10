from __future__ import annotations
import os
import json
from collections import defaultdict
from itertools import zip_longest
import pandas as pd
import time
from datetime import datetime
import sys
import ctypes
from pathlib import Path
from collections.abc import Iterable


def openFiles():
    import webbrowser
    import os

    path = "G:/CML Operations/WELL FILES"
    df = pd.read_excel("book5.xlsx")
    wells = df['Well'].tolist()
    do = []
    files = sorted([f for f in os.listdir(path)])
    for f in files:
        if f not in wells:continue
        rprtsDir = f'{path}/{f}/REPORTS-DAILY OPS/Individual Reports/'
        if os.path.exists(rprtsDir):
            do.append(f)

    do = sorted(do)
    for f in do:
        print(f)
        rprtsDir = f'{path}/{f}/REPORTS-DAILY OPS/Individual Reports/'
        files = [f for f in os.listdir(rprtsDir) if os.path.isfile(os.path.join(rprtsDir, f))]
        files.sort(key=lambda x: os.path.getmtime(os.path.join(rprtsDir, x)), reverse=True)
        if len(files) > 0:
            webbrowser.open_new_tab(rprtsDir+'/'+files[0])
            time.sleep(1)

def walkPath(keys,path="C:/"):
    #path = "C:/Users/plaisancem/CML Exploration/Brandon Rogers - Well Files/"
    res = defaultdict(list)
    for root,folders,files in os.walk(path):
        for fld,f in zip_longest(folders,files):
            for key in keys:
                k = key.lower()
                if fld:
                    if k in fld.lower():
                        print(root,fld)
                        res[root].append(fld)
                if f:
                    if k in f.lower():
                        file_path = os.path.join(root, f)
                        modified_time = os.path.getmtime(file_path)
                        modified_date = datetime.fromtimestamp(modified_time)
                        print(root,f)
                        res['root'].append(root)
                        res['file'].append(f)
                        res['time'].append(modified_date)


    print(res)
    df = pd.DataFrame(res)
    df.to_csv('orchard.csv')

def findFile(target_name):
    def get_fixed_drives() -> Iterable[str]:
        """Return drive roots such as ['C:\\', 'D:\\'] on Windows."""
        bitmask = ctypes.windll.kernel32.GetLogicalDrives()
        for i in range(26):
            if bitmask & 1 << i:               # drive exists
                drive = f"{chr(65 + i)}:\\"
                if ctypes.windll.kernel32.GetDriveTypeW(drive) == 3:  # DRIVE_FIXED
                    yield drive

    def search(root: Path, target: str, case_sensitive: bool = False) -> None:
        """Walk *root* and print every file whose name contains *target*."""
        if not case_sensitive:
            target = target.lower()

        def _ignore(err):          # onerror callback that swallows “Access is denied”
            pass

        for dirpath, _, filenames in os.walk(root, topdown=True, onerror=_ignore):
            for fname in filenames:
                haystack = fname if case_sensitive else fname.lower()
                if target in haystack:
                    print(Path(dirpath) / fname)


    for drive in get_fixed_drives():
        print(f"\n>>> Scanning {drive}")
        try:
            search(Path(drive), target_name)
        except Exception as exc:           # extremely broad on purpose
            print(f"   [skipped {drive} – {exc}]")


if __name__ == '__main__':
    findFile("Lloyd")
    exit()
    walkPath(keys=['frac'],path="C:\\Users\\plaisancem\\CML Exploration\\Travis Wadman - CML")