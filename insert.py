import os
import random
import django
from faker import Faker

# Set up the Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "food_notification.settings")
django.setup()

from users.models import Users, Notificationpreferences, Address, Restaurants

fake = Faker()


def generate_random_user():
    return {
        "username": fake.user_name(),
        "email": fake.email(),
        "phone_number": fake.phone_number(),
        "password": fake.password(),
    }


def generate_notification_preferences():
    return {
        "sms_enabled": random.choice([True, False]),
        "email_enabled": random.choice([True, False]),
        "created_at": fake.date_time_between(start_date="-1y", end_date="now"),
        "updated_at": fake.date_time_between(start_date="-1y", end_date="now"),
    }


def generate_random_address(user):
    return {
        "user": user,
        "address_line1": fake.street_address(),
        "address_line2": fake.secondary_address(),
        "city": fake.city(),
        "state": fake.state(),
        "zip_code": fake.zipcode(),
        "created_at": fake.date_time_between(start_date="-1y", end_date="now"),
        "updated_at": fake.date_time_between(start_date="-1y", end_date="now"),
    }


def generate_random_restaurant():
    return {
        "name": fake.company(),
        "description": fake.text(max_nb_chars=200),
        "phone_number": fake.phone_number(),
        "address": fake.address(),
        "created_at": fake.date_time_between(start_date="-1y", end_date="now"),
        "updated_at": fake.date_time_between(start_date="-1y", end_date="now"),
    }


def insert_data(num_users=100, num_restaurants=40):
    for _ in range(num_users):
        user_data = generate_random_user()
        user = Users(**user_data)
        user.save()

        notification_prefs = generate_notification_preferences()
        notification = Notificationpreferences(user=user, **notification_prefs)
        notification.save()

        address_data = generate_random_address(user)
        address = Address(**address_data)
        address.save()

    for _ in range(num_restaurants):
        restaurant_data = generate_random_restaurant()
        restaurant = Restaurants(**restaurant_data)
        restaurant.save()


if __name__ == "__main__":
    insert_data()
    print(
        "Inserted 100 users with their notification preferences, addresses, and 40 restaurants."
    )
