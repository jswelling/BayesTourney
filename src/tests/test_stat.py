#! /usr/bin/env python

import random
from collections import defaultdict
from pprint import pprint
import pandas as pd
import bayestourney.stat_utils as stat_utils

players = ['Andy', 'Bob', 'Carl', 'Donna', 'Erin', 'Fran']
hiddenScores = { 'Andy':1.0, 'Bob':2.0, 'Carl':3.0, 'Donna': 4.0, 'Erin': 5.0, 'Fran':6.0}

def genRandomOutcomes(scoreEstDict, nTrials):
    bouts = []
    for _ in range(nTrials):
        pair = random.sample(players,2)
        bouts.append((pair[0],pair[1]))
    result = []
    for l,r in bouts:
        lWt = scoreEstDict[l]
        rWt = scoreEstDict[r]
        if random.random() < lWt/(lWt+rWt):
            result.append((l,r,0))
        else:
            result.append((l,r,1))
    return result
        
def test_estimate():
    player_id_dict = {nm:idx for idx, nm in enumerate(players)}
    player_recs = []
    for nm, idx in player_id_dict.items():
        player_recs.append({'id':idx, 'name':nm})
        player_df = pd.DataFrame(player_recs)
        trials = genRandomOutcomes(hiddenScores,10000)
    bout_recs = []
    for idx, (l_name, r_name, flag) in enumerate(trials):
        bout_recs.append({
            "boutId" : idx,
            "tourneyId" : 0,
            "leftWins" : 1 - flag,
            "leftPlayerId" : player_id_dict[l_name],
            "rightPlayerId" : player_id_dict[r_name],
            "rightWins" : flag,
            "draws" : 0,
            "note" : ""
        })
    bouts_df = pd.DataFrame(bout_recs)
    m_f = stat_utils.estimate(player_df, bouts_df)
    winner_dict = m_f.estimate_win_probabilities().as_dict()
    top3_dict = {name: chance for name, chance in winner_dict['top3']}
    expected_dict = defaultdict(lambda: 0.0)
    expected_dict.update({'Fran': 1.0,
                          'Erin': 1.0,
                          'Donna': 1.0})
    matches = [ abs(chance - expected_dict[name])/(chance + expected_dict[name]) <= 0.01
                for name, chance in top3_dict.items() ]
    assert all(matches)

def main():
    test_estimate()

if __name__ == '__main__':
    main()
