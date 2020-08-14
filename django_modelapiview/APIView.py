from django.db import models
from django.db.models import QuerySet
from django.core.files.base import File
from django.views.decorators.csrf import csrf_exempt
from django.urls import path
from django.http import HttpRequest

import json

from typing import Any, List
from http import HTTPStatus

from django_routeview import RouteView, urlpatterns

from .APIResponse import APIResponse, QuerySuccessful, CreationSuccessful, NotFound, NotAllowed, Conflict


class JSONMixin(object):
    """
     Allow a model to be serialized / deserialized.
    """

    json_fields:List[str] = []

    def get_url(self, request:HttpRequest=None) -> str:
        if request is not None:
            return request.build_absolute_uri(f"{self._meta.verbose_name_plural}/{self.id}")
        else:
            return f"{self._meta.verbose_name_plural}/{self.id}"

    def serialize(self, request:HttpRequest=None) -> dict:
        """
         Serialize the object to a descriptive json

         request:HttpRequest:optional Allow the urls to be created using host and port
        """
        dump = {'id': self.id}
        for field_name in self.json_fields:
            field:models.Field = getattr(self, field_name)
            if issubclass(field.__class__, models.manager.BaseManager):
                value = [{'id': related.id, 'url': related.get_url(request)} for related in field.all().only('id')]
            elif hasattr(field, 'id'):
                value = {'id': field.id, 'url': field.get_url(request)}
            elif callable(field):
                value = field()
            elif issubclass(field.__class__, File):
                if field:
                    if request is not None:
                        print(f"build_absolute_uri({request.build_absolute_uri(field.url)}) from url({field.url})")
                        value = request.build_absolute_uri(field.url)
                    else:
                        print(f"url({field.url})")
                        value = field.url
                else:
                    print("default")
                    value = ""
            else:
                value = field
            dump[field_name] = value
        dump['url'] = self.get_url(request)
        return dump

    @classmethod
    def deserialize(cls, serialized_data:str, id:int=None, save:bool=True) -> dict:
        """
         Deserialize a string to type cls

         serialized_data:str
         id:int:optional       Does the deserialized object already have an id in the bdd
         save:boolean:optional Should the deserialized object be saved
        """
        raw_data = json.loads(serialized_data)

        data = {}
        if id:
            data['id'] = id
        elif raw_data['id']:
            data['id'] = raw_data['id']
        m2m_data = {}

        for (field_name, field_value) in raw_data.items():
            if field_name not in cls.json_fields:
                continue

            field = cls._meta.get_field(field_name)
            if field.remote_field and isinstance(field.remote_field, models.ManyToManyRel):
                m2m_data[field_name] = field_value
            else:
                data[field_name] = field_value
        
        queryset = cls.objects.filter(id=id)
        if queryset.count():
            queryset.update(**data)
            obj = queryset.first()
        else:
            obj = cls(**data)
        if save:
            obj.save()
            for (m2m_name, m2m_list) in m2m_data.items():
                for m2m_value in m2m_list:
                    getattr(obj, m2m_name).add(m2m_value['id'])
            obj.save()
        return obj


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
