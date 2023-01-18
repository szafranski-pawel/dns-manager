import json
import requests
import os


SERVER_ADDRESS = f"http://{os.environ['SERVER_ADDRESS']}"
ADMIN_API_KEY = os.environ['ADMIN_API_KEY']

# Create users and nodes
add_user_url = f"{SERVER_ADDRESS}/api/user"
add_node_url = f"{SERVER_ADDRESS}/api/node"
add_user_headers = {'content-type': 'application/json', 'X-Api-Key': ADMIN_API_KEY}
for i in range(5):
    new_user = {"name": f"test{str(i)}", "email": f"{str(i)}@a.pl", "password": "12345678", "subdomain": f"{str(i)}test"}
    resp = requests.post(add_user_url, data=json.dumps(new_user), headers=add_user_headers)
    print(resp.status_code, resp.text)
    for j in range(3):
        user_api_key = json.loads(resp.text).get("api_key")
        add_node_headers = {'content-type': 'application/json', 'X-Api-Key': user_api_key}
        new_node = {"subdomain": f"{str(j)}test"}
        resp_node = requests.post(add_node_url, data=json.dumps(new_node), headers=add_node_headers)
        print(resp_node.status_code, resp_node.text)