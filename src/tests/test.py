#! /usr/bin/env python

import random
import bayestourney.stat_utils as stat_utils

#players = ['Andy', 'Bob', 'Carl', 'Donna', 'Erin', 'Fran']
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
        
counts = {}
trials = genRandomOutcomes(hiddenScores,10000)
#print trials
estDict = stat_utils.estimate(players,trials)
print(estDict)
