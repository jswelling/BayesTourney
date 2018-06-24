#! /usr/bin/env python

import sys, math, random, types
import lordbayes

class Player:
    def __init__(self,name):
        self.name = name
    def fight(self,otherPlayer):
        if random.random()<=0.5: return 0
        else: return 1
    def __str__(self): return self.name
        
class LogitPlayer(Player):
    def __init__(self,name,weight):
        assert isinstance(weight,types.FloatType), "weight must be a float"
        Player.__init__(self,name)
        self.weight = weight
    def fight(self,otherPlayer):
        assert isinstance(otherPlayer,LogitPlayer), "%s can only fight LogitPlayers"%self.name
        if random.random() < self.weight/(self.weight+otherPlayer.weight): return 0
        else: return 1

class Bout:
    def __init__(self,player0,player1):
        self.l = player0
        self.r = player1
        self.outcome = None
    def resolve(self):
        self.outcome = self.l.fight(self.r)
        return self.outcome
    def getWinner(self):
        if self.outcome is None: self.resolve()
        if self.outcome==0: return self.l
        else: return self.r
    def getLoser(self):
        if self.outcome is None: self.resolve()
        if self.outcome==1: return self.l
        else: return self.r
    def __str__(self):
        if self.outcome is None:
            return "<%s vs. %s>"%(self.l.name,self.r.name)
        elif self.outcome == 0:
            return "<%s defeats %s>"%(self.l.name, self.r.name)
        elif self.outcome == 1:
            return "<%s defeats %s>"%(self.r.name, self.l.name)
        else:
            raise RuntimeError("Bout has invalid outcome %s"%self.outcome)

