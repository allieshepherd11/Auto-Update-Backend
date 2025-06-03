import pdfplumber
import pandas as pd
from collections import defaultdict
from datetime import datetime


def is_date(string, date_formats=["%Y-%m-%d", "%m/%d/%Y"]):
    for date_format in date_formats:
        try:
            datetime.strptime(string, date_format)
            return True
        except ValueError:
            continue
    return False


pdf_path = "C:/Users/plaisancem/Downloads/PDSWDX-DP-contango-2025-03-06.pdf"
df = defaultdict(list)

with pdfplumber.open(pdf_path) as pdf:
    l = len(pdf.pages)
    for i in range(len(pdf.pages)):
        print(i)
        #if i in errors: continue
        txt = pdf.pages[i].extract_text()
        lines = txt.split('\n')
        for iline in range(len(lines)): 
            if iline <= 2: continue
            cells = lines[iline].split(' ')
            date_idx = [i for i, value in enumerate(cells) if is_date(value)]
            if len(date_idx) != 0:
                date_idx = date_idx[0]
                well_name = " ".join(cells[2:date_idx])
                df['Well Name'].append(well_name)
                df['Date'].append(cells[date_idx])
                df['Oil'].append(cells[date_idx+1])
                df['Gas'].append(cells[date_idx+2])
                df['Water'].append(cells[date_idx+3])
                df['Page Number'].append(i+1)

pd.DataFrame(df).to_csv('contago_wells.csv',index=False)