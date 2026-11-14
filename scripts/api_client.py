"""Minimal HTTP helper shared by the manual API test scripts."""
import json
import urllib.request

BASE_URL = "http://127.0.0.1:5000"
TIMEOUT = 15


def post_json(path, payload, base_url=BASE_URL, timeout=TIMEOUT):
    """POST a JSON payload to the local API and return the raw response body."""
    request = urllib.request.Request(
        base_url + path,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode()    
