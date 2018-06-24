#! /usr/bin/env python

import random
import playermodel,lordbayes

#random.seed(1234)

#players = ['Andy', 'Bob', 'Carl', 'Donna', 'Erin', 'Fran']
activePlayerNames = ['Andy', 'Bob', 'Carl', 'Donna', 'Erin', 'Fran']
hiddenScores = { 'Andy':1.0, 'Bob':2.0, 'Carl':3.0, 'Donna': 4.0, 'Erin': 5.0, 'Fran':6.0}

def genRandomBouts(playersByName, activePlayerNames, nTrials):
    result = []
    for _ in xrange(nTrials):
        pair = random.sample(activePlayerNames,2)   
        result.append( playermodel.Bout(playersByName[pair[0]], playersByName[pair[1]]))     
    return result


playersByName = {}
for name,score in hiddenScores.items():
    playersByName[name] = playermodel.LogitPlayer(name,score)
bouts = genRandomBouts(playersByName, activePlayerNames,100)
for i,b in enumerate(bouts): print "%d: %s"%(i,b)
for b in bouts: b.resolve()
for i,b in enumerate(bouts): 
    print "%d: %s"%(i,b)
    print b.getWinner()
    print b.getLoser()
estDict = lordbayes.estimate(playersByName, activePlayerNames, bouts)
#counts = {}
#trials = genRandomOutcomes(playersByName, activePlayerNames,10000)
##print trials
#estDict = lordbayes.estimate(players,trials)
#print estDict
