from rest_framework import serializers
from .models import Users
from django.contrib.auth.models import AbstractUser

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model=Users
        fields=['user_id','username','email','password', "phone_number"]
        extra_kwargs={
            'password':{'write_only':True}
        }


    def create(self,validated_data):
        password=validated_data.pop('password',None)
        instance=self.Meta.model(**validated_data)
        if password is not None:
            instance.set_password(password)
        instance.save()
        return instance
    


# serializers.py
from rest_framework import serializers
from .models import Users, Notificationlogs, Orders, Payment

class NotificationLogsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notificationlogs
        fields = '__all__'

class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Orders
        fields = '__all__'

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'

