from celery import shared_task
import time


# @shared_task
# def handle_sleep(name="Sakshi"):
#     print("Sleeping for 10 seconds")
#     # Sleeps for a while to simulate some work.
#     print(name)
#     with open("abc.txt","w") as file:
#         file.write(f'Hello {name}')





#from celery import shared_task
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

@shared_task
def send_notification(message):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)('notifications', {'type': 'notification.message', 'message': message})
