from django.db.models import QuerySet
from django.views.decorators.csrf import csrf_exempt
from django.urls import path
from django.http import HttpRequest

from typing import List
from http import HTTPStatus

from django_routeview import RouteView, urlpatterns

from .responses import APIResponse, QuerySuccessful, CreationSuccessful, NotFound, NotAllowed, Conflict
from .JSONMixin import JSONMixin


class APIView(RouteView):
    """
     Auto registered view on self.route path
     Describe the endpoints associated with a model
    """

    model:JSONMixin = None
    queryset:QuerySet = None
    singular_name:str = None
    plural_name:str = None
    authentification:bool = False
    http_method_names:List[str] = ["get", "post", "put", "patch", "delete", "head", "options"]

    def _add_route_(self) -> None:
        if self.route is not None:
            if self.name is None:
                self.name = self.__name__
            if self.route is None:
                self.route = self.plural_name or self.model._meta.verbose_name_plural or f"{self.model.__name__}s"

            if not self.route.endswith("/"):
                urlpatterns.append(path(f"{self.route}/", self.as_view(), name=self.name))
                urlpatterns.append(path(f"{self.route}/<int:id>", self.as_view(), name=self.name))
            else:
                urlpatterns.append(path(self.route, self.as_view(), name=self.name))
                urlpatterns.append(path(f"{self.route}<int:id>", self.as_view(), name=self.name))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.queryset is None:
            self.queryset = self.model.objects.all()

        if self.singular_name is None:
            self.singular_name = self.model._meta.verbose_name or self.model.__name__

        if self.plural_name is None:
            self.plural_name = self.model._meta.verbose_name_plural or f"{self.model.__name__}s"

    @csrf_exempt
    def dispatch(self, *args, **kwargs) -> APIResponse:
        return super().dispatch(*args, **kwargs)

    def get(self, request:HttpRequest, id:int=None, *args, **kwargs) -> APIResponse:
        """
         Retrieve specific or collection
        """
        if id:
            queryset = self.queryset.filter(id=id)
            if queryset.count() == 0:
                return NotFound(f"No {self.singular_name} with id {id}")
            return QuerySuccessful(f"Retrieved {self.singular_name}", data=queryset.first().serialize(request))

        # Else if trying to get on collection
        return QuerySuccessful(f"Retrieved {self.plural_name}", data=[obj.serialize(request) for obj in self.queryset])

    def patch(self, request:HttpRequest, id:int=None, *args, **kwargs) -> APIResponse:
        """
         Update specific
        """
        if id:
            if self.queryset.filter(id=id).count() == 0:
                return NotFound(f"No {self.singular_name} with id {id}")
            return QuerySuccessful(f"Updated {self.singular_name}", self.model.deserialize(request.body.decode("utf-8"), id).serialize(request))

        # Else if trying to patch on collection
        return NotAllowed()

    def put(self, request:HttpRequest, id:int=None, *args, **kwargs) -> APIResponse:
        """
         Emplace specific
        """
        if id:
            if self.queryset.filter(id=id).count() != 0:
                return Conflict(f"{id} already taken")
            return CreationSuccessful(f"Created {self.singular_name}", self.model.deserialize(request.body.decode("utf-8"), id).serialize(request))

        # Else if trying to put on collection
        return NotAllowed("You are trying to emplace on a collection. Instead use POST to create or use an id")

    def delete(self, request:HttpRequest, id:int=None, *args, **kwargs) -> APIResponse:
        """
         Delete specific
        """
        if id:
            queryset = self.queryset.filter(id=id)
            if queryset.count() == 0:
                return NotFound(f"No {self.singular_name} with id {id}")
            obj_serialized = queryset.first().serialize(request)
            queryset.delete()
            return QuerySuccessful(f"Deleted {self.singular_name}", obj_serialized)

        # Else if trying to delete on collection
        return NotAllowed()

    def post(self, request:HttpRequest, id:int=None, *args, **kwargs) -> APIResponse:
        """
         Create specific in collection
        """
        if id:
            return NotAllowed("You are trying to create at a specific id. Instead use PUT to emplace or use no id")

        # Else if trying to post on collection
        return CreationSuccessful(f"Created {self.singular_name}", self.model.deserialize(request.body.decode("utf-8"), id).serialize(request))
