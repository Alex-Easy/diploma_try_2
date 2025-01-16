import yaml
from .models import Shop, Category, Product
import os
from django.conf import settings


def import_products_from_yaml(file_name):
    try:
        file_path = os.path.join(settings.BASE_DIR, 'procurement', 'data', file_name)

        if not os.path.exists(file_path):
            print(f"File {file_name} does not exist at the specified path: {file_path}")
            return

        with open(file_path, 'r', encoding='utf-8') as file:
            data = yaml.safe_load(file)

        shop_name = data.get('shop')
        if not shop_name:
            print("Shop name is missing in the YAML file.")
            return

        shop, created = Shop.objects.get_or_create(name=shop_name, defaults={"state": True})

        categories = data.get('categories', [])
        for category_data in categories:
            Category.objects.get_or_create(
                id=category_data['id'],
                defaults={"name": category_data['name']}
            )

        goods = data.get('goods', [])
        for product_data in goods:
            category_id = product_data.get('category')
            category_name = next(
                (cat['name'] for cat in categories if cat['id'] == category_id), "Unnamed"
            )

            category, _ = Category.objects.get_or_create(
                id=category_id,
                defaults={"name": category_name}
            )

            Product.objects.update_or_create(
                id=product_data['id'],
                defaults={
                    'category': category,
                    'shop': shop,
                    'name': product_data['name'],
                    'model': product_data['model'],
                    'price': product_data['price'],
                    'price_rrc': product_data['price_rrc'],
                    'quantity': product_data['quantity'],
                    'parameters': product_data.get('parameters', {}),
                }
            )
            print(f"Product '{product_data['name']}' imported successfully.")

    except yaml.YAMLError as e:
        print(f"Error parsing YAML: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
