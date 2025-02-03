import requests


def send_pager_request(mrn, timestamp):
    r = requests.post('http://127.0.0.1:8441', data=f'{mrn}, {timestamp}', timeout=0.2)
    return r.status_code