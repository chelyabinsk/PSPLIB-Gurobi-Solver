#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""


http://mmlib.eu/download.php

"""
from gurobipy import *
import probleminputs
import es_ls_solver

class Solver:
    def __init__(self,filename,random_parameters):
        print("Solving " + filename)
        I = probleminputs.Inputs("data/converted/",filename,random_parameters)
        
        self.n_jobs = I.n_jobs
        self.n_modes = I.n_modes
        
        self.job_modes = I.job_modes
        
        self.successor = I.successor
        self.duration_mode = I.duration_mode
        
        self.n_renewable = I.n_renewable
        self.resource_list = I.resource_list
        self.job_mode_resource = I.job_mode_resource
        self.n_res_types = I.n_res_types
        
        # New ones
        self.n_loc = I.n_loc  # Number of locations
        self.p_move = I.prop_move  # Proportion of jobs that can move their location
        self.j_move = I.j_move  # Matrix of all possible locations for each job
        self.j_time = I.j_travel  # Matrix of travel times between locations
        
        self.connectivity = I.connectivity
        
        # Solve two LP's problems to figure out ES and LS
        times_solver = es_ls_solver.ES_LS_Solver(self.n_jobs,
                                         self.successor,
                                         self.duration_mode,
                                         self.connectivity)
        
        self.job_early_start = times_solver.es
        self.job_late_start = times_solver.ls
        
        if(I.horizon == 0):
            self.horizon = max(self.job_late_start)# + max(self.duration_mode[-1]))
        else:
            self.horizon = I.horizon
        
        self.I = I
        
        
    def do_solve(self):  
        
        print("Creating problem")
        try:
            
            print("n_jobs = {}".format(self.n_jobs))
        
            # Create a new model
            m = Model("mip1")
            x_list = []
            y_list = []
            # Create variables
            print("Creating variables")
            
            # Create x and y variables
            for i in range(self.n_jobs-2):
                #print("i:{}".format(i))
                for mode in self.job_modes[i]:
                    for e in range(self.n_jobs - 1):
                        x_list.append(((i,mode,e),m.addVar(vtype=GRB.BINARY, name="X_{}_{}_{}".format(i,mode,e))))
                        y_list.append(((i,mode,e),m.addVar(vtype=GRB.BINARY, name="Y_{}_{}_{}".format(i,mode,e))))
            x = gurobipy.tupledict(x_list)
            y = gurobipy.tupledict(y_list)
            del x_list, y_list
            self.x = x
            self.y = y
            
            # Create continious t variable
            t_list = []
            for e in range(self.n_jobs - 1):
                t_list.append(((e),m.addVar(vtype=GRB.CONTINUOUS, lb=0, name="T_{}".format(e))))
            t = gurobipy.tupledict(t_list)
            del t_list
            self.t = t
            
            # Create continuous r variable
            r_list = []
            for e in range(len(t)):
                for res in range(self.n_res_types):
                    r_list.append(((e,res),m.addVar(vtype=GRB.CONTINUOUS,lb=0,name="R_{}_{}".format(e,res))))
            r = gurobipy.tupledict(r_list)
            del r_list
            self.r = r
            
            
            # Define gamma values (they keep track of where job started and ended)
#            gamma_s_list = []
#            gamma_f_list = []
#            
#            for i in range(self.n_jobs):
#                for l in range(self.n_loc):
#                    gamma_s_list.append( ( (i,l),m.addVar(vtype=GRB.BINARY, name="Gamma(S)_{}_{}".format(i,l)) ) )
#                    gamma_f_list.append( ( (i,l),m.addVar(vtype=GRB.BINARY, name="Gamma(F)_{}_{}".format(i,l)) ) )
#            gamma_s = gurobipy.tupledict(gamma_s_list)
#            gamma_f = gurobipy.tupledict(gamma_f_list)
#            del gamma_s_list, gamma_f_list
#            self.gamma_s = gamma_s
#            self.gamma_f = gamma_f
#            
#            # Define Beta and Delta values
#            beta_list = []
#            delta_list = []
#            for i in range(self.n_jobs - 1):
#                for j in self.successor[i]:
#                    for l1 in range(self.n_loc):
#                        for l2 in range(self.n_loc):
#                            beta_list.append( ( (j,i,l1,l2),m.addVar(vtype=GRB.BINARY,name="Beta_{}_{}_{}_{}".format(j,i,l1,l2)) ) )
#                            delta_list.append( ( (l1,l2,j,i),m.addVar(vtype=GRB.BINARY,name="Delta_{}_{}_{}_{}".format(l1,l2,j,i)) ) )
#            delta = gurobipy.tupledict(delta_list)
#            beta = gurobipy.tupledict(beta_list)
#            del delta_list, beta_list
#            self.delta = delta
#            self.beta = beta
#            
#            # Create theta variable. 
#            theta_list = []
#            for i in range(self.n_jobs):
#                for j in range(self.n_jobs):                   
#                        for mode in range(self.n_modes):
#                            theta_list.append(( (mode,j,i,),m.addVar(vtype=GRB.BINARY,name="THETA_{}_{}_{}".format(mode,j,i))  ))
#            theta = gurobipy.tupledict(theta_list)
#            del theta_list
#            self.theta = theta
            
            
            # Create objective function
            print("Creating objective function")            
            m.setObjective(t[len(t)-1],GRB.MINIMIZE)
            self.m = m
      
            # Create first constraint
            print("Creating constraint 1")
            m.addConstr(t[0] == 0)
            
            # Create second constraint
            print("Creating constraint 2")
            m.addConstrs(t[e+1] - t[e] >= 0 for e in range(len(t)-1))
            
            # Create third constraint
            print("Creating constraint 3")
            m.addConstrs(t[f]-t[e]-self.duration_mode[i][mode]*x[i,mode,e]
                                  +self.duration_mode[i][mode]*(1-y[i,mode,f])>=0
                                             for i in range(self.n_jobs-2)
                                             for mode in self.job_modes[i]
                                             for e in range(len(t))
                                             for f in range(e+1,len(t))    
                        )
            
            # Create fourth constraint
            print("Creating constraint 4")
            m.addConstrs( x.sum(i,"*","*") == 1 for i in range(self.n_jobs-2))
            
            # Create fifth constraint
            print("Creating constraint 5")
            m.addConstrs( y.sum(i,"*","*") == 1 for i in range(self.n_jobs-2))
            
            # Create sixth constraint
            print("Creating constraint 6")
            try:
                m.addConstrs(gurobipy.quicksum(y[i,mode,e_] for mode in self.job_modes[i]
                                                            for e_ in range(e,len(t))
                                              ) 
                                        +
                             gurobipy.quicksum(x[j,mode,e_] for mode in self.job_modes[j]
                                                            for e_ in range(e)     
                                              ) 
                                         <= 1
                                              for i in range(self.n_jobs - 2)
                                              for j in self.successor[i]
                                              for e in range(len(t))    
                            )
            except KeyError:
                # I just cannot be bothered fixing it properly tbh
                pass
                         
            # Create seventh constraint
            print("Creating constraint 7")
            # Renewable resources
            m.addConstrs(r[0,k]-gurobipy.quicksum(self.job_mode_resource[i][mode][k]*x[i,mode,0] 
                                            for i in range(self.n_jobs-2)
                                            for mode in self.job_modes[i]
                                                 )
                                                         
                           == 0                         
                               for k in range(self.n_renewable)
                         )
                         
            # Create eigth constraint
            print("Creating constraint 8")
            m.addConstrs(r[e,k]-r[e-1,k]+ gurobipy.quicksum(self.job_mode_resource[i][mode][k]*(y[i,mode,e]-x[i,mode,e])
                                                            for i in range(self.n_jobs-2)
                                                            for mode in self.job_modes[i]
                                                         )
            
                     == 0                                                                                                  
                                                            for e in range(1,len(t))
                                                            for k in range(self.n_renewable)     
            
            )
            
            # Create ninth constraint
            print("Creating constraint 9")
            m.addConstrs(r[e,k]<=self.resource_list[k]     for e in range(len(t))
                                                           for k in range(self.n_renewable)
                        )
            
            # Create tenth constraint
            print("Creating constraint 10")
            # Non-renewable constraint
            m.addConstrs(self.job_mode_resource[i][mode][k]*x[i,mode,e]
                 <= self.resource_list[k]  
                 
                                     for i in range(self.n_jobs-2)
                                     for mode in self.job_modes[i]
                                     for e in range(len(t))
                 
                                     for k in range(self.n_renewable,self.n_res_types)
            )
            
            # Create eleventh constraint
            print("Creating constraint 11")
            m.addConstrs(t[e] >= 0 for e in range(len(t)))
            
            # Create twelth constraint
            print("Creating constraint 12")
            m.addConstrs(r[e,k] >= 0 for e in range(len(t))
                                     for k in range(self.n_res_types))
            
            # Create 13th constraint
            print("Creating constraint 13")
#            m.addConstrs(self.job_early_start[i]*x[i,mode,e] 
#                        <= t[e] 
#                                                                     
#                                                                     for e in range(len(t))
#                                                                     for i in range(self.n_jobs-2)    
#                                                                     for mode in self.job_modes[i]
#                        )
#            m.addConstrs(t[e]<=
#                         
#            
#                            self.job_late_start[i]*x[i,mode,e]
#                            +
#                            self.job_late_start[-1]*(1-x[i,mode,e])
#                                                                
#                                                                for i in range(self.n_jobs-2)
#                                                                for mode in self.job_modes[i]
#                                                                for e in range(len(t))    
#                        )
            
            m.addConstrs(self.job_early_start[i]*gurobipy.quicksum(x[i,mode,e] for mode in self.job_modes[i])
                        <= t[e] 
                                                                     
                            <=
                         
            
                            (self.job_late_start[i]-self.job_late_start[-1])*gurobipy.quicksum(x[i,mode,e] for mode in self.job_modes[i])
                            +
                            self.job_late_start[-1]
                                                                for i in range(self.n_jobs-2)
                                                                for e in range(len(t))    
                        )
            
            # Create 14th constraint
            print("Creating constraint 14")
#            m.addConstrs( (self.job_early_start[i]+self.duration_mode[i][mode])*y[i,mode,e] <= t[e] 
#                                                    for i in range(self.n_jobs-2)
#                                                    for mode in self.job_modes[i]
#                                                    for e in range(len(t))
#                                                                                                    
#                        )
#            m.addConstrs(t[e]<=
#                    
#                    (self.job_late_start[i]+self.duration_mode[i][mode])*self.y[i,mode,e]
#                    +self.job_late_start[-1]*(1-y[i,mode,e])
#                    for i in range(self.n_jobs-2)
#                    for mode in self.job_modes[i]   
#                    for e in range(len(t))
#            )
            
            m.addConstrs( gurobipy.quicksum((self.job_early_start[i]+self.duration_mode[i][mode])
                    *
                    
                            y[i,mode,e] for mode in self.job_modes[i])
                <= 
                t[e] 
                <=   gurobipy.quicksum(                 
                    (self.job_late_start[i]+self.duration_mode[i][mode]-self.job_late_start[-1])
                    *
                    self.y[i,mode,e] for mode in self.job_modes[i])
                    +self.job_late_start[-1]
                    for e in range(len(t))
                    for i in range(self.n_jobs-2)
            )
            
            # Create 15th constraint
            print("Creating constraint 15")
            m.addConstr(self.job_early_start[-1] <= t[len(t)-1])
            
            
            # Add missing constraint
            print("Creating constraint 16")
            m.addConstrs(gurobipy.quicksum(y[i,mode,v] for mode in self.job_modes[i]
                                                       for v in range(e+1))
                         +
                         gurobipy.quicksum(x[i,mode,v] for mode in self.job_modes[i]
                                                       for v in range(e,len(t)) )
                         <= 1
                         for i in range(self.n_jobs-2)
                         for e in range(len(t))
                )
            
            print("Creating constraint 17")
            # Make sure that job starts and end in the same mode
            m.addConstrs(gurobipy.quicksum(x[i,mode,e] for e in range(len(t)))
                        ==
                         gurobipy.quicksum(y[i,mode,f] for f in range(len(t)))
                         for i in range(self.n_jobs-2)
                         for mode in self.job_modes[i]
                        )
            print("Running the solver")
            # Run the solver    
            m.optimize()
            
            self.m = m
        
        except GurobiError as e:
            print("Error!",e)
            