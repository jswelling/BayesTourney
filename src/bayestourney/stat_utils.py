#! /usr/bin/env python

import logging
from io import StringIO
from os import unlink
from tempfile import TemporaryFile

import numpy as np
import pandas as pd
import pygraphviz as pgv
import matplotlib.pyplot as plt

from .settings_constants import ALLOWED_SETTINGS

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)

"""Number of sweeps used in Metropolis burn-in"""
BURNIN_SWEEPS = 300
#BURNIN_SWEEPS = 0

"""Number of Metropolis samples to generate, per chain"""
#N_SAMP = 500
N_SAMP = 20

"""Number of sweeps between samples, to minimize correlation"""
SWEEPS_PER_SAMP = 100
#SWEEPS_PER_SAMP = 1

"""Number of independent Metropolis Markov Chains run simultaneously per thread"""
N_CHAINS = 20
#N_CHAINS = 1

"""Standard deviation of normal used to generate mutation step sizes"""
MUTATION_SIGMA = 4.0 # works for Iron Comet


def generate_random_bouts(n_players, n_pairs, player_wts):
    outcomes = []
    for pair in range(n_pairs):
        l_player = np.random.choice(range(n_players))
        r_player = np.random.choice(range(n_players-1))
        if r_player >= l_player:
            r_player += 1
        l_prob = player_wts[l_player] / (player_wts[l_player] + player_wts[r_player])
        if np.random.random() <= l_prob:
            outcomes.append({'l_player':l_player, 'r_player':r_player,
                             'l_wins':1, 'r_wins':0})
        else:
            outcomes.append({'l_player':l_player, 'r_player':r_player,
                             'l_wins':0, 'r_wins':1})
    outcomes_df = pd.DataFrame(outcomes)    
    totals_df = outcomes_df.groupby(['l_player','r_player']).sum().reset_index()
    return totals_df


def restructure_df(raw_df, draws_rule=None):
    """
    draws_rule must be one of the hr_draws_rule values supported in settings, or None.
    The effect of counting draws as wins or losses is the same because both players
    must gain either a win or a loss, so the other player must gain either a loss or
    a win.
    """
    if draws_rule is None:
        draws_rule = 'hr_draws_rule_ignore'
    assert draws_rule in ALLOWED_SETTINGS['hr_draws_rule'], f'invalid draws_rule {draws_rule}'
        
    merge_df_a = raw_df.rename(columns={'l_player':'player',
                                        'r_player':'opponent',
                                        'l_wins':'wins',
                                        'r_wins':'losses',
                                        'leftPlayerId':'player',
                                        'rightPlayerId':'opponent',
                                        'leftWins':'wins',
                                        'rightWins':'losses'}).copy()
    merge_df_b = raw_df.rename(columns={'r_player':'player',
                                        'l_player':'opponent',
                                        'r_wins':'wins',
                                        'l_wins':'losses',
                                        'rightPlayerId':'player',
                                        'leftPlayerId':'opponent',
                                        'rightWins':'wins',
                                        'leftWins':'losses'}).copy()
    merge_df_a['bouts'] = merge_df_a['wins'] + merge_df_a['losses']
    merge_df_b['bouts'] = merge_df_b['wins'] + merge_df_b['losses']

    for df in [merge_df_a, merge_df_b]:
        if draws_rule == 'hr_draws_rule_ignore':
            pass
        elif draws_rule in ['hr_draws_rule_win', 'hr_draws_rule_loss']:
            df['wins'] += df['draws']
            df['bouts'] += 2 * df['draws']
        else:
            raise RuntimeError(f'invalid draws_rule {draws_rule}')
            
    rslt = (pd.concat([merge_df_a, merge_df_b], axis=0)
            .groupby(['player','opponent']).sum().reset_index())
    LOGGER.debug('original table follows')
    LOGGER.debug(raw_df)
    LOGGER.debug('rslt follows')
    LOGGER.debug(rslt)
    rslt = rslt.drop(columns=[col for col in ['draws', 'note'] if col in rslt.columns])
    return rslt


def initialize_weights(n_players, n_chains=1):
    return np.ones((n_chains, n_players))


def mutate(w_vec, idx, rng, sigma=1.0):
    n_chains, n_players = w_vec.shape
    norm_samp = sigma * rng.standard_normal(size=n_chains)
    scale_fac = np.exp(norm_samp)
    rslt = w_vec.copy()
    rslt[:,idx] *= scale_fac
    return rslt


def calc_p_ratio(idx, player, old_wts, new_wts, samples_df):
    n_chains, n_players = old_wts.shape
    col_d = {nm:counter for counter, nm in enumerate(samples_df.columns)}
    player_col = col_d['player']
    opp_col = col_d['opponent']
    wins_col = col_d['wins']
    bouts_col = col_d['bouts']
    df_mtx = samples_df.values
    mask = df_mtx[:, player_col] == player
    sub_df_mtx = df_mtx[mask, :]
    #print(f'idx = {idx}; player = {player}; sub_df_mtx follows')
    #print(sub_df_mtx)
    n_opp = sub_df_mtx.shape[0]

    w = old_wts[:, idx]
    old_wts_exclude = np.delete(old_wts, idx, axis=1)
    #print(f'w: {w}')
    wprime = new_wts[:, idx]
    #print(f'wprime: {wprime}')
    log_w_ratio = np.log(wprime/w)
    #print(f'log_w_ratio: {log_w_ratio}')
    opp_idx = np.arange(sub_df_mtx.shape[0])
    #print(f'opp_idx: {opp_idx}')
    w_opp = old_wts_exclude[:, opp_idx]
    #print(f'w_opp: {w_opp}')
    p1 = np.log((w[:, None] + w_opp)/(wprime[:, None] + w_opp))
    p2 = sub_df_mtx[:, bouts_col]
    tot = (np.outer(log_w_ratio, sub_df_mtx[:, wins_col])
           + np.einsum('ij,j -> ij', p1, p2))
    #print(f'p1: {p1}  p2: {p2}  tot: {tot}')
    rslt = np.exp(np.sum(tot, axis=1))
    #print(f'result: {rslt}')
    return rslt


def sweep(player_id_vec, w_vec, win_loss_df, rng, sigma):
    """
    Not really a sweep- we try n_players mutations, but the player that
    gets updated is chosen at random each time, so some players may be
    skipped or updated more than once.
    """
    n_chains, n_players = w_vec.shape
    assert player_id_vec.shape[0] == n_players, ("Weight vector length does"
                                                 " not match players")
    tot_accepted = 0
    tot_trials = 0
    for trial in range(n_players):
        idx = np.random.randint(n_players)
        player = player_id_vec[idx]
        mutated_w_vec = mutate(w_vec, idx, rng, sigma=sigma)
        p_ratio = calc_p_ratio(idx, player, w_vec, mutated_w_vec, win_loss_df)
        choice_vec = (np.random.random(n_chains) <= p_ratio)
        tot_accepted += choice_vec.sum()
        tot_trials += np.prod(choice_vec.shape)
        w_vec = np.where(choice_vec[:, None], mutated_w_vec, w_vec)

    return w_vec, tot_accepted/tot_trials


def sample_list_to_array(samp_l):
    n_chains, n_players = samp_l[0].shape
    samp_array = np.empty((len(samp_l), n_chains, n_players))
    for idx, vec in enumerate(samp_l):
        samp_array[idx, :, :] = vec
    samp_array = samp_array.reshape(-1, n_players)
    return samp_array


def metropolis(player_id_list, restructured_df, n_samp, n_chains,
               burnin_sweeps, sweeps_per_samp):
    n_players = len(player_id_list)
    player_id_vec = np.array(player_id_list, dtype=int)
    rng = np.random.default_rng()
    w_vec = initialize_weights(n_players, n_chains)
    # burn-in
    sigma = MUTATION_SIGMA
    accept_ratio_samps = []
    for iter in range(burnin_sweeps):
        w_vec, accept_ratio = sweep(player_id_vec, w_vec, restructured_df,
                                    rng, sigma=sigma)
        accept_ratio_samps.append(accept_ratio)
        accept_ratio_samps = accept_ratio_samps[-10:]  # Keep the last 10
        running_mean_accept_ratio = sum(accept_ratio_samps) / len(accept_ratio_samps)
        #
        # The following is an extremely primitive self-tuning algorithm based on the
        # rule that the acceptance ratio for a Normal jump function should be around
        # 0.3 .
        #
        if (iter + 1) % 10 == 0:
            sigma_initial = sigma
            if running_mean_accept_ratio < 0.2:
                sigma *= 0.5
            elif running_mean_accept_ratio > 0.5:
                sigma *= 1.5
            LOGGER.debug(f'Updating sigma: running mean = {running_mean_accept_ratio}'
                         f' so sigma {sigma_initial} -> {sigma}')
        w_vec /= w_vec[:, 0, None]  # rescale
    LOGGER.debug(f'burn-in complete; sigma={sigma}')
    samp_l = []
    for samp in range(n_samp):
        for iter in range(sweeps_per_samp):
            w_vec, accept_ratio = sweep(player_id_vec, w_vec, restructured_df,
                                        rng, sigma=sigma)
            w_vec /= w_vec[:, 0, None]  # rescale
        samp_l.append(w_vec.copy())

    samp_array= sample_list_to_array(samp_l)
    return samp_array


class ModelFit(object):
    def __init__(self, player_df, bout_df):
        self.player_df = player_df
        self.bouts_df = bout_df  # in restructured form
        self.samp_array = None
        self.win_probabilities = None
        self.player_id_list = [elt for elt in self.bouts_df['player'].unique()]
        self.player_name_dict = {row['id']: row['name']
                                 for idx, row in self.player_df.iterrows()}

    def from_raw_bouts(player_df, raw_bouts_df, draws_rule=None):
        """
        This version of the constructor includes restructuring of the
        bouts dataframe.

        If present, draws_rule must be one of the 'hr_draws_rule' settings
        """
        restructured_df = restructure_df(raw_bouts_df, draws_rule=draws_rule)
        return ModelFit(player_df, restructured_df)

    def gen_samples(self):
        #print(self.player_name_dict)
        self.win_probabilities = None  # Any old result is about to become invalid
        self.samp_array = metropolis(self.player_id_list, self.bouts_df,
                                     N_SAMP, N_CHAINS, BURNIN_SWEEPS,
                                     SWEEPS_PER_SAMP)
    @staticmethod
    def set_axis_style(ax, labels):
        ax.xaxis.set_tick_params(direction='out')
        ax.xaxis.set_ticks_position('bottom')
        ax.set_xticks(np.arange(1, len(labels)+1))
        ax.tick_params(axis='x', labelsize='small', labelrotation=45.0)
        ax.set_xticklabels(labels)
        ax.set_xlim(0.25, len(labels) + 0.75)
        ax.set_xlabel('Player name')
                      
    def gen_graph(self, fig, axis, graph_type):
        if self.samp_array is None:
            self.gen_samples()
        if graph_type == 'violin':
            labels = [self.player_name_dict[id] for id in self.player_id_list]
            self.set_axis_style(axis, labels)
            axis.violinplot(self.samp_array)
        elif graph_type == 'boxplot':
            labels = [self.player_name_dict[id] for id in self.player_id_list]
            self.set_axis_style(axis, labels)
            axis.boxplot(self.samp_array, labels=labels, showfliers=False)
        else:
            raise RuntimeError(f'Unknown graph type {graph_type}')

    def estimate_win_probabilities(self) -> 'WinProbabilities':
        self.win_probabilities = WinProbabilities(self)
        return self.win_probabilities

    def gen_bouts_graph_svg(self):
        """
        Write a graph representation of the bouts network to outfile
        """
        grph = pgv.AGraph(strict=False, directed=False)
        grph.graph_attr['overlap'] = 'scale'
        for idx, row in self.player_df.iterrows():
            grph.add_node(row['name'])
        penw_scale = 10.0 / self.bouts_df['bouts'].max()
        for idx, row in self.bouts_df.iterrows():
            if row['player'] <= row['opponent']:  # don't double-count bouts
                grph.add_edge(self.player_name_dict[row['player']],
                              self.player_name_dict[row['opponent']],
                              weight=row['bouts'],
                              penwidth=(penw_scale * row['bouts']),
                              dir='both', arrowhead='normal',
                              label=f"{row['bouts']} bouts")
        grph.layout(prog="neato")
        tmpf = TemporaryFile()
        grph.draw(tmpf, format="svg")
        tmpf.seek(0)
        svg_str = tmpf.read().decode("utf-8")
        tmpf.close()  # causes file to be removed
        return svg_str


class WinProbabilities(object):
    def __init__(self, model_fit: ModelFit):
        self.model_fit = model_fit
        if self.model_fit.samp_array is None:
            self.model_fit.gen_samples()
        n_samps, n_players = self.model_fit.samp_array.shape
        #print(n_samps, n_players)
        winner_hits = {id: 0 for id in self.model_fit.player_id_list}
        top3_hits = {id: 0 for id in self.model_fit.player_id_list}
        for idx in range(n_samps):
            pairs = [(est, id)
                     for est, id in zip(self.model_fit.samp_array[idx, :],
                                        self.model_fit.player_id_list)]
            pairs.sort(reverse=True)
            ranked_ids = [id for est, id in pairs]
            winner_hits[ranked_ids[0]] += 1
            for idx2 in range(min(3, n_players)):
                top3_hits[ranked_ids[idx2]] += 1
        #print(f'winner_hits: {winner_hits}')
        #print(f'top3_hits: {top3_hits}')
        pairs = [(ct, id) for id, ct in winner_hits.items()]
        pairs.sort(reverse=True)
        winner_ct, winner_id = pairs[0]
        self.winner = (winner_id, winner_ct / n_samps)
        pairs = [(ct, id) for id, ct in top3_hits.items()]
        pairs.sort(reverse=True)
        self.top3 = []
        for idx in range(min(3, n_players)):
            winner_ct, winner_id = pairs[idx]
            self.top3.append((winner_id, winner_ct / n_samps))

    def as_string(self) -> str:
        sio = StringIO()
        id, chance = self.winner
        chance_str = '{:.2f}'.format(chance)
        sio.write(f'{self.model_fit.player_name_dict[id]} has a {chance_str}'
                  ' chance of having won\n')
        for id, chance in self.top3:
            chance_str = '{:.2f}'.format(chance)
            sio.write(f'{self.model_fit.player_name_dict[id]} has a {chance_str}'
                      ' chance of being in the top 3\n')
        return sio.getvalue()

    def as_html(self) -> str:
        sio = StringIO()
        id, chance = self.winner
        chance_str = '{:.2f}'.format(chance)
        sio.write(f'<b>{self.model_fit.player_name_dict[id]}</b> has a {chance_str}'
                  ' chance of having won.<br>')
        sio.write('<br>')
        for id, chance in self.top3:
            chance_str = '{:.2f}'.format(chance)
            sio.write(f'<b>{self.model_fit.player_name_dict[id]}</b> has a {chance_str}'
                      ' chance of being in the top 3.<br>')
        return sio.getvalue()


def estimate(player_df, bouts_df, draws_rule=None):
    """
    If present, draws_rule must be one of the 'hr_draws_rule' settings
    """
    m_f = ModelFit.from_raw_bouts(player_df, bouts_df, draws_rule=draws_rule)
    m_f.gen_samples()
    return m_f


def main():
    n_players = 10
    player_names = ['Andy le Fake', 'Bob le Fake', 'Carl le Fake',
                    'Doug le Fake', 'Ellen le Fake', 'Fran le Fake',
                    'Grace le Fake', 'Hugh le Fake', 'Inez le Fake',
                    'John le Fake']
    n_bouts = 40000
    player_wts = np.zeros(n_players, dtype=float)
    for i in range(n_players):
        player_wts[i] = i+1
    player_df = pd.DataFrame([{'id':id, 'name':nm, 'weight':wt, 'note':''}
                              for id, nm, wt in zip(range(n_players),
                                                    player_names,
                                                    player_wts)])
    print('player_df follows')
    print(player_df)
    # player_df.to_csv('/tmp/long_tourney_entrants.tsv', sep='\t')
    totals_df = generate_random_bouts(n_players, n_bouts, player_wts)
    # print('totals_df follows')
    # print(totals_df)
    restructured_df = restructure_df(totals_df)

    # merged_df = pd.merge(totals_df, player_df, left_on='l_player', right_on='id')
    # merged_df = merged_df.rename(columns={'name':'leftPlayerName'}).drop(columns=['weight','id',
    #                                                                              'note'])
    # merged_df = pd.merge(merged_df, player_df, left_on='r_player', right_on='id')
    # merged_df = merged_df.rename(columns={'name':'rightPlayerName'}).drop(columns=['weight','id',
    #                                                                                'note'])

    # merged_df = merged_df.rename(columns={'l_wins':'leftWins',
    #                                       'r_wins':'rightWins'}).drop(columns=['l_player',
    #                                                                            'r_player'])
    # merged_df['draws'] = 0
    # merged_df['tourneyName'] = f'long tourney example, {n_bouts} bouts'
    # print('merged:')
    # print(merged_df)
    # merged_df.to_csv('/tmp/tourney_40.tsv', sep='\t', index=False)

    trimmed_df = restructured_df[restructured_df['player'] != 3]
    trimmed_df = trimmed_df[trimmed_df['opponent'] != 3]
    print('trimmed_df follows')
    print(trimmed_df)
    # m_f_1 = ModelFit(player_df, restructured_df)
    m_f_2 = ModelFit(player_df, trimmed_df)
    # fig, axes = plt.subplots(ncols=2, nrows=1)
    # m_f_1.gen_graph(fig, axes[0], 'violin')
    # m_f_2.gen_graph(fig, axes[1], 'boxplot')
    # plt.show(block=True)

    print(m_f_2.estimate_win_probabilities().as_string())
    
if __name__ == '__main__':
    main()
