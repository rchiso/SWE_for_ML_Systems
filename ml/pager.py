import requests
import os



def send_pager_request(mrn, timestamp):
    """
    Sends a pager request with MRN and timestamp.

    Args:
        mrn (str): The Medical Record Number (MRN).
        timestamp (str): The AKI detection timestamp.

    Returns:
        int or None: HTTP status code if the request is successful or fails with an HTTP error,
                     None if a network-related error occurs.
    """
    try:
        PAGER_PORT = 8441
        PAGER_URL = os.getenv('PAGER_ADDRESS', default=f"http://127.0.0.1:{PAGER_PORT}/page")
        if 'http' not in PAGER_URL:
            PAGER_URL = 'http://' + PAGER_URL + '/page'
        response = requests.post(PAGER_URL, data=f"{mrn},{timestamp}", timeout=0.2)
        return response.status_code  # Return actual status code
    except requests.exceptions.RequestException as e:
        print(f'[ml_pager] Network error while paging, {e}')
        return None  # Return None for network-related errors