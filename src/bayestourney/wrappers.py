import functools
import logging
from flask import request

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

    
