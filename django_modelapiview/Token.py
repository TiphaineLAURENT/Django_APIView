from django.core import signing

from datetime import timedelta

class Token(object):
    """
     Represent a token used when authenticating a request toward an APIView with authentification set to True
    """

    _max_age = timedelta(hours=2)
    _body = None
    _signed_data = None

    def __init__(self, body:dict):
        self._body = body
        self._sign_data = None

    def __str__(self):
        return self._signed_data if self.is_signed() else str(self._body)

    def __repr__(self):
        return f"<Token id({id(self)}): {'S' if self.is_signed() else 'Not s'}igned>"

    def sign(self) -> None:
        self._signed_data = signing.dumps(self._body)

    def unsign(self) -> None:
        self._body = signing.loads(self._signed_data, max_age=self._max_age)

    def is_signed(self):
        return self._sign_data is not None

    def is_unsigned(self):
        return self._body is not None
