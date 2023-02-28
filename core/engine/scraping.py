import bs4
import cloudscraper
import requests

import logging
LOGGER = logging.getLogger(__name__)


def get(url: str, cloud: bool = False, *args, **kwargs) -> requests.Response:
    if cloud:
        cloud_scraper = cloudscraper.create_scraper()
        result = cloud_scraper.get(url, *args, **kwargs)
    else:
        result = requests.get(url, *args, verify=False, **kwargs)
    LOGGER.info(result.text)
    return result


def post(url: str, cloud: bool = False, *args, **kwargs) -> requests.Response:
    if cloud:
        cloud_scraper = cloudscraper.create_scraper()
        result = cloud_scraper.post(url, *args, **kwargs)
    else:
        result = requests.post(url, *args, verify=False, **kwargs)
    LOGGER.info(result.text)
    return result


def get_soup(url: str, *args, **kwargs) -> bs4.BeautifulSoup:
    return bs4.BeautifulSoup(get(url, *args, **kwargs).text)


def post_soup(url: str, *args, **kwargs) -> bs4.BeautifulSoup:
    return bs4.BeautifulSoup(post(url, *args, **kwargs).text)
