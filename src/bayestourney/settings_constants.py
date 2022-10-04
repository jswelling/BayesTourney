"""
Moved to a separate file because importing settings requires activating
the database
"""

ALLOWED_SETTINGS = {"hr_graph_style": ["hr_graph_style_box",
                                       "hr_graph_style_violin"],
                    "hr_graph_yscale": ["hr_graph_yscale_linear",
                                        "hr_graph_yscale_log"],
                    "bp_wins_rule": ["bp_wins_1_pts",
                                     "bp_wins_2_pts"],
                    "bp_draws_rule": ["bp_draws_0_pts",
                                      "bp_draws_1_pts",
                                      "bp_draws_2_pts"],
                    "bp_losses_rule": ["bp_losses_0_pts",
                                       "bp_losses_1_pts"],
                    "hr_draws_rule": ["hr_draws_rule_ignore",
                                      "hr_draws_rule_win",
                                      "hr_draws_rule_loss"],
                    }


DEFAULT_SETTINGS = {"hr_graph_style": "hr_graph_style_box",
                    "hr_draws_rule": "hr_draws_rule_ignore",
                    "hr_graph_yscale": "hr_graph_yscale_linear",
                    "bp_wins_rule": "bp_wins_2_pts",
                    "bp_draws_rule": "bp_draws_1_pts",
                    "bp_losses_rule": "bp_losses_1_pts",
                    }

SETTINGS_GROUPS = {"hr_group": ["hr_graph_style", "hr_graph_yscale"],
                   "bp_group": ["bp_wins_rule", "bp_draws_rule", "bp_losses_rule"],
                   "tourney_group": ["bp_wins_rule", "bp_losses_rule",
                                     "bp_draws_rule", "hr_draws_rule"],
                   }


