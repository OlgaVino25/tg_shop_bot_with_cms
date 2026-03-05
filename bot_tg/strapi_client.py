import logging
import requests
from io import BytesIO
from settings import STRAPI_BASE_URL

logger = logging.getLogger(__name__)

STRAPI_URL = f"{STRAPI_BASE_URL}/api/products"
CART_URL = f"{STRAPI_BASE_URL}/api/carts"
CART_ITEM_URL = f"{STRAPI_BASE_URL}/api/cart-items"
CUSTOMER_URL = f"{STRAPI_BASE_URL}/api/customers"


def fetch_products():
    """Возвращает список товаров."""
    response = requests.get(STRAPI_URL, params={"populate": "picture"})
    response.raise_for_status()
    return response.json().get("data", [])


def fetch_product(document_id: str):
    """Возвращает товар по document_id."""
    response = requests.get(
        f"{STRAPI_URL}/{document_id}", params={"populate": "picture"}
    )
    response.raise_for_status()
    return response.json().get("data")


def fetch_product_image(product):
    """Возвращает BytesIO с изображением товара."""
    picture = product.get("picture")
    if not picture or not isinstance(picture, dict):
        return None

    image_url = picture.get("url")
    if not image_url:
        return None

    if image_url.startswith("/"):
        image_url = f"{STRAPI_BASE_URL}{image_url}"

    response = requests.get(image_url, stream=True)
    response.raise_for_status()
    return BytesIO(response.content)


def get_or_create_cart(user_id: str):
    """Возвращает ID корзины для пользователя. Если нет — создаёт."""
    response = requests.get(CART_URL, params={"filters[userId][$eq]": user_id})
    response.raise_for_status()
    carts = response.json().get("data", [])

    if carts:
        return carts[0]["documentId"]

    creation_response = requests.post(CART_URL, json={"data": {"userId": user_id}})
    creation_response.raise_for_status()
    return creation_response.json()["data"]["documentId"]


def add_to_cart(cart_id: str, product_id: str, quantity: float = 1.0):
    """Добавляет товар в корзину (создаёт CartItem)."""
    filter_params = {
        "filters[cart][documentId][$eq]": cart_id,
        "filters[product][documentId][$eq]": product_id,
    }
    response = requests.get(CART_ITEM_URL, params=filter_params)
    response.raise_for_status()
    existing_cart_items = response.json().get("data", [])
    if existing_cart_items:
        item_id = existing_cart_items[0]["documentId"]
        new_qty = existing_cart_items[0]["quantity"] + quantity
        update_response = requests.put(
            f"{CART_ITEM_URL}/{item_id}", json={"data": {"quantity": new_qty}}
        )
        update_response.raise_for_status()
        return True

    payload = {
        "data": {
            "quantity": quantity,
            "product": {"connect": [product_id]},
            "cart": {"connect": [cart_id]},
        }
    }
    creation_response = requests.post(CART_ITEM_URL, json=payload)
    creation_response.raise_for_status()
    return True


def get_cart_contents(cart_id: str):
    """Возвращает список товаров в корзине с количеством."""
    response = requests.get(
        f"{CART_URL}/{cart_id}", params={"populate": "cart_items.product"}
    )
    response.raise_for_status()
    cart_data = response.json()["data"]
    items = cart_data.get("cart_items", [])
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


def delete_cart_item(item_id: str):
    """Удаляет элемент корзины по его documentId."""
    response = requests.delete(f"{CART_ITEM_URL}/{item_id}")
    response.raise_for_status()
    return True


def create_customer(user_id: str, email: str):
    """Создаёт запись клиента в Strapi."""
    payload = {"data": {"userId": user_id, "email": email}}
    response = requests.post(CUSTOMER_URL, json=payload)
    response.raise_for_status()
    logger.info(f"Customer created for user {user_id} with email {email}")
    return response.json()["data"]["documentId"]
