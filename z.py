import os
import xlrd
from openpyxl import Workbook

def xls_xlsx(input_file_path,output_file_path):
    xls_workbook = xlrd.open_workbook(input_file_path)

    xlsx_workbook = Workbook()

    for sheet_name in xls_workbook.sheet_names():
        xls_sheet = xls_workbook.sheet_by_name(sheet_name)
        xlsx_sheet = xlsx_workbook.create_sheet(title=sheet_name)
        
        for row_index in range(xls_sheet.nrows):
            for col_index in range(xls_sheet.ncols):
                cell_value = xls_sheet.cell_value(row_index, col_index)
                xlsx_sheet.cell(row=row_index + 1, column=col_index + 1, value=cell_value)

    if 'Sheet' in xlsx_workbook.sheetnames:
        xlsx_workbook.remove(xlsx_workbook['Sheet'])

    xlsx_workbook.save(output_file_path)
    os.remove(ifile)

    print(f"File '{input_file_path}' converted and saved as '{output_file_path}'")


input_file_path = "C:\\Users\\plaisancem\\Documents\\well_files\\JIC #1\\ST01.xls"

output_file_path = "C:\\Users\\plaisancem\\Documents\\well_files\\JIC #1\\ST01.xlsx"
path = 'C:\\Users\\plaisancem\\Documents\\well_files'

for well in os.listdir(path=path):
    print(well)
    folder = f'{path}\\{well}'
    for file in os.listdir(path=folder):
        ifile = f'{folder}\\{file}'
        if file[-1] == 's':
            print(f'XLS FILE: {ifile}' )
            ofile = f'{ifile}x'
            print(f'OFILE {ofile}')
            xls_xlsx(ifile,ofile)
        else: print(f'excel file : {ifile}')