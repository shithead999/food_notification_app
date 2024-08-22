from django.views import View
from .serializers import UserSerializer
import jwt, datetime
from django.shortcuts import redirect, render
from django.http import HttpResponse
from .models import (
    Notificationlogs,
    Orders,
    Payment,
    Users,
    Restaurants,
    Notificationpreferences,
    Events,
    Menu,
    Cart,
    CartItem
)
from .task import *
from django.views.decorators.csrf import csrf_exempt
from send_mail_app.tasks import send_mail_func
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.core.serializers import serialize
import json


def send_notification(user, new_log, event):
    log_s = serialize("json", [new_log, event])

    group_name = user.group_name
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            "type": "send.log",
            "log_data": log_s,
        },
    )

def update_notification_to_read(user):
    group_name = user.group_name
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            "type": "send.message",
            "action": json.dumps({"message": "read_notification"}),
        },
    )

def send_notification_payment(user, new_log, event):
    log_s = serialize("json", [new_log, event])

    group_name = user.group_name
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            "type": "send.log",
            "log_data": log_s,
        },
    )


class Register(View):
    def post(self, request):
        serializer = UserSerializer(data=request.POST)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        noti = request.POST.getlist("notification_preference")
        pref = Notificationpreferences(
            user_id=user.user_id,
            sms_enabled="sms_enabled" in noti,
            email_enabled="email_enabled" in noti,
        )
        pref.save()
        return redirect("login")

    def get(self, request):
        return render(request, "register/register.html")


class LoginView(View):
    def post(self, request):
        email = request.POST.get("email")
        password = request.POST.get("password")

        user = Users.objects.filter(email=email).first()

        if user is None:
            raise ValueError("User not found!")

        if not user.check_password(password):
            raise ValueError("Password doesn't match!")

        payload = {
            "user_id": user.user_id,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=1440),
            "iat": datetime.datetime.utcnow(),  # intiated at
        }

        token = jwt.encode(payload, "secrets", algorithm="HS256")

        response = redirect("homepage")
        response.set_cookie(key="jwt", value=token, httponly=True)
        # response.data = {"jwt": token}

        return response

    def get(self, request):
        return render(request, "login/login.html")


class LogoutView(View):
    def get(self, request):
        response = redirect("homepage")
        response.delete_cookie("jwt")
        # response.data = {"message": "Logged Out!"}
        return response


def homepage(request):
    user = request.user

    notification_count = Notificationlogs.objects.filter(user=user, read_status='unread').count()

    context = {
        'User': user,
        'notification_count': notification_count,
    }

    return render(request, "homepage/homepage.html", context=context)

def notification_logs_list(request):

    notification_logs = (
        Notificationlogs.objects.filter(user_id=request.user.user_id)
        .select_related("event")
        .order_by("-created_at")[:10]
    )

    Notificationlogs.objects.filter(user_id=request.user.user_id, read_status="unread").update(read_status="read")
    update_notification_to_read(request.user)
    return render(
        request,
        "notification/notification.html",
        {"notification_logs": notification_logs},
    )


def order_list(request):
    orders = Orders.objects.filter(user_id=request.user.user_id).order_by(
        "-created_at"
    )[:10]
    return render(request, "orders/orders_list.html", {"orders": orders})


def payment_list(request):
    payments = Payment.objects.filter(order__user_id=request.user.user_id).order_by(
        "-created_at"
    )[:10]
    return render(request, "payments/payments_list.html", {"payments": payments})

 
def update_payment_status(request):
    payment_id = request.POST.get("payment_id")
    new_status = request.POST.get("payment_status")
    status_to_event_id = {
        "successful": 4,
        "failed": 5,
        
    }

    payment = Payment.objects.get(payment_id=payment_id)
    payment.payment_status = new_status
    payment.save()

    pref = Notificationpreferences.objects.get(user=request.user.user_id)
    not_type = "none"
    if pref.sms_enabled and pref.email_enabled:
        not_type = "S & E"
    elif pref.email_enabled:
        not_type = "email"
    elif pref.sms_enabled:
        not_type = "sms"


    event = Events.objects.get(event_id=status_to_event_id[new_status.strip().lower()])
    not_log = Notificationlogs(
        user=request.user,
        event_id=event.event_id,  
        notification_type=not_type,
    )
    not_log.save()
    send_notification(request.user, not_log, event)

    
    rest = Restaurants.objects.get(restaurant_id=payment.order.restaurant_id)
    payment_amount = payment.payment_amount
    payment_status = payment.payment_status

    if rest:
        message = f"Your payment of {payment_amount} amount for {rest.name} is successfully {payment_status}."
    else:
        message = (
            f"Your Payment of { payment_amount} amount is successfully {payment_status}."
        )

    send_mail_func.delay(
        request.user.user_id,
        message,
    )

    return redirect("payment-list")


def create_order(request):
    user = request.user.user_id
    total_amount = request.POST.get("total_amount")
    restaurant_id = request.POST.get("restaurant_id")
    status = request.POST.get("status")
    order_id = request.POST.get("order_id")

    status_to_event_id = {
        "placed": 1,
        "cancelled": 3,
        "delivered": 2,
    }

    if status == "placed":
        order = Orders(
            user_id=user,
            total_amount=total_amount,
            restaurant_id=int(restaurant_id),
            status=status,
        )
        order.save()

        #TODO: delete the card for request.user
        user_cart = Cart.objects.filter(user=request.user)
        if user_cart:
            user_cart.delete()

    else:
        order = Orders.objects.get(order_id=int(order_id))
        order.status = status
        order.save()
    

    pref = Notificationpreferences.objects.get(user=request.user.user_id)
    not_type = "none"
    if pref.sms_enabled and pref.email_enabled:
        not_type = "S & E"
    elif pref.email_enabled:
        not_type = "email"
    elif pref.sms_enabled:
        not_type = "sms"

    event = Events.objects.get(event_id=status_to_event_id[status.strip().lower()])
    not_log = Notificationlogs(
        user=request.user,
        event_id=event.event_id, 
        notification_type=not_type,
    )
    not_log.save()
    send_notification(request.user, not_log, event)

    payment = Payment(
        order=order, payment_amount=order.total_amount, payment_status="successful" if order.status=="delivered" else "pending" 
    )
    payment.save()

    message = f"""
    Your Order #{order.order_id}
    Amount: {order.total_amount}
    from {order.restaurant.name} is {order.status}
    """

    send_mail_func.delay(
        user,
        message,
    )

    return redirect("order-list")


def dashboard_view(request):
    return render(request, "dashboard/dashboard.html")


def send_mail_to_all(request):
    send_mail_func.delay()
    return HttpResponse("Sent")


def index(request):
    return render(request, "index/index.html")


def restaurant_list(request):
    restaurants = Restaurants.objects.all()
    return render(request, 'restaurants/restaurant_list.html', {'restaurants': restaurants})


def restaurant_menu(request, restaurant_id):
    restaurant = Restaurants.objects.get(pk=restaurant_id)
    menu_items = Menu.objects.filter(restaurant=restaurant)
    return render(request, 'restaurants/restaurant_menu.html', {'restaurant': restaurant, 'menu_items': menu_items})


def add_to_cart(request, menu_item_id):
    if request.method == 'POST':
        menu_item = Menu.objects.get(pk=int(menu_item_id))
        cart, created = Cart.objects.get_or_create(user=request.user)

        items = CartItem.objects.filter(cart=cart)
        if items and menu_item.restaurant != items.first().menu_item.restaurant:
            cart = Cart.objects.get(user=request.user)
            if cart:
                context = _get_cart_context(cart=cart)
                context["error"] = "Cannot add items from different restaurants, first do checkout."
                return render(request, 'cart/cart.html', context)
            return render(request, 'cart/cart.html', {'cart_items': [], 'total_items': 0, 'total_amount': 0})
            
        cart_item, item_created = CartItem.objects.get_or_create(cart=cart, menu_item=menu_item)
        if item_created:
            cart_item.quantity = 1
        else:
            cart_item.quantity += 1
        
        cart_item.save()

        return redirect('cart')
    return redirect('restaurant_list')


def _get_cart_context(cart):
    cart_items = CartItem.objects.filter(cart=cart)
    total_items = cart_items.count()
    total_amount = sum(item.menu_item.price * item.quantity for item in cart_items) 
    return {'cart_items': cart_items, 'total_items': total_items, 'total_amount': total_amount}


def cart(request):
    cart = Cart.objects.filter(user=request.user).first()
    

    if cart:
        context = _get_cart_context(cart=cart)
        return render(request, 'cart/cart.html', context)
    
    return render(request, 'cart/cart.html', {'cart_items': [], 'total_items': 0, 'total_amount': 0})
