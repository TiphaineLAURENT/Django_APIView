from django.db import models
from django.db.models import QuerySet
from django.core.files.base import File
from django.http import HttpRequest
from django.conf import settings

import json
import operator

from .responses import APIResponse, QuerySuccessful, CreationSuccessful, NotFound, NotAllowed, Conflict


class JSONMixin(object):
    """
     Allow a model to be serialized / deserialized.

     json_fields:list[str]
    """

    json_fields = []

    def get_url(self, request:HttpRequest=None) -> str:
        if request is not None:
            return request.build_absolute_uri(f"/{request.get_full_path_info().split('/')[1]}/{self._meta.verbose_name_plural}/{self.id}")
        else:
            return f"/{self._meta.verbose_name_plural}/{self.id}"

    def serialize(self, request:HttpRequest=None) -> dict:
        """
         Serialize the object to a descriptive json

         request:HttpRequest:optional Allow the urls to be created using host and port
        """
        dump = {'id': self.id}
        for field_name in self.json_fields:
            field = getattr(self, field_name)
            if issubclass(field.__class__, models.manager.BaseManager):
                value = [{'id': related.id, 'url': related.get_url(request)} if isinstance(related, JSONMixin) else {'id': related.id}for related in field.all().only('id')]
            elif hasattr(field, 'id'):
                value = {'id': field.id, 'url': field.get_url(request)}
            elif callable(field):
                value = field()
            elif issubclass(field.__class__, File):
                if field:
                    if request is not None:
                        value = request.build_absolute_uri(field.url)
                    else:
                        value = field.url
                else:
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

        data = {'id': id or raw_data.get('id', None)}
        m2m_data = {}

        for field_name, field_value in raw_data.items():
            if field_name not in cls.json_fields:
                continue

            field = cls._meta.get_field(field_name)
            if field.remote_field and field.remote_field.many_to_many:
                m2m_data[field_name] = field_value
            elif field.remote_field and field.remote_field.many_to_one: # separated 1:N from N:1
                if isinstance(field_value[0], dict):
                    values = map(operator.itemgetter('id'), field_value)
                    m2m_data[field_name] = field.remote_field.model.objects.filter(id__in=values)
                else:
                    m2m_data[field_name] = field.remote_field.model.objects.filter(id__in=field_value)
            elif field.remote_field and field.remote_field.one_to_many and not field_name.endswith("_id"):
                data[f"{field_name}_id"] = field_value
            else:
                data[field_name] = field_value

        queryset = cls.objects.filter(id=id)
        if queryset.count():
            queryset.update(**data)
            obj = queryset.first()
        else:
            if save:
                obj = cls.objects.create(**data)
            else:
                obj = cls(**data)
        if save:
            for m2m_name, m2m_list in m2m_data.items():
                if isinstance(m2m_list[0], dict):
                    field = getattr(obj, m2m_name)
                    field.set(map(operator.itemgetter('id'), m2m_list))
                else:
                    getattr(obj, m2m_name).set(m2m_list)
            obj.save()
        return obj
