from typing import Callable, Any
from flask import Response, request, abort
import functools


def check_auth(username: str, password: str) -> bool:
    """This function is called to check if a username /
    password combination is valid.
    """
    return username == 'alexapeople' and password == 'givemeaccesstostuff'


def authenticate() -> Response:
    """Sends a 401 response that enables basic auth"""
    return Response(
        'Could not verify your access level for that URL.\n'
        'You have to login with proper credentials', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'})


def requires_auth(f: Callable) -> Callable:
    @functools.wraps(f)
    def decorated(*args, **kwargs) -> Any:
        auth = request.authorization
        with open('ip_addresses.txt') as fil:
            ip_addresses = [x.strip() for x in fil.readlines()]
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        if request.headers.get('X-Nginx-Real-IP', request.remote_addr) not in ip_addresses:
            abort(404)
        return f(*args, **kwargs)
    return decorated
