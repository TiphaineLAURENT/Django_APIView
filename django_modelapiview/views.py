from django.views import View
from django.contrib.auth import authenticate
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.urls import get_resolver

from http import HTTPStatus
import json

from . import APIView, Token
from .responses import APIResponse

@method_decorator(csrf_exempt, "dispatch")
class LoginView(APIView):
    route = "login"

    def post(self, request, **kwargs) -> APIResponse:
        data = request.body.decode('utf-8')
        json_data = json.loads(data)

        user = authenticate(username=json_data['username'], password=json_data['password'])
        if user is not None:
            token = Token({'uid': user.id})
            token.sign()
            return APIResponse(HTTPStatus.OK, "User logged in", {'token': str(token), 'user': user.serialize(request)})
        else:
            return APIResponse(HTTPStatus.UNAUTHORIZED, "Wrong user credentials")


class URLsView(APIView):
    route = ""

    def get(self, request, **kwargs) -> APIResponse:
        return APIResponse(HTTPStatus.OK, "URLs available", sorted(set(view[1] for view in get_resolver(None).reverse_dict.values())))
