import cloudscraper
import requests

cloud_scraper = cloudscraper.create_scraper()
flaresolverr_url = 'http://localhost:8191'


def get(url, *args, **kwargs):
    return cloud_scraper.get(url, *args, **kwargs)


def get_flare(url, max_timeout: int = 60):
    data = {'cmd': 'request.get', 'url': url, 'maxTimeout': max_timeout * 1000}
    response = requests.post(f"{flaresolverr_url}/v1", json=data)
    if response.ok:
        return_data = response.json()
        if return_data['status'] == 'ok':
            return return_data['solution']['response']


def post(url, *args, **kwargs):
    return cloud_scraper.post(url, *args, **kwargs)
