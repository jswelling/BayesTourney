#! /usr/bin/env python

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


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
    print('restructured df:')
    print(rslt)
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
    col_d = {nm:idx for idx, nm in enumerate(samples_df.columns)}
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
    #print(f'w: {w}')
    wprime = new_wts[:, idx]
    log_w_ratio = np.log(wprime/w)
    opp_idx = np.arange(sub_df_mtx.shape[0])
    w_opp = old_wts[:, opp_idx]
    p1 = np.log((w[:, None] + w_opp)/(wprime[:, None] + w_opp))
    p2 = sub_df_mtx[:, bouts_col]
    tot = np.outer(log_w_ratio, sub_df_mtx[:, wins_col]) + np.einsum('ij,j -> ij', p1, p2)
    return np.exp(np.sum(tot, axis=1))


def sweep(player_id_list, w_vec, win_loss_df, rng, sigma):
    n_chains, n_players = w_vec.shape
    assert len(player_id_list) == n_players, "Weight vector length does not match players"
    #print(f'player_id_list: {player_id_list}')
    #for idx in player_id_list:
    for idx, player in enumerate(player_id_list):
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


def metropolis(player_id_list, restructured_df, n_samp, n_chains, burnin_sweeps, sweeps_per_samp):
    print('player_id_list IS REDUNDANT!')
    n_players = len(player_id_list)
    rng = np.random.default_rng()
    w_vec = initialize_weights(n_players, n_chains)
    # burn-in
    for iter in range(burnin_sweeps):
        w_vec = sweep(player_id_list, w_vec, restructured_df, rng, sigma=0.1)
        w_vec /= w_vec[:, 0, None]  # rescale
    print('burn-in complete')
    samp_l = []
    for samp in range(n_samp):
        for iter in range(sweeps_per_samp):
            w_vec = sweep(player_id_list, w_vec, restructured_df, rng, sigma=0.1)
            w_vec /= w_vec[:, 0, None]  # rescale
        samp_l.append(w_vec.copy())
        print(samp)

    samp_array= sample_list_to_array(samp_l)
    return samp_array


def estimate(player_df, bouts_df):
    print('player_df follows')
    print(player_df)
    print('bouts_df follows')
    print(bouts_df)
    n_players = len(player_df)

    restructured_df = restructure_df(bouts_df)

    burnin_sweeps = 300
    n_samp = 5
    sweeps_per_samp = 100
    n_chains = 20
    player_id_list = [elt for elt in restructured_df['player'].unique()]
    print(player_id_list)
    samp_array = metropolis(player_id_list, restructured_df, n_samp, n_chains, burnin_sweeps, sweeps_per_samp)

    fig, axes = plt.subplots(ncols=1, nrows=1)
    axes.violinplot(samp_array)
    plt.show(block=True)

    return {}

#     playerLut = {}
#     nPlayers = len(orderedPlayerList)
#     for i,p in enumerate(orderedPlayerList): playerLut[p.id] = i
#     #print playerLut
#     colCount = 0
#     colLut = {}
#     orderedCols = []
#     for i in range(nPlayers):
#         for j in range(nPlayers-(i+1)):
#             pair = (i,i+j+1)
#             colLut[pair] = colCount
#             colCount += 1
#             orderedCols.append(pair)
#     #print colLut
#     nFactors = colCount
#     print("nFactors: %d"%nFactors)
#     trialDict = {}
#     for b in boutList:
#         l = playerLut[b.leftPlayerId]
#         r = playerLut[b.rightPlayerId]
#         if l < r :
#             key = (l,r)
#             lWins = b.leftWins
#             rWins = b.rightWins
#         elif r < l :
#             key = (r,l)
#             lWins = b.rightWins
#             rWins = b.leftWins
#         else:
#             raise RuntimeError('bad trial; got (%s,%s,%s)'%(b.lName,b.rName))
#         if key in trialDict:
#             count, wins = trialDict[key]
#             trialDict[key] = count+lWins+rWins, wins+lWins
#         else:
#             trialDict[key] = lWins+rWins, lWins
#     for k,v in list(trialDict.items()):
#         l,r = k
#         count,wins = v
#         print("%s %s : %d of %d"%(orderedPlayerList[l],orderedPlayerList[r],wins,count))
#     obsList = []
#     countsList = []
#     for key in orderedCols:
#         if key in trialDict:
#             count,wins = trialDict[key]
#         else:
#             count,wins = (0,0)
#         countsList.append(count)
#         obsList.append(wins)
#     obs = numpy.array(obsList,dtype=numpy.float)
#     obs = obs.transpose()
#     counts = numpy.array(countsList,dtype=numpy.float)
#     counts = counts.transpose()
#     betas = numpy.zeros(nPlayers)
#     print('obs: %s'%obs)
#     print('counts: %s'%counts)
#     print('ratios: %s'%(obs/counts))
#     factors = numpy.zeros([nFactors,nPlayers])
#     for key in orderedCols:
#         i,j = key
#         offset = colLut[key]
#         factors[offset,i] = 1.0
#         factors[offset,j] = -1.0
#     print('factors: \n%s'%factors)
#     try:
#         params = fit(nPlayers, obs, factors, counts)
#         print('params by lr: %s'%params)
#         result = []
#         for p,s in zip(orderedPlayerList,params): result.append((p,s))
#         return result
#     except Exception as e:
#         raise RuntimeError("Fit did not converge: %s"%e)
#     #params = fit2(nPlayers, obs, factors, counts)
#     #print 'params by praxis: %s'%params
# #    for i in xrange(obs.shape[0]):
# #        cObs = obs.copy()
# #        if cObs[i] == counts[i] : cObs[i] -= 1
# #        else: cObs[i] += 1
# #        params = fit(nPlayers, cObs, factors, counts)
# #        print 'params tweaking %d: %s'%(i,params)
#     #print ratios[:nPlayers]/ratios[0]
# #    with open('/tmp/stuff.gnuplot','a') as f:
# #        for i,v in enumerate(numpy.exp(beta)):
# #            f.write("%f, %f\n"%(float(i+1),v))


def main():
    n_players = 10
    player_wts = np.zeros(n_players, dtype=float)
    for i in range(n_players):
        player_wts[i] = i+1

    n_bouts = 4000
    totals_df = generate_random_bouts(n_players, n_bouts, player_wts)
    restructured_df = restructure_df(totals_df)

    burnin_sweeps = 300
    n_samp = 5
    sweeps_per_samp = 100
    n_chains = 20

    trimmed_df = restructured_df[restructured_df['player'] != 3]
    trimmed_df = trimmed_df[trimmed_df['opponent'] != 3]
    print(trimmed_df)
    samp_array = metropolis([n for n in range(n_players)],
                            restructured_df, n_samp, n_chains, burnin_sweeps, sweeps_per_samp)
    trimmed_samp_array = metropolis([n for n in range(n_players) if n != 3],
                                    trimmed_df,
                                    n_samp, n_chains, burnin_sweeps, sweeps_per_samp)
    fig, axes = plt.subplots(ncols=2, nrows=1)
    axes[0].violinplot(samp_array)
    axes[1].violinplot(trimmed_samp_array)
    plt.show(block=True)


if __name__ == '__main__':
    main()
