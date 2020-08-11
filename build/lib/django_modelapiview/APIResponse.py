from django.http import JsonResponse

from . import http_status_codes

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
     code:int Value of the http code to be sent back
     reason:str String describing the code
     data:dict Dictionnary to be sent as json
    """

    def __init__(self, code:int, reason:str, data:dict={}, *args, **kwargs):
        super().__init__({
            'statuscode': code,
            'reason': reason,
            'data': data
        }, safe=False, status=code, *args, **kwargs)


class NotImplemented(APIResponse):
    """
     Verb not implemented
    """

    def __init__(self, *args, **kwargs):
        super().__init__(http_status_codes.HTTP_501_NOT_IMPLEMENTED, "Verb not implemented", *args, **kwargs)


class ExceptionCaught(APIResponse):
    """
     Exception caught

     exception:Exception The exception object to be sent as json
    """

    def __init__(self, exception:Exception, *args, **kwargs):
        super().__init__(http_status_codes.HTTP_500_INTERNAL_SERVER_ERROR, f"Exception caught: {str(exception)}", *args, **kwargs)


class NotAllowed(APIResponse):
    """
     Verb not allowed

     reason:str Default to "Verb not allowed"
    """

    def __init__(self, reason:str="Verb not allowed", *args, **kwargs):
        super().__init__(http_status_codes.HTTP_405_METHOD_NOT_ALLOWED, reason, *args, **kwargs)


class InvalidToken(APIResponse):
    """
     Invalid token

     reason:str Concatenated with "Invalid token: "
    """

    def __init__(self, reason:str, *args, **kwargs):
        super().__init__(http_status_codes.HTTP_401_UNAUTHORIZED, f"Invalid token: {reason}", *args, **kwargs)


class TokenExpired(InvalidToken):
    """
     Invalid token: Token expired
    """

    def __init__(self, *args, **kwargs):
        super().__init__("Token expired")
