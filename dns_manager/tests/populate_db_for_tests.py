import itertools
import json
import requests
import os
import concurrent.futures
import time
from functools import wraps

SERVER_ADDRESS = "https://dns-manager.elka-dns.pl"
ADMIN_API_KEY = os.environ['ADMIN_API_KEY']

# Create users and nodes URLs
add_user_url = f"{SERVER_ADDRESS}/api/user"
add_node_url = f"{SERVER_ADDRESS}/api/node"


def timeit(method):
    @wraps(method)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = method(*args, **kwargs)
        end_time = time.time()
        print(f"{method.__name__} => {(end_time-start_time)} s")

        return result

    return wrapper


@timeit
def add_node(nr, api_key):
    add_node_headers = {'content-type': 'application/json', 'X-Api-Key': api_key}
    new_node = {"subdomain": f"{str(nr)}test"}
    resp_node = requests.post(add_node_url, data=json.dumps(new_node), headers=add_node_headers)
    return resp_node.status_code


@timeit
def add_user(nr):
    add_user_headers = {'content-type': 'application/json', 'X-Api-Key': ADMIN_API_KEY}
    new_user = {"name": f"test{str(nr)}", "email": f"{str(nr)}@a.pl", "password": "12345678", "subdomain": f"{str(nr)}test"}
    resp = requests.post(add_user_url, data=json.dumps(new_user), headers=add_user_headers)
    return resp.status_code, resp.text

user_api_keys = []
with concurrent.futures.ProcessPoolExecutor(max_workers=100) as executor:
    future_to_url_user = (executor.submit(add_user, i) for i in range(90, 120))
    for future in concurrent.futures.as_completed(future_to_url_user):
        try:
            data = future.result()
        except Exception as exc:
            data = str(type(exc))
        finally:
            print(data[0])
            raw_json = json.loads(data[1])
            user_api_keys.append(raw_json["api_key"])

# with concurrent.futures.ProcessPoolExecutor(max_workers=200) as executor:
#     future_to_url_node = (executor.submit(add_node, i, api_key) for api_key, i in itertools.product(user_api_keys, range(0,5)))
#     for future in concurrent.futures.as_completed(future_to_url_node):
#         try:
#             data = future.result()
#         except Exception as exc:
#             data = str(type(exc))
#         finally:
#             print(data)