from functools import wraps

from .responses import APIResponse, ExceptionCaught

def catch_exceptions(view_function) -> APIResponse:
    """
     Catch exceptions and return them as a valid APIResponse
    """
    def wrapped_view(*args, **kwargs):
        try:
            return view_function(*args, **kwargs)
        except Exception as e:
            return ExceptionCaught(e)
    return wraps(view_function)(wrapped_view)
