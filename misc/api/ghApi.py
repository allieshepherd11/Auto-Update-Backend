def fetchGh(repo_owner,repo,file_path):
    import requests,json,dotenv,os

    dotenv.load_dotenv()
    token = os.getenv('TOKEN_MPPROD')

    api_url = f'https://api.github.com/repos/{repo_owner}/{repo}/contents/{file_path}'
    response = requests.get(api_url, headers={
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3.raw',  
    })

    if response.status_code == 200:
        content,outfile = response.json(),'output.json'
        with open(outfile, 'w') as f:
            json.dump(content, f, indent=4)
        print(f'dumped to {outfile}')
    else: print(f"Failed: {response.status_code} - {response.text}")


if __name__ == "__main__": fetchGh(repo_owner='dailyprod',repo='prod',file_path='data/ST/prodST.json')