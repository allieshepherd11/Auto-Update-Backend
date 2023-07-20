import pandas as pd
import numpy as np
from fpdf import FPDF
import webbrowser

class ProdReport():
    def __init__(self, field,title):
        self.field = field
        self.title = title
        self.dtype = {'Oil (BBLS)': float, 'Water (BBLS)': float, 'Gas (MCF)': float, 'TP': float, 'CP': float, 'Comments': str}
        self.df = pd.read_csv(f'data\\prod\\{self.field}\\data.csv', dtype=self.dtype)
    
    def prepdf(self, df):
        df = df[df['Well Name'] != 'South Texas Total']
        today = df['Date'][0]
        mon = today[:-3]
        df['Date'] = pd.to_datetime(df['Date'])
        df_mon = pd.DataFrame(df[df['Date'].dt.strftime('%Y-%m') == mon])
        df_mon = df_mon.drop(['Date','TP','CP','Comments'],axis=1)
        df_monCuml = df_mon.groupby('Well Name').sum()
        df_monCuml = df_monCuml.rename({'Oil (BBLS)': 'MTD Oil','Gas (MCF)': 'MTD Gas','Water (BBLS)': 'MTD Water' },axis=1)

        df = pd.merge(df,df_monCuml,on='Well Name')
        
        df = df.reindex(columns=['Well Name','Date','Oil (BBLS)','Gas (MCF)','Water (BBLS)', 'MTD Oil', 'MTD Gas', 'MTD Water','TP','CP','Comments'])
        df = df[df['Date'] == today]
        df = df.sort_values(['Date', 'Well Name'], ascending = [False , True])
        df = df.drop(['Date'],axis=1).fillna('')
        
        for col in df.columns:
            if df[col].dtype == float:
                df[col] = np.round(df[col]).astype('Int64')
        widths = self.workoutWidth(df)
        return df.reset_index(drop=True),widths,today
    
    def workoutWidth(self, df):
        df = pd.DataFrame(df)
        pdf = FPDF()
        pdf.set_font("Arial", size=7)

        print(df)
        widths = {}
        pos_end = pdf.l_margin
        for col in df.columns:
            widths[col] = {}
            longest = max(df[col].astype(str).tolist(),key=pdf.get_string_width)
    
            print(f'{col} longest {longest}')
            title = col.split(' ')
            if len(title) == 2:
                unit = '(MCF)' if title[1] == 'Gas' else '(BBLS)'
                if title[0] == 'Well': widths[col]['r1'] = col; widths[col]['r2'] = ''
                elif title[0] == 'MTD': widths[col]['r1'] = title[1]; widths[col]['r2'] = unit
                else: widths[col]['r1'] = title[0]; widths[col]['r2'] = title[1]
            else: widths[col]['r1'] = col; widths[col]['r2'] = ''
            
            offset = 6
            if col == 'TP' or col == 'CP': offset = 2

            widths[col]['width'] = pdf.get_string_width(longest) + offset
            pos_end += widths[col]['width']

            widths[col]['pos_end'] = pos_end
        pw = pdf.w - 2 * pdf.l_margin
        gifts = (pw - 30) - widths['Comments']['pos_end']
        if gifts > 0:
            gift = gifts/(len(widths)-1)
            for idx,poor in enumerate(widths):
                if widths[poor]['r1'] == 'Comments':continue
                widths[poor]['width'] += gift
                widths[poor]['pos_end'] += gift*(idx + 1)
        return widths
    
    def genReport(self):
        df,col_widths,today = self.prepdf(self.df)
        print(df)
        pdf = FPDF()
        pdf.set_font("Arial", size=10)

        row_height = pdf.font_size * 1.5
        page_width = pdf.w - 2 * pdf.l_margin

        comm_offset = 0
        def header():
            pdf.set_font("Arial", style="B", size=16)
            pdf.cell(0, 10, txt=self.title, ln=True, align="C")
            pdf.cell(0, 10, txt="Daily Gross Production Report", border='B', ln=True, align="C")
            pdf.set_font("Arial", size=10)
            pdf.cell(0, 8, txt=today, ln=True, align="R")

            pdf.set_x(col_widths['MTD Oil']['pos_end'])
            pdf.set_font("Arial", size=7)
            pdf.cell(0, 5, txt='**MTD**',ln=True)
            pdf.ln(0)

            for r in ['r1','r2']:
                brdr = 0
                if r == 'r2': pdf.cell(0, row_height, ln=True);pdf.set_font("Arial", size=6); brdr = 'B'
                for _,info in col_widths.items():
                    pdf.cell(0, row_height, txt=info[r],border=brdr)
                    pdf.set_x(info['pos_end'])
            pdf.cell(0, 5, txt='',ln=True)
            
            pdf.ln(row_height)
            nonlocal comm_offset
            comm_offset = col_widths['Comments']['pos_end'] - col_widths['Comments']['width']

        

        pdf.add_page()
        header()
        mb = pdf.b_margin

        for _, row in df.iterrows():
            if pdf.y + pdf.font_size * 1.5 > pdf.h - pdf.b_margin:
                pdf.add_page()
                header()
            pdf.set_font("Arial", size=7)

            for col in df.columns:
                cell_value = str(row[col]).replace("’","")
                cell_width = col_widths[col]['width']
                
                if col == 'Comments':
                    cell_width = page_width - col_widths['CP']['pos_end'] + pdf.l_margin
                    comm_width = pdf.get_string_width(cell_value)
                    words = cell_value.split(' ')
                    if comm_width + 2 > cell_width: 
                        w = words[:]
                        cnt = 0
                        while comm_width + 2 > cell_width:
                            cnt += 1
                            w.pop()
                            comm1 = ' '.join(w)
                            comm_width = pdf.get_string_width(comm1)
                        
                        comm2 = ' '.join(words[-cnt:])

                        pdf.cell(cell_width, row_height, txt=comm1, border='LTR', ln=True, align='L')
                        if pdf.y + row_height > pdf.h - pdf.b_margin: pdf.set_auto_page_break(0,0)

                        pdf.set_x(comm_offset)
                        pdf.cell(cell_width, row_height, txt=comm2, border='LRB', ln=False, align='L')

                        pdf.set_auto_page_break(1,mb)
                        continue   

                    

                pdf.cell(cell_width, row_height, txt=cell_value, border=1, ln=False, align='L')
            pdf.ln(row_height)

        pdf.output(f'data/prod/{self.field}/report.pdf','F')    

#if __name__ == '__main__':
#    for FIELD,TITLE in {'ST':'South Texas','ET':'East Texas'}.items():
#        reprt = ProdReport(field=FIELD,title=TITLE)
#        reprt.genReport()
#        webbrowser.open_new_tab(f"C:\\Users\\plaisancem\\Documents\\dev\\prod app\\backend\\data/prod/{FIELD}/report.pdf")
