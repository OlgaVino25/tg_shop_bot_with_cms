import requests
from requests.exceptions import RequestException
import logging

logger = logging.getLogger(__name__)

STRAPI_URL = "http://localhost:1337/api/products"


def fetch_products():
    """Возвращает список товаров или None при ошибке."""
    try:
        response = requests.get(STRAPI_URL)
        if response.ok:
            return response.json().get("data", [])
        else:
            logger.error(f"Strapi error: {response.status_code}")
    except RequestException:
        logger.exception("Ошибка подключения к Strapi при запросе списка товаров")
    return None


def fetch_product(document_id: str):
    """Возвращает товар по document_id или None при ошибке."""
    try:
        response = requests.get(f"{STRAPI_URL}/{document_id}")
        if response.ok:
            return response.json().get("data")
        else:
            logger.error(
                f"Strapi error {response.status_code} for product {document_id}"
            )
    except RequestException:
        logger.exception(f"Ошибка при запросе товара {document_id}")
    return None
