from django.views import View
from django.contrib.auth import authenticate, get_user_model
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.urls import get_resolver
from django.utils.translation import gettext as _

from http import HTTPStatus
import json

from . import APIView, Token
from .responses import APIResponse

USER_MODEL = get_user_model()

class LoginView(APIView):
    route = "login"

    def post(self, request, **kwargs) -> APIResponse:
        data = request.body.decode('utf-8')
        json_data = json.loads(data)

        user = authenticate(username=json_data.get(USER_MODEL.USERNAME_FIELD), password=json_data.get('password'))
        if user is not None:
            token = Token({'uid': user.id})
            token.sign()
            return APIResponse(HTTPStatus.OK, _("User logged in"), {'token': str(token), 'user': user.serialize(request)})
        else:
            return APIResponse(HTTPStatus.UNAUTHORIZED, _("Wrong user credentials"))


class URLsView(APIView):
    route = ""

    def get(self, request, **kwargs) -> APIResponse:
        return APIResponse(HTTPStatus.OK, _("URLs available"), sorted(set(view[1] for view in get_resolver(None).reverse_dict.values())))
