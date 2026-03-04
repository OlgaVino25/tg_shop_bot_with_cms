import logging
import requests
from io import BytesIO
from requests.exceptions import RequestException

logger = logging.getLogger(__name__)

STRAPI_URL = "http://localhost:1337/api/products"
CART_URL = "http://localhost:1337/api/carts"
CART_ITEM_URL = "http://localhost:1337/api/cart-items"


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


def get_or_create_cart(user_id: str):
    """Возвращает ID корзины для пользователя. Если нет — создаёт."""
    try:
        response = requests.get(CART_URL, params={"filters[userId][$eq]": user_id})
        if response.ok:
            data = response.json().get("data", [])
            if data:
                return data[0]["documentId"]
        create_response = requests.post(CART_URL, json={"data": {"userId": user_id}})
        if create_response.ok:
            return create_response.json()["data"]["documentId"]
    except RequestException:
        logger.exception("Ошибка при работе с корзиной")
    return None


def add_to_cart(cart_id: str, product_id: str, quantity: float = 1.0):
    """Добавляет товар в корзину (создаёт CartItem)."""
    try:
        filter_params = {
            "filters[cart][documentId][$eq]": cart_id,
            "filters[product][documentId][$eq]": product_id,
        }
        response = requests.get(CART_ITEM_URL, params=filter_params)
        if response.ok:
            existing = response.json().get("data", [])
            if existing:
                item_id = existing[0]["documentId"]
                new_qty = existing[0]["quantity"] + quantity
                upd_response = requests.put(
                    f"{CART_ITEM_URL}/{item_id}", json={"data": {"quantity": new_qty}}
                )
                return upd_response.ok
        payload = {
            "data": {
                "quantity": quantity,
                "product": {"connect": [product_id]},
                "cart": {"connect": [cart_id]},
            }
        }
        create_response = requests.post(CART_ITEM_URL, json=payload)
        return create_response.ok
    except RequestException:
        logger.exception("Ошибка при добавлении в корзину")
    return False


def get_cart_contents(cart_id: str):
    """Возвращает список товаров в корзине с количеством."""
    try:
        response = requests.get(
            f"{CART_URL}/{cart_id}", params={"populate": "cart_items.product"}
        )
        if response.ok:
            data = response.json()["data"]
            items = data.get("cart_items", [])
            result = []
            for item in items:
                product = item.get("product", {})
                result.append(
                    {
                        "title": product.get("title"),
                        "price": product.get("price"),
                        "quantity": item.get("quantity"),
                        "item_id": item["documentId"],
                    }
                )
            return result
    except RequestException:
        logger.exception("Ошибка при получении корзины")
    return None


def delete_cart_item(item_id: str):
    """Удаляет элемент корзины по его documentId."""
    try:
        response = requests.delete(f"{CART_ITEM_URL}/{item_id}")
        return response.ok
    except RequestException:
        logger.exception(f"Ошибка при удалении элемента корзины {item_id}")
        return False
