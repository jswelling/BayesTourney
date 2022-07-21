#! /usr/bin/env python

from copy import deepcopy
from flask_login import current_user

from .database import get_db

from .settings_constants import ALLOWED_SETTINGS, DEFAULT_SETTINGS


class SettingsError(RuntimeError):
    pass


def get_settings() -> dict:
    """
    A convenient method to get user-specific settings
    """
    rslt = deepcopy(DEFAULT_SETTINGS)
    if current_user.prefs is not None:
        rslt.update(current_user.prefs)
    return rslt


def set_settings(key: str, value: str):
    """
    A convenience method for updating settings.
    """
    if key not in ALLOWED_SETTINGS:
        raise SettingsError(f"Invalid setting key {key}")
    if value not in ALLOWED_SETTINGS[key]:
        raise SettingsError(f"Value {value} is invalid for setting {key}")
    settings_copy = deepcopy(get_settings())
    settings_copy[key] = value
    current_user.prefs = settings_copy
    get_db().add(current_user)

    
