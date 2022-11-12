import functools
import logging
from flask import request, current_app
from flask_login import current_user
from flask_login.config import EXEMPT_METHODS

logging.basicConfig()
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)


def debug_wrapper(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        LOGGER.debug(f'{request.method} Request for {request.endpoint}'
                     f' kwargs {kwargs}'
                     f' params {[(k,request.values[k]) for k in request.values]}')
        rslt = view(**kwargs)
        LOGGER.debug(f'Returning {rslt}')
        return rslt
    return wrapped_view

    
def debug_page_wrapper(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        LOGGER.debug(f'{request.method} Request for {request.endpoint}'
                     f' kwargs {kwargs}'
                     f' params {[(k,request.values[k]) for k in request.values]}'
        )
        #print('session state before view follows:')
        #pprint(session)
        rslt = view(**kwargs)
        #print('session follows:')
        #pprint(session)
        return rslt
    return wrapped_view

    
def admin_login_required(view):
    """
    Require that the current user have Admin privilege before calling the wrapped
    view.  If not, 
    """
    @functools.wraps(view)
    def wrapped_view(*args, **kwargs):
        if (request.method in EXEMPT_METHODS
            or current_app.config.get("LOGIN_DISABLED")):
            pass
        elif not current_user.is_admin():
            return 'Not an admin', 403
        return view(*args, **kwargs)
    return wrapped_view
