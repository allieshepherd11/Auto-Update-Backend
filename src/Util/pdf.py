import pdfplumber
import pandas as pd
from collections import defaultdict
from datetime import datetime

def get_next_chars(text, target,depth=10):
    index = text.find(target)  # Find the index of the target
    if index == -1:
        return ''  # Return None if the target is not found

    start = index + len(target)  # Start position after the target
    return text[start:start + depth] 

def is_date(string, date_formats=["%Y-%m-%d", "%m/%d/%Y"]):
    for date_format in date_formats:
        try:
            datetime.strptime(string, date_format)
            return True
        except ValueError:
            continue
    return False

def search_page(lines,key):
    val = ''
    for i,l in enumerate(lines):
        if key in l.lower():
            if key == 'operator':
                val = l.split(':')[-1]
                return val
            if key == 'working interest' or key == 'revenue interest': 
                val = l.split(':')[-1]
                val = val.split(' ')[1]
            if key == 'case':
                val = l.split(':')[-1]
                return val
            if key == '10.00%':
                chars = get_next_chars(l, key,9)
                val = chars.split(':')[-1].strip()
                val = val.replace('P','').strip()
                return val
            if key == '20.00%':
                chars = get_next_chars(l, key)
                val = chars.split(':')[-1].strip()
                return val
            if key == '30.00%':
                chars = get_next_chars(l, key)
                val = chars.split(':')[-1].strip()
                return val
            if key == 'co.':
                chars = get_next_chars(l,'Co., State :')
                val = chars.split(',')[0]
                return val
    return val

pdf_path = "C:/Users/plaisancem/Downloads/east texas economics - 2025-01-01 - nymex.pdf"
df = defaultdict(list)
#errors = [41,50,52,55,79,107]

with pdfplumber.open(pdf_path) as pdf:
    l = len(pdf.pages)
    for i in range(len(pdf.pages)):
        if i == 0 or i == 1:continue
        #if i in errors: continue
        df['Page Number'].append(i+1)
        #if i != 10:continue
        txt = pdf.pages[i].extract_text()
        lines = txt.split('\n')
        api_num = lines[8].split(':')[-1].rstrip('0')


        county = search_page(lines,'co.')
        pv20 = search_page(lines,'20.00%')
        pv10 = search_page(lines,'10.00%')
        pv30 = search_page(lines,'30.00%')
        well_name = search_page(lines,'case')
        operator = search_page(lines,'operator')
        wi = search_page(lines,'working interest')
        ri = search_page(lines,'revenue interest')

        df['Well Name'].append(well_name)
        df['API Number'].append(api_num)
        df['County'].append(county)
        df['Operator'].append(operator)
        df['Working Interest'].append(wi)
        df['Revenue Interest'].append(ri)
        df['PV10'].append(pv10)
        df['PV20'].append(pv20)
        df['PV30'].append(pv30)


        continue
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

pd.DataFrame(df).to_csv('ptn_summary.csv',index=False)
                