# -*- coding: utf-8 -*-
"""
This is where I am going to create data.

This script is going to generate two types of data

1) Which jobs can go in which room (number of available rooms for each jobs is a variable)
2) Travel times between locations (this is going to be based on some parameters)
"""

import numpy as np
from numpy.random import choice
from random import randint as rndint
from random import uniform  as uniform
from random import sample as sample
from random import seed as seed
import math

class Location_Generator():
    def __init__(self, n_loc, n_jobs, move_frac,travel_bounds,run_num=0):
        """
        n_loc         : number of locations
        n_jobs        : number of jobs
        move_frac     : fraction of jobs that can have more than 1 location
        travel_bounds : lower and upper bounds on the travel times
        
        """
        
        seedinst = 12041997+run_num
        
        # Create seed
        seed(seedinst)
        np.random.seed(seedinst)
        
        self.n_loc = n_loc
        self.n_jobs = n_jobs
        self.move_frac = move_frac
        self.travel_bounds = travel_bounds
        
    def make_pos_data(self):
        # Initialise a zero matrix
        j_move = np.zeros((self.n_jobs,self.n_loc))
        
        if(self.n_loc == 1 or self.move_frac == 1):
            j_move = np.ones((self.n_jobs,self.n_loc))
        else:
            probs = self.gen_probs()
            
            for i in range(self.n_jobs):
                k = choice(range(1,self.n_loc+1), 1, p=probs).item()
                #print(k)
                
                poses = sample(range(self.n_loc),k)
                
                for pos in poses:
                    j_move[i,pos] = 1
        
        return j_move
    
    def make_travel_times_data(self):
        j_travel = np.zeros((self.n_loc,self.n_loc))
        
        for i in range(self.n_loc):
            for j in range(i+1,self.n_loc):
                l,u = self.travel_bounds
                travel_time = rndint(l,u)
                j_travel[i,j] = travel_time
                j_travel[j,i] = travel_time
                
        return j_travel
    
    def gen_probs(self):
        # Function to generate the probability list
        probs = []  # Cumulative prob
        for i in range(self.n_loc):
            probs.append( (i/self.n_loc)**(math.log(1-self.move_frac)/math.log( (self.n_loc - 1)/(self.n_loc) )) )
        probs.append(1)
        # Generate non-cumulative probs
        noncumprob = []
        for i in range(len(probs)-1):
            noncumprob.append(probs[i+1] - probs[i])
        return noncumprob
    
        

#L = Location_Generator(5,10,0.5,(1,10),10)
##print(L.gen_probs())
#print(L.make_pos_data())
#print(L.make_travel_times_data())