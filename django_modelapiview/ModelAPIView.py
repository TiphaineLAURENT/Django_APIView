from django.db.models import QuerySet
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.urls import path
from django.http import HttpRequest, HttpResponse
from django.core.signing import BadSignature, SignatureExpired
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import gettext as _

from typing import List, Tuple, Callable
from http import HTTPStatus

from django_routeview import urlpatterns

from .APIView import APIView
from .responses import APIResponse, QuerySuccessful, CreationSuccessful, NotFound, NotAllowed, Conflict, InvalidToken
from .JSONMixin import JSONMixin
from .Token import Token
from .decorators import catch_exceptions


class ModelAPIView(APIView):
    """
     Describe the endpoints associated with a model


     `model:JSONMixin|django.db.Model`

     `queryset:django.db.QuerySet:optional` # Default to `model.objects.all()`

     `singular_name:str:optional` # Default to `model._meta.verbose_name or model.__name__`

     `plural_name:str:optional` # Default to `model._meta.verbose_name_plural or f"{model.__name__}s"`

     `query_parameters:list[tuple[str, callable[[QuerySet, object], QuerySet]]]`
     # Default to `('order_by', lambda queryset, field_names: queryset.order_by(*field_names.split(",")) if field_names else queryset),
        ('limit', lambda queryset, limit: queryset[:int(limit)] if limit else queryset)`
    """

    model:JSONMixin = None
    queryset:QuerySet = None
    singular_name:str = None
    plural_name:str = None
    query_parameters:List[Tuple[str, Callable[[QuerySet, object], QuerySet]]] = [
        ('order_by', lambda queryset, field_names: queryset.order_by(*field_names.split(",")) if field_names else queryset),
        ('limit', lambda queryset, limit: queryset[:int(limit)] if limit else queryset),
    ]

    def _init_properties(self) -> None:
        if self.__name__ == "ModelAPIView":
            return

        super()._init_properties(self)

        if self.route is None:
            self.route = self.plural_name or self.model._meta.verbose_name_plural or f"{self.model.__name__}s"

        if self.queryset is None:
            self.queryset = self.model.objects.all()

        if self.singular_name is None:
            self.singular_name = self.model._meta.verbose_name or self.model.__name__

        if self.plural_name is None:
            self.plural_name = self.model._meta.verbose_name_plural or f"{self.model.__name__}s"

        if self.name is None:
            self.name = self.singular_name or self.__name__

    def _add_route_(self) -> None:
        if self.__name__ == "ModelAPIView":
            return

        self.route = f"{self.route.rstrip('/')}/"
        urlpatterns.extend((
            path(self.route, self.as_view(), name=self.name),
            path(f"{self.route}<int:id>", self.as_view(), name=self.name)
        ))

    def _parse_parameters(self, request:HttpRequest, queryset:QuerySet) -> QuerySet:
        get_parameters = request.GET.dict()
        get_parameters.pop('lang', None)

        queries = {query[0]: get_parameters.pop(query[0], None) for query in self.query_parameters}

        for filter_name, filter_value in get_parameters.items():
            if "," in filter_value:
                queryset = queryset.filter((filter_name, filter_value.split(",")))
            else:
                queryset = queryset.filter((filter_name, filter_value))

        for query_name, transform in self.query_parameters:
            queryset = transform(queryset, queries.get(query_name))

        return queryset

    @catch_exceptions
    @csrf_exempt
    def dispatch(self, request:HttpRequest, id:int=None) -> APIResponse:
        queryset = self._parse_parameters(request, self.queryset.filter(id=id) if id else self.queryset)
        return super().dispatch(request, queryset, id)

    def get(self, request:HttpRequest, queryset:QuerySet, id:int=None) -> APIResponse:
        """
         Retrieve specific or collection
        """
        if id:
            if not queryset.exists():
                return NotFound(_("No %(singular_name)s with id %(id)d") % {'singular_name': self.singular_name, 'id': id})
            return QuerySuccessful(_("Retrieved %(singular_name)s") % {'singular_name': self.singular_name}, data=queryset.first().serialize(request))

        # Else if trying to get on collection
        return QuerySuccessful(_("Retrieved %(plural_name)s") % {'plural_name': self.plural_name}, data=[obj.serialize(request) for obj in queryset])

    def patch(self, request:HttpRequest, queryset:QuerySet, id:int=None) -> APIResponse:
        """
         Update specific
        """
        if id:
            if not queryset.exists():
                return NotFound(_("No %(singular_name)s with id %(id)d") % {'singular_name': self.singular_name, 'id': id})
            return QuerySuccessful(_("Updated %(singular_name)s") % {'singular_name': self.singular_name}, self.model.deserialize(request.body.decode("utf-8"), id).serialize(request))

        # Else if trying to patch on collection
        return NotAllowed()

    def put(self, request:HttpRequest, queryset:QuerySet, id:int=None) -> APIResponse:
        """
         Emplace specific
        """
        if id:
            if queryset.exists():
                return Conflict(_("%(id)d already taken") % {'id': id})
            return CreationSuccessful(_("Created %(singular_name)s") % {'singular_name': self.singular_name}, self.model.deserialize(request.body.decode("utf-8"), id).serialize(request))

        # Else if trying to put on collection
        return NotAllowed(_("You are trying to emplace on a collection. Instead use POST to create or use an id"))

    def delete(self, request:HttpRequest, queryset:QuerySet, id:int=None) -> APIResponse:
        """
         Delete specific
        """
        if id:
            if not queryset.exists():
                return NotFound(_("No %(singular_name)s with id %(id)d") % {'singular_name': self.singular_name, 'id': id})
            obj_serialized = queryset.first().serialize(request)
            queryset.delete()
            return QuerySuccessful(_("Deleted %(singular_name)s") % {'singular_name': self.singular_name}, obj_serialized)

        # Else if trying to delete on collection
        return NotAllowed()

    def post(self, request:HttpRequest, queryset:QuerySet, id:int=None) -> APIResponse:
        """
         Create specific in collection
        """
        if id:
            return NotAllowed(_("You are trying to create at a specific id. Instead use PUT to emplace or use no id"))

        # Else if trying to post on collection
        return CreationSuccessful(_("Created %(singular_name)s") % {'singular_name': self.singular_name}, self.model.deserialize(request.body.decode("utf-8"), id).serialize(request))
