from bs4 import BeautifulSoup
import csv

with open('testing/table.html', 'r', encoding='utf-8') as file:
    html_content = file.read()
# Parse the HTML content
soup = BeautifulSoup(html_content, 'html.parser')
table = soup.find('table')
# Extract rows
rows = table.find_all('tr')

# Open a CSV file for writing
with open('output.csv', 'w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    
    for row in rows:
        # Extract cell data
        cells = row.find_all(['td', 'th'])
        row_data = [cell.get_text(strip=True) for cell in cells]
        writer.writerow(row_data)

print("HTML table has been converted to output.csv.")
