import bs4
import cloudscraper
import requests


def get(url: str, cloud: bool = True, *args, **kwargs) -> requests.Response:
    if cloud:
        cloud_scraper = cloudscraper.create_scraper()
        return cloud_scraper.get(url, *args, **kwargs)
    return requests.get(url, *args, **kwargs)


def post(url: str, cloud: bool = True, *args, **kwargs) -> requests.Response:
    if cloud:
        cloud_scraper = cloudscraper.create_scraper()
        return cloud_scraper.post(url, *args, **kwargs)
    return requests.post(url, *args, **kwargs)


def get_soup(url: str, *args, **kwargs) -> bs4.BeautifulSoup:
    return bs4.BeautifulSoup(get(url, *args, **kwargs).text)


def post_soup(url: str, *args, **kwargs) -> bs4.BeautifulSoup:
    return bs4.BeautifulSoup(post(url, *args, **kwargs).text)
