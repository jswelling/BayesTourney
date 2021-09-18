#! /usr/bin/env python

import random
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
print(m_f.estimate_win_probabilities().as_string())
