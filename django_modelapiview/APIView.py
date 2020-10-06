from django.db.models import QuerySet
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.urls import path
from django.http import HttpRequest, HttpResponse
from django.core.signing import BadSignature, SignatureExpired
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist

from http import HTTPStatus

from django_routeview import RouteView, urlpatterns

from .responses import APIResponse, QuerySuccessful, CreationSuccessful, NotFound, NotAllowed, Conflict, InvalidToken, MethodNotImplemented
from .JSONMixin import JSONMixin
from .Token import Token
from .decorators import catch_exceptions


class APIView(RouteView):
    """
     Auto registered view on self.route path

     `enforce_authentification:bool:optional` Default to `False`

     `http_method_names:list[str]:optional` Default to `["head", "options", "get", "post", "put", "patch", "delete"]`
    """

    enforce_authentification:bool = False
    http_method_names:list[str] = ["get", "post", "put", "patch", "delete", "head", "options"]

    _permissions_match_table = {
        'GET': "view",
        'PATCH': "change",
        'POST': "add",
        'PUT': "add",
        'DELETE': "delete"
    }

    def _init_properties(self) -> None:
        if self.__name__ == "APIView":
            return

        for cls in self.mro():
            self.http_method_names = [method_name for method_name, method in vars(cls).items() if hasattr(method, '__annotations__') and method_name != "dispatch" and method.__annotations__.get('return') == APIResponse]
            if self.http_method_names:
                break

        if self.name is None:
            self.name = self.__name__

        if self.route is None:
            raise ValueError(f"APIView {self.__name__} requires a user defined route")

    def _add_route_(self) -> None:
        if self.__name__ == "APIView":
            return

        urlpatterns.append(
            path(self.route, self.as_view(), name=self.name)
        )

    @catch_exceptions
    @csrf_exempt
    def dispatch(self, request:HttpRequest, *args, **kwargs) -> APIResponse:
        headers = dict(request.headers)

        if self.enforce_authentification:

            if not 'Authorization' in headers:
                return InvalidToken("Authentification required")

            token = Token(signed_data=headers['Authorization'].split(" ")[1])
            try:
                token.unsign()
            except BadSignature:
                return InvalidToken("Invalid signature")
            except SignatureExpired:
                return InvalidToken("Token expired")

            try:
                user = get_user_model().objects.get(id=token.uid)
            except (KeyError, ObjectDoesNotExist):
                return InvalidToken("Invalid body")

            if not user.has_perm(f'api.{self._permissions_match_table[request.method]}_{self.singular_name}') and not request.path_info.split("?")[0].strip("/").endswith(str(user.id)):
                return NotAllowed()

        return super().dispatch(request, *args, **kwargs)

    def http_method_not_allowed(self, request:HttpRequest, *args, **kwargs):
        return MethodNotImplemented()

    def head(self, request:HttpRequest, *args, **kwargs) -> APIResponse:
        return HttpResponse()

    def options(self, request:HttpRequest, *args, **kwargs) -> APIResponse:
        return APIResponse(HTTPStatus.OK, "Available methods", self.http_method_names)
