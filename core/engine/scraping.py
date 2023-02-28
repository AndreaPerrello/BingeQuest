import bs4
import cloudscraper
import requests

_base_kwargs = dict(timeout=10)


def get(url: str, cloud: bool = True, *args, **kwargs) -> requests.Response:
    if cloud:
        cloud_scraper = cloudscraper.create_scraper()
        return cloud_scraper.get(url, *args, timeout=10, **kwargs)
    return requests.get(url, *args, **kwargs)


def post(url: str, cloud: bool = True, *args, **kwargs) -> requests.Response:
    if cloud:
        cloud_scraper = cloudscraper.create_scraper()
        return cloud_scraper.post(url, *args, timeout=10, **kwargs)
    return requests.post(url, *args, **kwargs)


def get_soup(url: str, *args, **kwargs) -> bs4.BeautifulSoup:
    return bs4.BeautifulSoup(get(url, *args, **kwargs).text)


def post_soup(url: str, *args, **kwargs) -> bs4.BeautifulSoup:
    return bs4.BeautifulSoup(post(url, *args, **kwargs).text)
