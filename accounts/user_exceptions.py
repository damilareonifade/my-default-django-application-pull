from django.db import IntegrityError
from django.http import Http404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    if isinstance(exc, IntegrityError):
        response_data = {
            'error': 'This email is already registered.'
        }
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    return exception_handler(exc, context)


def http_404_exception_handler(exc,context):
    if isinstance(exc,Http404):
        response_data = {
            "error":"This Object is not Found"
        }
        return Response(response_data,status=status.HTTP_404_NOT_FOUND)
    
    return exception_handler(exc,context)
