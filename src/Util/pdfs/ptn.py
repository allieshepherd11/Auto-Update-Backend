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

def search_page_ptn_append(df,txt):
    lines = txt.split('\n')
    api_num = lines[8].split(':')[-1].rstrip('0')


    county = search_page(lines,'co.')
    #pv00 = search_page(lines,'0.00%')
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
    df['PTN Working Interest'].append(wi)
    df['PTN Revenue Interest'].append(ri)
    #df['PTN PV0'].append(pv00)
    df['PTN PV10'].append(pv10)
    df['PTN PV20'].append(pv20)
    df['PTN PV30'].append(pv30)

    wi_jrr = .07625
    if county == 'MADISON':
        wi_jrr = .07625
    if county == 'GRIMES':
        wi_jrr == .12525
    if county == 'BRAZOS':
        wi_jrr = .11491880
        
    df['JRR Working Interest'].append(wi_jrr)
    return df,well_name

def read_pdf(pdf_path):
    df = defaultdict(list)
    df_cf = defaultdict(list)
    with pdfplumber.open(pdf_path) as pdf:
        l = len(pdf.pages)
        for pg_num,page in enumerate(pdf.pages,start=1):
            if pg_num == 2:continue
            #if pg_num != 9:continue
            df['Page Number'].append(pg_num)
            txt = page.extract_text()
            df,well_name = search_page_ptn_append(df,txt)

            bbox = (0, 180, page.width, 400)
            cropped_page = page.within_bbox(bbox)
            text = cropped_page.extract_text()
            lines = text.splitlines() if text else []

            
            for line in lines:
                els = line.split(' ')
                if len(els) == 14:
                    df_cf['Well Name'].append(well_name)
                    df_cf['Year'].append(els[0])
                    df_cf['Oil Gross (MBBL)'].append(els[1])
                    df_cf['Gas Gross (MMcf)'].append(els[2])
                    df_cf['Oil Net (MBBL)'].append(els[3])
                    df_cf['Gas Net (MMcf)'].append(els[4])
                    df_cf['Oil Price'].append(els[5])
                    df_cf['Gas Price'].append(els[6])
                    df_cf['Net Rev (M$)'].append(els[7])
                    df_cf['Costs Net (M$)'].append(els[9])
                    df_cf['Taxes Net (M$)'].append(els[10])
                    df_cf['Invest Net (M$)'].append(els[11])
                    df_cf['Nominal CF (M$)'].append(els[12])
                    df_cf['Cuml Disc CF (M$)'].append(els[13])
                else:
                    print(line)

    
    return pd.DataFrame(df),pd.DataFrame(df_cf)

if __name__ == '__main__':
    pdf_path = "C:/Users/plaisancem/Downloads/east texas economics - 2025-01-01 - nymex.pdf"
    df,df_cf = read_pdf(pdf_path)
    #df.to_csv('ptn_summary.csv',index=False)
    df_cf.to_csv('ptn_cf.csv',index=False)


                