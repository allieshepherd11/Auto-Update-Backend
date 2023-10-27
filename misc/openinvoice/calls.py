import requests
x = requests.get('https://api.openinvoice.com/docp/supply-chain/v1/coding',verify=False)

#x = requests.get('https://api.openinvoice.com/docp/supply-chain/v1/invoices',verify=False)
print(x)