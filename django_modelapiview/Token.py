from django.core import signing

from datetime import timedelta


class StillSigned(ValueError):

    def __init__(self):
        super().__init__("Token still signed")


class Token(object):
    """
     Represent a token used when authenticating a request toward an APIView with authentification set to True
    """

    _max_age = timedelta(hours=2)
    _body = None
    _signed_data = None

    def __init__(self, body:dict=None, signed_data:str=None):
        self._body = body
        self._signed_data = signed_data

    def __str__(self) -> str:
        return self._signed_data if self.is_signed() else str(self._body)

    def __repr__(self) -> str:
        return f"<Token id({id(self)}): {'S' if self.is_signed() else 'Not s'}igned>"

    def sign(self) -> None:
        self._signed_data = signing.dumps(self._body)

    def unsign(self) -> None:
        self._body = signing.loads(self._signed_data, max_age=self._max_age)

    def is_signed(self) -> bool:
        return self._signed_data is not None

    def is_unsigned(self) -> bool:
        return self._body is not None

    @property
    def uid(self):
        if not self.is_unsigned():
            raise StillSigned
        return self._body['uid']
