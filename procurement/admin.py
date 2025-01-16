from django.contrib import admin, messages
from django.urls import path
from django.shortcuts import render, redirect
import yaml
from django.conf import settings
import os
from .models import User, Contact, Shop, Category, Product, Basket, Order
from .utils import import_products_from_yaml


# Custom Actions
@admin.action(description="Mark orders as 'Delivered'")
def mark_orders_as_delivered(modeladmin, request, queryset):
    queryset.update(status='delivered')
    messages.success(request, "Selected orders have been marked as delivered.")


@admin.action(description="Reset user password via email")
def reset_user_password(modeladmin, request, queryset):
    for user in queryset:
        # Implement your API call here or custom logic
        messages.info(request, f"Password reset email sent to {user.email}.")


@admin.action(description="Activate selected shops")
def activate_shops(modeladmin, request, queryset):
    queryset.update(state=True)
    messages.success(request, "Selected shops have been activated.")


@admin.action(description="Deactivate selected shops")
def deactivate_shops(modeladmin, request, queryset):
    queryset.update(state=False)
    messages.success(request, "Selected shops have been deactivated.")


@admin.action(description="Upload price list for selected shops")
def upload_price_list(modeladmin, request, queryset):
    """
    Custom admin action to upload price list for selected shops.
    """
    if 'apply' in request.POST:
        yaml_file = request.FILES.get('yaml_file')
        if not yaml_file:
            messages.error(request, "No file provided.")
            return redirect(request.get_full_path())

        try:
            # Сохраняем файл и импортируем данные
            temp_file_path = os.path.join(settings.BASE_DIR, 'temp_price_list.yaml')
            with open(temp_file_path, 'wb') as temp_file:
                for chunk in yaml_file.chunks():
                    temp_file.write(chunk)

            import_products_from_yaml(temp_file_path)
            messages.success(request, "Price list uploaded successfully.")
        except Exception as e:
            messages.error(request, f"Error uploading price list: {e}")
        return redirect(request.get_full_path())

    return render(request, 'admin/upload_price_list.html', {'queryset': queryset})


class UserAdmin(admin.ModelAdmin):
    list_display = ['email', 'first_name', 'last_name', 'is_staff', 'email_verified']
    actions = [reset_user_password]
    search_fields = ['email', 'first_name', 'last_name']
    list_filter = ['is_staff', 'email_verified']


class ContactAdmin(admin.ModelAdmin):
    list_display = ['user', 'city', 'street', 'phone']
    search_fields = ['user__email', 'city', 'phone']
    list_filter = ['city']


class ShopAdmin(admin.ModelAdmin):
    list_display = ['name', 'state']
    list_filter = ['state']
    actions = [activate_shops, deactivate_shops, upload_price_list]

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('upload-price-list/', self.admin_site.admin_view(self.upload_price_list_view),
                 name='shop-upload-price-list'),
        ]
        return custom_urls + urls

    def upload_price_list_view(self, request):
        if request.method == 'POST':
            yaml_file = request.FILES.get('yaml_file')
            if not yaml_file:
                messages.error(request, "No file provided.")
                return redirect('..')

            try:
                # Save to temporary file
                temp_file_path = os.path.join(settings.BASE_DIR, 'temp_price_list.yaml')
                with open(temp_file_path, 'wb') as temp_file:
                    for chunk in yaml_file.chunks():
                        temp_file.write(chunk)

                # Import products
                import_products_from_yaml(temp_file_path)

                messages.success(request, "Price list uploaded successfully.")
            except Exception as e:
                messages.error(request, f"Error uploading price list: {e}")

            return redirect('..')

        return render(request, 'admin/upload_price_list.html', {'title': 'Upload Price List'})


class CategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
    search_fields = ['name']


class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'shop', 'price', 'quantity']
    list_filter = ['category', 'shop']
    search_fields = ['name']


class BasketAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'quantity']
    search_fields = ['user__email', 'product__name']


class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'status', 'created_at']
    list_filter = ['status']
    actions = [mark_orders_as_delivered]


# Register all models
admin.site.register(User, UserAdmin)
admin.site.register(Contact, ContactAdmin)
admin.site.register(Shop, ShopAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Basket, BasketAdmin)
admin.site.register(Order, OrderAdmin)
