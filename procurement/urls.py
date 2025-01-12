from django.urls import path
from .views import (
    UserRegisterView, EmailVerificationView, UserLoginView,
    PasswordResetView, PasswordResetConfirmView, UserEditView,
    ContactListView, ContactDetailView, ShopListView,
    CategoryListView, ProductListView, BasketView,
    OrderListView, PartnerUpdateView, PartnerStateView,
    PartnerOrdersView
)

urlpatterns = [
    # User Endpoints
    path('user/register', UserRegisterView.as_view(), name='user-register'),
    path('user/register/confirm', EmailVerificationView.as_view(), name='email-verification'),
    path('user/login', UserLoginView.as_view(), name='user-login'),
    path('user/password_reset', PasswordResetView.as_view(), name='password-reset'),
    path('user/password_reset/confirm', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    path('user/details', UserEditView.as_view(), name='user-edit'),
    path('user/contact', ContactListView.as_view(), name='contact-list'),
    path('user/contact/<int:pk>/', ContactDetailView.as_view(), name='contact-detail'),

    # Shop Endpoints
    path('shops', ShopListView.as_view(), name='shop-list'),
    path('categories', CategoryListView.as_view(), name='category-list'),
    path('products', ProductListView.as_view(), name='product-list'),

    # Basket Endpoints
    path('basket', BasketView.as_view(), name='basket'),

    # Order Endpoints
    path('order', OrderListView.as_view(), name='order'),

    # Partner Endpoints
    path('partner/update', PartnerUpdateView.as_view(), name='partner-update'),
    path('partner/state', PartnerStateView.as_view(), name='partner-state'),
    path('partner/orders', PartnerOrdersView.as_view(), name='partner-orders'),
]
