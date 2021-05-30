#! /usr/bin/env python

import sys, types
import numpy
#from fiasco_numpy import *
import playermodel

def estimateDummy(playersByName, orderedPlayerList, trialList):
    result = {}
    for l,r,wi in trialList:
        if wi == 0:
            if l in result: result[l] += 1.0
            else: result[l] = 1.0
        else:
            if r in result: result[r] += 1.0
            else: result[r] = 1.0
    return result

def fit(nPlayers, obs, factors, counts):
    regressor = create_logistic_regressor()
    nParams = regressor.n_params(nPlayers)
    params = numpy.zeros(nParams)
    #regressor.set(GLM_DEBUG,1)
    regressor.fit(obs, factors, counts, params)
    beta = params
    beta = beta - numpy.min(beta)
    return numpy.exp(beta)

#def chisqr(est, obs, factors, counts):
def chisqr(est, hook):
    obs,factors,counts = hook
    estP = numpy.ones(est.shape[0]+1)
    estP[1:] = est
    weights = numpy.sqrt(counts)
    nPlayers = factors.shape[1]
    nObs = factors.shape[0]
    assert nObs==obs.shape[0], 'Dimension mismatch'
    sum = 0.0
    for i in range(nObs):
        count = counts[i]
        if count>0.0:
            ratio = obs[i]/count
            i = i
            row = factors[i]
            lE = (row == 1.0)
            l = estP[lE]
            r = estP[row == -1.0]
            v = (l/(l+r))[0]
            delta = ratio-v
            sum += weights[i]*delta*delta
    return sum

def resetFun( array, hook ):
    #print "In resetFun! <%s> <%s>"%(repr(array),repr(hook))
    pass

def fit2(nPlayers, obs, factors, counts):
    est = numpy.ones(factors.shape[1]-1)
    #opt= createNelminOptimizer(0.0001,1.0,5)
    opt= createPraxisOptimizer(0.000001,1.0)
    sf= buildSimpleScalarFunction( (chisqr, resetFun, factors.shape[1]-1, 
                                    (obs, factors, counts)) )
    #opt.setDebugLevel(1)
    opt.go(sf, est)
    params = numpy.ones(est.shape[0]+1)
    params[1:] = est
    return params

def estimate(playersByName, orderedPlayerList, trialList):
    playerLut = {}
    nPlayers = len(orderedPlayerList)
    for i,p in enumerate(orderedPlayerList): playerLut[p] = i
    #print playerLut
    colCount = 0
    colLut = {}
    orderedCols = []
    for i in range(nPlayers):
        for j in range(nPlayers-(i+1)):
            pair = (i,i+j+1)
            colLut[pair] = colCount
            colCount += 1
            orderedCols.append(pair)
    #print colLut
    nFactors = colCount
    print("nFactors: %d"%nFactors)
    trialDict = {}
    if isinstance(trialList[0],tuple):
        tupleTrialList = trialList
    else: 
        tupleTrialList = [(str(b.getWinner()), str(b.getLoser()), 0) for b in trialList]
    for lName,rName,wI in tupleTrialList:
        l = playerLut[lName]
        r = playerLut[rName]
        if wI not in [0,1]:
            raise RuntimeError('bad trial; got (%s,%s,%s)'%(lName,rName,wI))
        if l < r :
            key = (l,r)
            if wI == 0: won = True
            else: won = False
        elif r < l :
            key = (r,l)
            if wI == 1: won = True
            else: won = False
        else:
            raise RuntimeError('bad trial; got (%s,%s,%s)'%(lName,rName,wI))
        if key in trialDict:
            count, wins = trialDict[key]
            if won:
                trialDict[key] = (count+1, wins+1)
            else:
                trialDict[key] = (count+1, wins)
        else:
            count = 1
            if won: wins = 1
            else: wins = 0
            trialDict[key] = (count, wins)
    for k,v in list(trialDict.items()):
        l,r = k
        count,wins = v
        print("%s %s : %d of %d"%(orderedPlayerList[l],orderedPlayerList[r],wins,count))
    obsList = []
    countsList = []
    for key in orderedCols:
        if key in trialDict:
            count,wins = trialDict[key]
        else:
            count,wins = (0,0)
        countsList.append(count)
        obsList.append(wins)
    obs = numpy.array(obsList,dtype=numpy.float)
    obs = obs.transpose()
    counts = numpy.array(countsList,dtype=numpy.float)
    counts = counts.transpose()
    betas = numpy.zeros(nPlayers)
    print('obs: %s'%obs)
    print('counts: %s'%counts)
    print('ratios: %s'%(obs/counts))
    factors = numpy.zeros([nFactors,nPlayers])
    for key in orderedCols:
        i,j = key
        offset = colLut[key]
        factors[offset,i] = 1.0
        factors[offset,j] = -1.0
    print('factors: \n%s'%factors)
    params = fit(nPlayers, obs, factors, counts)
    print('params by lr: %s'%params)
    #params = fit2(nPlayers, obs, factors, counts)
    #print 'params by praxis: %s'%params
    for i in range(obs.shape[0]):
        cObs = obs.copy()
        if cObs[i] == counts[i] : cObs[i] -= 1
        else: cObs[i] += 1
        params = fit(nPlayers, cObs, factors, counts)
        print('params tweaking %d: %s'%(i,params))
    #print ratios[:nPlayers]/ratios[0]
#    with open('/tmp/stuff.gnuplot','a') as f:
#        for i,v in enumerate(numpy.exp(beta)):
#            f.write("%f, %f\n"%(float(i+1),v))
    
    return {}
