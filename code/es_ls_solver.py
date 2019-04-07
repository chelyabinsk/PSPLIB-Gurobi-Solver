# -*- coding: utf-8 -*-
"""
Created on Sat Dec  1 20:54:54 2018

https://books.google.co.uk/books?id=jED8CAAAQBAJ&pg=PA13&lpg=PA13&dq=neumann+schwindt+zimmermann+project+scheduling+longest+path&source=bl&ots=bonK-5qT7j&sig=RMeuu31gcExnapgIEPgzcT0llz0&hl=de&sa=X&ved=2ahUKEwjWtvjJiPXeAhWEL1AKHcxoD10Q6AEwAHoECAAQAQ#v=onepage&q=neumann%20schwindt%20zimmermann%20project%20scheduling%20longest%20path&f=false

@author: c1536127
"""

from gurobipy import *

class ES_LS_Solver():
    def __init__(self,n_jobs,successor,duration_mode,connections,travel_times = None):
         
        self.n_jobs = n_jobs

        self.successor = successor
        self.duration_mode = duration_mode
        self.connections = connections
        
        self.travel_times = travel_times
                
        self.solve_es()
        self.solve_ls()
        
        
    def solve_es(self):
        try:
        
            # Create a new model
            m = Model("mip1")
            s = []
            # Create variables
            print("Creating variables")
            for i in range(self.n_jobs):
                s.append(m.addVar(vtype=GRB.INTEGER, name="S_{}".format(i)))
            
            # Set S_0 = 0
            m.addConstr(s[0],GRB.EQUAL,0)
            
            # Create objective function
            print("Creating objective function")
            obj = 0*s[0]
            for i in range(self.n_jobs):
                obj += s[i]
            m.setObjective(obj, GRB.MINIMIZE)
            
            # Create constraint
            for i in range(self.n_jobs - 1):
                for j in self.successor[i]:
                    m.addConstr(s[j] - s[i],GRB.GREATER_EQUAL,min(self.duration_mode[i]))
         
            print("Running the solver")
            # Run the solver    
            m.optimize()
            
            self.es = []
            for i in s:
                self.es.append(round(i.X))
            
            self.m = m
        
        except GurobiError:
            print("Error!")
            
    def solve_ls(self):
        self.ls = []
        dist = [0]*self.n_jobs
        # Make the connections list of lists a flat list
        # https://stackoverflow.com/questions/952914/how-to-make-a-flat-list-out-of-list-of-lists
        flat_list = [item for sublist in self.connections for item in sublist]
        
        # https://www.geeksforgeeks.org/longest-path-between-any-pair-of-vertices/
        for u in flat_list:
            if(u != self.n_jobs - 1):
                for v in self.successor[u]:
#                    print("{} !!!!!!!!!!!!!!!!!!! {}".format((self.travel_times.max()),type(self.travel_times)))
                    if(type(self.travel_times) == type(None)):
                        if(dist[v] < dist[u] + max(self.duration_mode[u])):
                            dist[v] = dist[u] + max(self.duration_mode[u])
                    else:
                        if(dist[v] < dist[u] + max(self.duration_mode[u]) + int(self.travel_times.max())):
                            dist[v] = dist[u] + max(self.duration_mode[u]) + int(self.travel_times.max())
        self.ls = dist
        