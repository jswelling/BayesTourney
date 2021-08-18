#! /usr/bin/env python

from copy import deepcopy
from flask import g

from .database import get_db



ALLOWED_SETTINGS = {"hr_graph_style": ["hr_graph_style_box",
                                       "hr_graph_style_violin"],
                    "hr_draws_rule": ["hr_draws_rule_ignore",
                                      "hr_draws_rule_win",
                                      "hr_draws_rule_loss"],
                    }


DEFAULT_SETTINGS = {"hr_graph_style": "hr_graph_style_box",
                    "hr_draws_rule": "hr_draws_rule_ignore"
                    }


class SettingsError(RuntimeError):
    pass


def get_settings() -> dict:
    """
    A convenient method to get user-specific settings
    """
    if g.user.prefs is None:
        return deepcopy(DEFAULT_SETTINGS)
    else:
        return g.user.prefs


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
    g.user.prefs = settings_copy
    get_db().add(g.user)

    
