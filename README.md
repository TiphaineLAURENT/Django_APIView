# Django_APIView

Implement a base generic view for handling model RESTful endpoints

## Usage

```py
# models.py

from django.db import models

from django_modelapiview import JSONMixin

class MyModel(JSONMixin, models.Model):
    """
    Declare your model as you usually do but
    add a json_fields list
    """

    json_fields:list[str] = ['text', 'image', 'fk', 'fk_reverse', 'm2m', 'my_method']

    text = models.TextField()
    image = models.ImageField()

    fk = models.ForeignKey(...)
    # fk_reverse
    m2m = models.ManyToManyField(...)

    def my_method(self):
        return "my custom value"
```

```py
# views.py

from django_modelapiview import APIView
from django_modelapiview.responses import APIResponse

from .models import MyModel

class MyView(APIView):
    # Required
    route:str = "myroute" # The url to access your view

    # Optional
    enforce_authentification:bool = True # Should this model be restricted with Token access
    def get(self, request, *args, **kwargs) -> APIResponse:... # One of head, options, get...
```

```py
# views.py

from django_modelapiview import ModelAPIView

from .models import MyModel

class MyModelView(ModelAPIView):
    # Required
    model:JSONMixin = MyModel # Your model
    route:str = "mymodels" # The url to access your collection

    # Optional
    queryset:QuerySet = MyModel.objects.all() # A custom base queryset (will be affected by query filters)
    singular_name:str = "my model" # Singular name of your model for reason message
    plural_name:str = "my models" # Plural name of your model for reason message
    enforce_authentification:bool = True # Should this model be restricted with Token access
    query_parameters:list[tuple[str, Callable[[QuerySet, object], QuerySet]]] = [
        ('order_by', lambda queryset, field_names: queryset.order_by(*field_names.split(",")) if field_names else queryset),
        ('limit', lambda queryset, limit: queryset[:int(limit)] if limit else queryset), # Should be last since sliced QuerySet can't be filtered anymore
    ]
    def get(self, request, *args, **kwargs) -> APIResponse:... # One of head, options, get...
```

```py
# urls.py

from django.urls import path, include

from . import views

urlpatterns = [
    path("", include("django_routeview")), # Django RouteView are used as based class for APIView in order to automatically register them
]
```

```sh
# You can use query parameters like order_by or limit (or customs):
https://myhost.com/api/mymodel/?order_by=-id&limit=1 # Will inverse order by id and limit to one : get the last id

# Or you can use Django defined filters:
https://myhost.com/api/mymodel/?id__in=1,2,3&foreignkey__id__in=2,3&field__lte=5

# And finally both:
https://myhost.com/api/mymodel/?manytomany__in=2,3&field__lte=5&limit=10
```

It also supports translation:

First enable it as an app
```py
#settings.py

INSTALLED_APPS = [
    ...
    'django_modelapiview',
    ...
]
```

Then change the language using GET parameters:
```sh
#Currently supports : enlish(en)(default), français(fr)
https://myhost.com/api/mymodel/?lang=fr
```

## Using base views

Django ModelAPIView provides 2 base views:
* LoginView: to handle authentification (using the default Django authentification system)
* URLsView: to list the urls availables

### Usage

```py
# urls.py

from django.urls import path

from django_modelapiview.views import LoginView, URLsView # Importing them is enough
```

## Errors

If you get a "Verb not implemented" reason from your endpoint but you are sure to have defined it.
You probable just forgot the `-> APIResponse` return type hint.
