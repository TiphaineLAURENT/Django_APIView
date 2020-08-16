from django.http import JsonResponse

from http import HTTPStatus

class CORSResponse(JsonResponse):
    """
     CORS support for JSONResponse
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self['Access-Control-Allow-Origin'] = '*'
        self['Access-Control-Allow-Headers'] = 'Origin, X-Requested-With, Content-Type, Accept'


class APIResponse(CORSResponse):
    """
     `code:int` Value of the http code to be sent back
     `reason:str` String describing the code
     `data:dict` Dictionnary to be sent as json
    """

    def __init__(self, code:int, reason:str, data={}, *args, **kwargs):
        super().__init__({
            'statuscode': code,
            'reason': reason,
            'data': data
        }, safe=False, status=code, *args, **kwargs)


class QuerySuccessful(APIResponse):
    """
     Query on requested data has been successful

     `reason:str` String describing the code
     `data:dict` Dictionnary to be sent as json
    """

    def __init__(self, reason:str, data={}, **kwargs):
        super().__init__(HTTPStatus.OK, reason, data=data, **kwargs)


class CreationSuccessful(APIResponse):
    """
     Creation of requested data has been successful

     `reason:str` String describing the code
     `data:dict` Dictionnary to be sent as json
    """

    def __init__(self, reason:str, data={}, **kwargs):
        super().__init__(HTTPStatus.CREATED, reason, data=data, **kwargs)


class NotFound(APIResponse):
    """
     Requested data not found

     `reason:str` String describing the code
    """

    def __init__(self, reason:str, **kwargs):
        super().__init__(HTTPStatus.NOT_FOUND, reason, **kwargs)


class NotImplemented(APIResponse):
    """
     Verb not implemented
    """

    def __init__(self, **kwargs):
        super().__init__(HTTPStatus.NOT_IMPLEMENTED, "Verb not implemented", **kwargs)


class ExceptionCaught(APIResponse):
    """
     Exception caught

     `exception:Exception` The exception object to be sent as json
    """

    def __init__(self, exception:Exception, **kwargs):
        super().__init__(HTTPStatus.INTERNAL_SERVER_ERROR, f"Exception caught: {str(exception)}", **kwargs)


class Conflict(APIResponse):
    """
     Item already exist

     `reason:str`
    """

    def __init__(self, reason:str, **kwargs):
        super().__init__(HTTPStatus.CONFLICT, reason, **kwargs)


class NotAllowed(APIResponse):
    """
     Verb not allowed

     `reason:str` Default to "Verb not allowed"
    """

    def __init__(self, reason:str="Verb not allowed", **kwargs):
        super().__init__(HTTPStatus.METHOD_NOT_ALLOWED, reason, **kwargs)


class InvalidToken(APIResponse):
    """
     Invalid token

     `reason:str` Prefixed by "Invalid token: "
    """

    def __init__(self, reason:str, **kwargs):
        super().__init__(HTTPStatus.UNAUTHORIZED, f"Invalid token: {reason}", **kwargs)
