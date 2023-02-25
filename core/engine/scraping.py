import bs4
import cloudscraper
import requests
import twocaptcha

cloud_scraper = cloudscraper.create_scraper()
# flaresolverr_url = 'http://localhost:8191'

_2CAPTCHA_API_KEY = 'b25e37f8f3b2742548fa41fc1222feb5'


def get(url, cloud: bool = True, *args, **kwargs) -> requests.Response:
    if cloud:
        return cloud_scraper.get(url, *args, **kwargs)
    return requests.get(url, *args, **kwargs)


# def get_flare(url, max_timeout: int = 60):
#     data = {'cmd': 'request.get', 'url': url, 'maxTimeout': max_timeout * 1000}
#     response = requests.post(f"{flaresolverr_url}/v1", json=data)
#     if response.ok:
#         return_data = response.json()
#         if return_data['status'] == 'ok':
#             return return_data['solution']['response']


def post(url, cloud: bool = True, *args, **kwargs) -> requests.Response:
    if cloud:
        return cloud_scraper.post(url, *args, **kwargs)
    return requests.post(url, *args, **kwargs)


def solve_captcha(url: str) -> str:
    page_soup = bs4.BeautifulSoup(get(url).text)
    k = page_soup.findAll(lambda t: t.name == 'div' and 'data-sitekey' in t.attrs)[0]['data-sitekey']
    solver = twocaptcha.TwoCaptcha(_2CAPTCHA_API_KEY)
    return solver.solve_captcha(k, url)
