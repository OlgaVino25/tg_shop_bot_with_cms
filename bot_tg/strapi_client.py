import logging
import requests
from io import BytesIO
from requests.exceptions import RequestException

logger = logging.getLogger(__name__)

STRAPI_URL = "http://localhost:1337/api/products"


def fetch_products():
    """Возвращает список товаров или None при ошибке."""
    try:
        response = requests.get(STRAPI_URL, params={"populate": "picture"})
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
        response = requests.get(
            f"{STRAPI_URL}/{document_id}", params={"populate": "picture"}
        )
        if response.ok:
            return response.json().get("data")
        else:
            logger.error(
                f"Strapi error {response.status_code} for product {document_id}"
            )
    except RequestException:
        logger.exception(f"Ошибка при запросе товара {document_id}")
    return None


def fetch_product_image(product):
    """Извлекает изображение из объекта товара (уже полученного через fetch_product)
    и возвращает BytesIO или None.
    """
    picture = product.get("picture")
    if not picture or not isinstance(picture, dict):
        return None

    image_url = picture.get("url")
    if not image_url:
        return None

    if image_url.startswith("/"):
        base_url = "http://localhost:1337"
        image_url = base_url + image_url

    try:
        response = requests.get(image_url, stream=True)
        if response.ok:
            return BytesIO(response.content)
        else:
            logger.error(f"Failed to download image: {response.status_code}")
    except RequestException:
        logger.exception("Error downloading image")
    return None
