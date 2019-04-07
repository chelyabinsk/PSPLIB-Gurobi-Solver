#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""


http://mmlib.eu/download.php

"""
from gurobipy import *
import probleminputs
import es_ls_solver

class Solver:
    def __init__(self,filename):
        print("Solving " + filename)
        I = probleminputs.Inputs("data/converted/",filename)
        
        self.n_jobs = I.n_jobs
        self.n_modes = I.n_modes
        
        self.job_modes = I.job_modes
        
        self.successor = I.successor
        self.duration_mode = I.duration_mode
        
        self.n_renewable = I.n_renewable
        self.resource_list = I.resource_list
        self.job_mode_resource = I.job_mode_resource
        self.n_res_types = I.n_res_types
        
        # Solve two LP's problems to figure out ES and LS
        times_solver = es_ls_solver.ES_LS_Solver(self.n_jobs,
                                         self.successor,
                                         self.duration_mode)
        
        #self.job_late_start = times_solver.ls
        self.job_early_start = times_solver.es
        
        if(I.horizon == 0):
            #self.horizon = sum(self.job_late_start)
            self.horizon = max(self.job_early_start)*2
        else:
            self.horizon = I.horizon
        
        #self.horizon = sum(self.job_late_start)
        #self.horizon = I.horizon
        self.I = I
        
        
    def do_solve(self):  
        
        print("Creating problem")
        try:
            
            print("n_jobs = {}".format(self.n_jobs))
        
            # Create a new model
            m = Model("mip1")
            x_list = []
            # Create variables
            print("Creating variables")
            
            # Create x variables
            for i in range(1,self.n_jobs):
                #print("i:{}".format(i))
                for mode in self.job_modes[i]:
                    for e in range(self.n_jobs - 1):
                        x_list.append(((i,mode,e),m.addVar(vtype=GRB.BINARY, name="X_{}_{}_{}".format(i,mode,e))))
            x = gurobipy.tupledict(x_list)
            del x_list
            self.x = x
            
            # Create continious t variable
            t_list = []
            for e in range(self.n_jobs - 1):
                t_list.append(((e),m.addVar(vtype=GRB.CONTINUOUS, lb=0, name="T_{}".format(e))))
            t = gurobipy.tupledict(t_list)
            del t_list
            self.t = t
            
            # Create C_max variable
            c_max = m.addVar(vtype=GRB.CONTINUOUS,name="C_MAX")
            self.c_max = c_max
            
            
            # Create objective function
            print("Creating objective function")            
            m.setObjective(c_max,GRB.MINIMIZE)
            self.m = m
            
            # Create first constraint
            print("Creating constraint 1")
            m.addConstrs(c_max >= t[e] 
            + (x[i,mode,e] - x[i,mode,e-1])*self.duration_mode[i][mode] for e in range(1,len(t))
                                                                        for i in range(1,len(t))
                                                                        for mode in self.job_modes[i])
            # Create second constraint
            print("Creating constraint 2")
            m.addConstr(t[0] == 0)

            # Create third constraint
            print("Creating constraint 3")
            m.addConstrs(
                   t[f] >= t[e]
                   + ( (x[i,mode,e] - x[i,mode,e-1]) 
                      -(x[i,mode,f] - x[i,mode,f-1]) - 1
                     ) * self.duration_mode[i][mode]    for i in range(1,len(t))
                                                        for e in range(1,len(t))
                                                        for f in range(e+1,len(t))
                                                        for mode in self.job_modes[i]
                   )
            # Create fourth constraint
            print("Creating constraint 4")
            m.addConstrs(t[e+1] >= t[e] for e in range(len(t)-1))
            
            # Create fifth constraint
            print("Creating constraint 5")
            m.addConstrs(gurobipy.quicksum(
                    x[i,mode,e_] for e_ in range(e)
                                 for mode in self.job_modes[i]
                    ) <= e*(1-(x[i,mode_,e] - x[i,mode_,e-1]))  for e in range(1,len(t))
                                                                for i in range(1,len(t))
                                                                for mode_ in self.job_modes[i]
                   )
                   
            # Create sixth constraint
            print("Creating constraint 6")
            m.addConstrs(gurobipy.quicksum(
                    x[i,mode,e_] for e_ in range(e,len(t))
                                 for mode in self.job_modes[i]
                    ) <= ((len(t)-1)-e)*(1+(x[i,mode_,e] - x[i,mode_,e-1]))  for e in range(1,len(t))
                                                                for i in range(1,len(t))
                                                                for mode_ in self.job_modes[i]
                   )
                   
            # Create seventh constraint
            print("Creating constraint 7")
            m.addConstrs(gurobipy.quicksum(x[i,mode,e] for e in range(len(t))
                                                       for mode in self.job_modes[i]
                                          ) >= 1       for i in range(1,len(t))
                                                       
                        )
            # Create eighth constraint
            print("Creating constraint 8")
            m.addConstrs(x[i,mode,e] +
            gurobipy.quicksum(x[j,mode_,e_] for mode_ in self.job_modes[j]
                                            for e_ in range(e)
                             ) <= 1 + e*(1-x[i,mode,e]) for e in range(len(t))
                                                        for i in range(1,len(t)-1)
                                                        for j in self.successor[i]
                                                        for mode in self.job_modes[i]
            )
            
            print("Running the solver")
            # Run the solver    
            m.optimize()
            
            self.m = m
        
        except GurobiError:
            print("Error!")
            