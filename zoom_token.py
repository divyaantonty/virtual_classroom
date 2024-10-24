import requests
from requests.auth import HTTPBasicAuth

# Replace these with your actual credentials
client_id = '95w1T2nlSpOWyuxu5Gjh4w'
client_secret = 'IXjEp1mgI5w5HEb3VHR3NS8taAmyCX5q'
account_id = 'bs4hsQ6GRte8O-EHmG8uDQ'

url = f'https://zoom.us/oauth/token?grant_type=account_credentials&account_id={account_id}'

response = requests.post(url, auth=HTTPBasicAuth(client_id, client_secret))

if response.status_code == 200:
    access_token = response.json().get('access_token')
    print(f"Access Token: {access_token}")
else:
    print(f"Failed to get Access Token. Status code: {response.status_code}")
    print(f"Response: {response.text}")
