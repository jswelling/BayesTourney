#! /usr/bin/env python

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

"""Number of sweeps used in Metropolis burn-in"""
BURNIN_SWEEPS = 300
#BURNIN_SWEEPS = 0

"""Number of Metropolis samples to generate, per chain"""
N_SAMP = 500
#N_SAMP = 20

"""Number of sweeps between samples, to minimize correlation"""
SWEEPS_PER_SAMP = 100
#SWEEPS_PER_SAMP = 1

"""Number of independent Metropolis Markov Chains run simultaneously per thread"""
N_CHAINS = 20
#N_CHAINS = 1

"""Standard deviation of normal used to generate mutation step sizes"""
MUTATION_SIGMA = 0.03

"""Number of samples to use in estimating victory probability"""
N_VICTORY_SAMPS = 10000

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


def restructure_df(raw_df):
    """
    We are excluding draws from the bouts totals at this point.
    """
    merge_df_a = raw_df.rename(columns={'l_player':'player', 'r_player':'opponent', 'l_wins':'wins', 'r_wins':'losses',
                                        'leftPlayerId':'player', 'rightPlayerId':'opponent', 'leftWins':'wins',
                                        'rightWins':'losses'})
    merge_df_a['bouts'] = merge_df_a['wins'] + merge_df_a['losses']
    merge_df_b = raw_df.rename(columns={'r_player':'player', 'l_player':'opponent', 'r_wins':'wins', 'l_wins':'losses',
                                        'rightPlayerId':'player', 'leftPlayerId':'opponent', 'rightWins':'wins',
                                        'leftWins':'losses'})
    merge_df_b['bouts'] = merge_df_b['wins'] + merge_df_b['losses']
    rslt = pd.concat([merge_df_a, merge_df_b], axis=0).groupby(['player','opponent']).sum().reset_index()
    rslt = rslt.drop(columns=[col for col in ['draws', 'note'] if col in rslt.columns])
    return rslt


def initialize_weights(n_players, n_chains=1):
    return np.ones((n_chains, n_players))


def mutate(w_vec, idx, rng, sigma=1.0):
    n_chains, n_players = w_vec.shape
    norm_samp = rng.standard_normal(size=n_chains)
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
    for trial in range(n_players):
        idx = np.random.randint(n_players)
        player = player_id_vec[idx]
        mutated_w_vec = mutate(w_vec, idx, rng, sigma=sigma)
        p_ratio = calc_p_ratio(idx, player, w_vec, mutated_w_vec, win_loss_df)
        choice_vec = (np.random.random(n_chains) <= p_ratio)
        w_vec = np.where(choice_vec[:, None], mutated_w_vec, w_vec)
    return w_vec


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
    for iter in range(burnin_sweeps):
        w_vec = sweep(player_id_vec, w_vec, restructured_df,
                      rng, sigma=MUTATION_SIGMA)
        w_vec /= w_vec[:, 0, None]  # rescale
    print('burn-in complete')
    samp_l = []
    for samp in range(n_samp):
        for iter in range(sweeps_per_samp):
            w_vec = sweep(player_id_vec, w_vec, restructured_df,
                          rng, sigma=MUTATION_SIGMA)
            w_vec /= w_vec[:, 0, None]  # rescale
        samp_l.append(w_vec.copy())
        print(samp)

    samp_array= sample_list_to_array(samp_l)
    return samp_array


class ModelFit(object):
    def __init__(self, player_df, bout_df):
        self.player_df = player_df
        self.bouts_df = bout_df  # in restructured form
        self.samp_array = None
        self.player_id_list = None
        self.player_name_dict = None
    def gen_samples(self):
        self.player_id_list = [elt for elt in self.bouts_df['player'].unique()]
        self.player_name_dict = {row['id']: row['name']
                                 for idx, row in self.player_df.iterrows()}
        #print(self.player_name_dict)
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
        
    def estimate_victory_probabilities(self):
        if self.samp_array is None:
            self.gen_samples()
        n_samps, n_players = self.samp_array.shape
        print(n_samps, n_players)
        total_win_prob = 0.0
        for idx, player_id in enumerate(self.player_id_list):
            print(self.player_name_dict[player_id])
            samps = np.random.choice(self.samp_array[:, idx], N_VICTORY_SAMPS)
            cum_win_prob = 1.0
            for opp_idx in range(n_players):
                if opp_idx == idx:
                    print('--------------')
                    continue
                opp_samps = np.random.choice(self.samp_array[:, opp_idx],
                                             N_VICTORY_SAMPS)
                rslt = np.choose(samps > opp_samps, [0, 1])
                print('----------------')
                print(np.sum(rslt))
                win_prob = float(np.sum(rslt))/float(N_VICTORY_SAMPS)
                cum_win_prob *= win_prob
            print(f'{self.player_name_dict[player_id]} median {np.median(self.samp_array[:, idx])}, win prob: {cum_win_prob}')
            total_win_prob += cum_win_prob
        print(f'total win prob: {total_win_prob}')
        for idx in range(n_players):
            print(f'{self.player_name_dict[self.player_id_list[idx]]}')
            bins, bounds = np.histogram(self.samp_array[:,idx], bins=100)
            peak_idx = np.argmax(bins)
            print(peak_idx, bounds[peak_idx], bounds[peak_idx+1])
                

def estimate(player_df, bouts_df):
    restructured_df = restructure_df(bouts_df)
    m_f = ModelFit(player_df, restructured_df)
    m_f.gen_samples()
    return m_f


def main():
    n_players = 10
    player_names = ['andy', 'bob', 'carl', 'doug', 'ellen', 'fran', 'grace',
                    'hugh', 'inez', 'john']
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
    totals_df = generate_random_bouts(n_players, n_bouts, player_wts)
    restructured_df = restructure_df(totals_df)

    trimmed_df = restructured_df[restructured_df['player'] != 3]
    trimmed_df = trimmed_df[trimmed_df['opponent'] != 3]
    print('trimmed_df follows')
    print(trimmed_df)
    m_f_1 = ModelFit(player_df, restructured_df)
    m_f_2 = ModelFit(player_df, trimmed_df)
    fig, axes = plt.subplots(ncols=2, nrows=1)
    m_f_1.gen_graph(fig, axes[0], 'violin')
    m_f_2.gen_graph(fig, axes[1], 'boxplot')
    plt.show(block=True)

    m_f_1.estimate_victory_probabilities()
    
if __name__ == '__main__':
    main()
