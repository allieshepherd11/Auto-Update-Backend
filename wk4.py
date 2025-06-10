from pathlib import Path
import subprocess
import sys

SOFFICE = r"C:\Program Files\LibreOffice\program\soffice.exe"  # adjust if needed

def convert_wk4(wk4_path: Path) -> Path:
    out_dir = "./"
    subprocess.run(
        [SOFFICE, "--headless", "--convert-to", "xlsx", str(wk4_path),
         "--outdir", str(out_dir)],
        check=True
    )
    return wk4_path.with_suffix(".xlsx")

def main():
    wk4_file = "./HARGRAVE.WK4"
    xlsx_file = convert_wk4(wk4_file)
    print(f"Converted to {xlsx_file}")

if __name__ == "__main__":
    main()
