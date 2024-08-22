from django.urls import path
from . import views
from .views import (
    Register,
    LoginView,
    # UserView,
    LogoutView,
    notification_logs_list,
)

urlpatterns = [
    path("register/", Register.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    # path("user/", UserView.as_view()),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("notification/", notification_logs_list, name="notification"),
    path(
        "update-payment-status/",
        views.update_payment_status,
        name="update-payment-status",
    ),
    path("orders/create/", views.create_order, name="create-order"),
    path("sendmail/", views.send_mail_to_all, name="sendmail"),
    path("orders/", views.order_list, name="order-list"),
    path("payments/", views.payment_list, name="payment-list"),
    # path("login_page/", views.login_view, name="login"),
    # path("register_page/", views.register_view, name="register"),
   path("dashboard/", views.dashboard_view, name="dashboard"),
   path("homepage/", views.homepage, name="homepage"),

   path('restaurants/', views.restaurant_list, name='restaurant_list'),
   path('restaurants/<int:restaurant_id>/', views.restaurant_menu, name='restaurant_menu'),
   path('add-to-cart/<int:menu_item_id>/', views.add_to_cart, name='add_to_cart'),
   path('cart/', views.cart, name='cart'),
]
