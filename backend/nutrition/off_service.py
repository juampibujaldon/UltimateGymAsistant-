from typing import Optional

import httpx
from fastapi import HTTPException

from nutrition.schemas import FoodLookupResult


OPEN_FOOD_FACTS_URL = "https://world.openfoodfacts.org/api/v2/product"


def _safe_float(value: Optional[float]) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


class OpenFoodFactsService:
    def lookup_barcode(self, barcode: str) -> FoodLookupResult:
        response = httpx.get(f"{OPEN_FOOD_FACTS_URL}/{barcode}.json", timeout=12.0)
        response.raise_for_status()
        payload = response.json()

        if payload.get("status") != 1 or not payload.get("product"):
            raise HTTPException(status_code=404, detail="Product not found for this barcode.")

        product = payload["product"]
        nutrients = product.get("nutriments", {})

        return FoodLookupResult(
            barcode=barcode,
            name=product.get("product_name") or product.get("generic_name") or "Unknown product",
            brand=product.get("brands"),
            image_url=product.get("image_front_url") or product.get("image_url"),
            default_grams=_safe_float(product.get("product_quantity")) or 100,
            calories_per_100g=_safe_float(nutrients.get("energy-kcal_100g")),
            protein_per_100g=_safe_float(nutrients.get("proteins_100g")),
            carbs_per_100g=_safe_float(nutrients.get("carbohydrates_100g")),
            fat_per_100g=_safe_float(nutrients.get("fat_100g")),
            fiber_per_100g=_safe_float(nutrients.get("fiber_100g")),
            sugar_per_100g=_safe_float(nutrients.get("sugars_100g")),
        )
