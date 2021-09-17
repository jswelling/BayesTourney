"""
Moved to a separate file because importing settings requires activating
the database
"""

ALLOWED_SETTINGS = {"hr_graph_style": ["hr_graph_style_box",
                                       "hr_graph_style_violin"],
                    "hr_draws_rule": ["hr_draws_rule_ignore",
                                      "hr_draws_rule_win",
                                      "hr_draws_rule_loss"],
                    "hr_graph_yscale": ["hr_graph_yscale_linear",
                                        "hr_graph_yscale_log"]
                    }


DEFAULT_SETTINGS = {"hr_graph_style": "hr_graph_style_box",
                    "hr_draws_rule": "hr_draws_rule_ignore",
                    "hr_graph_yscale": "hr_graph_yscale_linear",
                    }


