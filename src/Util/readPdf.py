import pdfplumber
import pandas as pd

def pdf_to_dataframe(pdf_path, page_number=0):
    # Open the PDF file
    with pdfplumber.open(pdf_path) as pdf:
        # Select the specific page
        page = pdf.pages[page_number]
        
        # Extract tables from the page
        tables = page.extract_tables()
        
        if not tables:
            print("No tables found on this page.")
            return None
        
        # Assuming the first table is the one we need
        table = tables[0]
        
        # Create a DataFrame
        df = pd.DataFrame(table[1:], columns=table[0])
        return df

# Example usage
pdf_path = "G:/CML Operations/WELL FILES/Dial #1 ST/REPORTS-DAILY OPS/Individual Reports/2024-03-22 Dial ST #1.pdf"
df = pdf_to_dataframe(pdf_path)
if df is not None:
    print(df)
    df.to_csv('table.csv')