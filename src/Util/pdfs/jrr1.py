import pdfplumber
from collections import defaultdict
import pandas as pd


def extract_value_from_line(line, x_min, x_max):
    # Filter characters that fall completely within the specified x-range.
    selected_chars = [
        char for char in line.get('chars', [])
        if char['x0'] >= x_min and char['x1'] <= x_max
    ]
    
    # Sort the characters by their x0 position to ensure proper reading order.
    selected_chars.sort(key=lambda c: c['x0'])
    
    result = ""
    space_threshold = 5
    prev_char = None
    for char in selected_chars:
        if prev_char is not None:
            # If the gap between the current and previous character exceeds the threshold, insert a space.
            gap = char['x0'] - prev_char['x1']
            if gap > space_threshold:
                result += " "
        result += char['text']
        prev_char = char
    return result

def read_pdf_lines_extract_value(pdf_path):
    df = defaultdict(list)
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            print(page_num)
            # Extract lines; each line is a dict that includes a 'chars' attribute.
            lines = page.extract_text_lines()
            for idx,line in enumerate(lines):
                #if idx != 14:continue
                print(idx,line['text'])
                exit()

                well_name = extract_value_from_line(line, 0, 165)
                interest = extract_value_from_line(line, 300, 350)
                descript = extract_value_from_line(line, 400, 520)
                expire_date = extract_value_from_line(line, 515, 570)

                #print(well_name)
                #print(interest)
                #print(descript)
                #print(expire_date)
                #exit()

                if well_name != '':
                    if 'PRIMARY' in descript:
                        try:
                            interest = float(interest)
                        except ValueError:
                            continue

                        df['Well Name'].append(well_name)
                        df['Interest'].append(interest)
                        df['Expire Date'].append(expire_date)
                        df['Description'].append(descript)
                        
                        df['Page'].append(page_num)
    
    return pd.DataFrame(df)


if __name__ == '__main__':
    pdf_path = r"C:\Users\plaisancem\Downloads\plaisanc_JIB721.0_1549.pdf"
    df = read_pdf_lines_extract_value(pdf_path)
    df.loc[df['Expire Date'] == '', 'Expire Date'] = '3/26/2025'
    df['Expire Date'] = pd.to_datetime(df['Expire Date'])
    df = df.loc[df.groupby('Well Name')['Expire Date'].idxmax()].reset_index(drop=True)

    df.to_csv('ssd interest.csv',index=False)
   
