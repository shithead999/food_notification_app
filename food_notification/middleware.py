"""
File in which we have the middleware for Django for Authenticating API requests
"""
import json
import jwt
import logging
from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin
from users.models import Users
from django.shortcuts import redirect
from django.urls import resolve
from django.conf import settings

# Initialize logger
logger = logging.getLogger(__name__)


def create_response(request_id, code, message):
    """
    Function to create a response to be sent back via the API
    :param request_id:Id fo the request
    :param code:Error Code to be used
    :param message:Message to be sent via the APi
    :return:Dict with the above given params
    """

    try:
        req = str(request_id)
        data = {"data": message, "code": int(code), "request_id": req}
        return data
    except Exception as creation_error:
        logger.error(f"create_response:{creation_error}")


class CustomMiddleware(MiddlewareMixin):

    """
    Custom Middleware Class to process a request before it reached the endpoint
    """

    def process_request(self, request):
        """
        Custom middleware handler to check authentication for a user with JWT authentication
        :param request: Request header containing authorization tokens
        :type request: Django Request Object
        :return: HTTP Response if authorization fails, else None
        """
        mat = resolve(request.path)
        if mat.url_name in settings.EXCLUDED_PATH_FROM_AUTH_MIDDLEWARE:
            return None
        jwt_token = request.COOKIES.get("jwt", None)
        logger.info(f"request received for endpoint {str(request.path)}")

        # If token Exists
        if jwt_token:
            try:
                payload = jwt.decode(jwt_token, "secrets", algorithms=["HS256"])
                userid = payload["user_id"]
                user = Users.objects.filter(user_id=payload["user_id"]).first()
                request.user = user
                logger.info(f"Request received from user - {userid}")
                return None
            except:
                return redirect("login")
        else:
            return redirect("login")
