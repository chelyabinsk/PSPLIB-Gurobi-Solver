#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""


http://mmlib.eu/download.php

DT model with dynamic locations and dynamic modes

This includes a naive extension

+ Early and Late start times

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
        
            # Create a new model
            m = Model("mip1")
            x_list = []
            y_list = []
            # Create variables
            print("Creating variables")
            for i in range(self.n_jobs):
                #print("i:{}".format(i))
                for mode in self.job_modes[i]:
                    for t in range(self.horizon+1):
                        x_list.append(((i,mode,t),m.addVar(vtype=GRB.BINARY, name="X_{}_{}_{}".format(i,mode,t))))
                        y_list.append(((i,mode,t),m.addVar(vtype=GRB.BINARY, name="Y_{}_{}_{}".format(i,mode,t))))
            x = gurobipy.tupledict(x_list)
            y = gurobipy.tupledict(y_list)
            del x_list, y_list
            self.x = x
            self.y = y
            
            # Define gamma values (they keep track of where job started and ended)
            gamma_s_list = []
            gamma_f_list = []
            
            for i in range(self.n_jobs):
                for l in range(self.n_loc):
                    gamma_s_list.append( ( (i,l),m.addVar(vtype=GRB.BINARY, name="Gamma(S)_{}_{}".format(i,l)) ) )
                    gamma_f_list.append( ( (i,l),m.addVar(vtype=GRB.BINARY, name="Gamma(F)_{}_{}".format(i,l)) ) )
            gamma_s = gurobipy.tupledict(gamma_s_list)
            gamma_f = gurobipy.tupledict(gamma_f_list)
            del gamma_s_list, gamma_f_list
            self.gamma_s = gamma_s
            self.gamma_f = gamma_f
            
            # Define Beta and Delta values
            beta_list = []
            delta_list = []
            for i in range(self.n_jobs - 1):
                for j in self.successor[i]:
                    for l1 in range(self.n_loc):
                        for l2 in range(self.n_loc):
                            beta_list.append( ( (j,i,l1,l2),m.addVar(vtype=GRB.BINARY,name="Beta_{}_{}_{}_{}".format(j,i,l1,l2)) ) )
                            delta_list.append( ( (l1,l2,j,i),m.addVar(vtype=GRB.BINARY,name="Delta_{}_{}_{}_{}".format(l1,l2,j,i)) ) )
            delta = gurobipy.tupledict(delta_list)
#            beta = gurobipy.tupledict(beta_list)
            del delta_list, beta_list
            self.delta = delta
#            self.beta = beta
            
            # Create theta variable. 
#            theta_list = []
#            for i in range(self.n_jobs):
#                for j in range(self.n_jobs):                   
#                        for mode in range(self.n_modes):
#                            theta_list.append(( (mode,j,i,),m.addVar(vtype=GRB.BINARY,name="THETA_{}_{}_{}".format(mode,j,i))  ))
#            theta = gurobipy.tupledict(theta_list)
#            del theta_list
#            self.theta = theta
            
#            # Create objective function
            print("Creating objective function")            
            m.setObjective((gurobipy.quicksum(t*x[self.n_jobs-1,mode,t] for mode in self.job_modes[self.n_jobs-1]
                                                                        
                                                                        for t in range(self.job_early_start[-1],self.horizon + 1)))
                                                    ,GRB.MINIMIZE)
            
            # Construct first constraint
            print("Adding constraint 1")
            for i in range(self.n_jobs-1):
                for j in self.successor[i]:
                    if(i != 0 and j != self.n_jobs - 1):
                        m.addConstr(gurobipy.quicksum(t*x[j,mode,t] for t in range(self.job_early_start[j],self.horizon+1)
                                                                for mode in self.job_modes[j])
                             - gurobipy.quicksum((t + self.duration_mode[i][mode])*x[i,mode,t]
                                                 for t in range(self.job_early_start[i],self.horizon+1)
                                                 for mode in self.job_modes[i]
                                                 )
                            >=  
                               gurobipy.quicksum(self.j_time[l1][l2]*delta[l1,l2,j,i]
                                                  for l1 in range(self.n_loc)
                                                  for l2 in range(self.n_loc)
                                                )
                              )
                    else:
                        m.addConstr(gurobipy.quicksum(t*x[j,mode,t] for t in range(self.job_early_start[j],self.horizon+1)
                                                                for mode in self.job_modes[j])
                            >=  gurobipy.quicksum((t + self.duration_mode[i][mode])*x[i,mode,t]
                                                                                                 for t in range(self.job_early_start[i],self.horizon+1)
                                                                                                 for mode in self.job_modes[i])
                              )

#             Construct constraint 2 (Renewable resources)
            print("Adding constraint 2.R")
            m.addConstrs(
gurobipy.quicksum((self.job_mode_resource[i][mode][res]*x[i,mode,tau] for i in range(1,self.n_jobs-1)
                                                                      for mode in self.job_modes[i]
                                                                      for tau in range(max(0,t-self.duration_mode[i][mode]+1),t+1)
                                                                      )
) <= self.resource_list[res] for t in range(self.horizon + 1)
                             for res in range(self.n_renewable)
)                
#             Construct constraint 2 (Non-renewable resources)
            print("Adding constraint 2.NR")
            m.addConstrs(
gurobipy.quicksum((self.job_mode_resource[i][mode][res]*x[i,mode,tau] for i in range(1,self.n_jobs-1)
                                                                      for mode in self.job_modes[i]
                                                                      for tau in range(self.job_early_start[i],self.horizon+1)
                                                                      )
) <= self.resource_list[res] 
                             for res in range(self.n_renewable,self.n_res_types)
)                

            # Construct third constraint
            print("Adding constraint 3")
            m.addConstrs( x.sum(i,"*","*") == 1 for i in range(self.n_jobs))          
            
            
            # # # # # # # # # # #
            #                   #
            # Extra constraints #
            #                   #
            # # # # # # # # # # #
            
            
            # Give variable y its value
            m.addConstrs(x[i,mode,t]  - y[i,mode,t+self.duration_mode[i][mode]] == 0
                                                                                                for i in range(self.n_jobs)
                                                                                                for mode in self.job_modes[i]
                                                                                                for t in range(self.job_early_start[i],self.horizon - self.duration_mode[i][mode])
                                                                                                        
                        )
                          
            
            # Second constraint of the further extensions
            m.addConstrs(gurobipy.quicksum(x[i,mode,t]  for mode in self.job_modes[i]
                                                        for t in range(self.job_early_start[i],self.horizon - self.duration_mode[i][mode])
                ) ==     gurobipy.quicksum(gamma_s[i,l] for l in range(self.n_loc))  for i in range(self.n_jobs))
            # Third constraint of the further extensions
            m.addConstrs(gurobipy.quicksum(y[i,mode,t]  for mode in self.job_modes[i]
                                                        for t in range(self.job_early_start[i],self.horizon - self.duration_mode[i][mode])
                ) ==     gurobipy.quicksum(gamma_f[i,l] for l in range(self.n_loc))  for i in range(self.n_jobs))
            # Fourth constraint of the further extensions
            m.addConstrs(gamma_s[i,l] == gamma_f[i,l]   for i in range(self.n_jobs)
                                                        for l in range(self.n_loc))
            
            # Force some of the rooms to be unavailable
            for i in range(len(self.j_move)):
                for loc in range(len(self.j_move[i])):
                    m.addConstr(gamma_f[i,loc] <= self.j_move[i][loc])
            
            
#            m.addConstrs(                    
#                    
#                        gurobipy.quicksum(t*x[j,mode,t] for t in range(self.job_early_start[j],self.horizon+1)
#                                                                for mode in self.job_modes[j])
#                         - gurobipy.quicksum((t + self.duration_mode[i][mode])*x[i,mode,t]
#                                     for t in range(self.job_early_start[i],self.horizon+1)
#                                     for mode in self.job_modes[i]
#                                 )
#                    
##                        gurobipy.quicksum(
##                        self.j_time[l1,l2]*
##                        delta[l1,l2,j,i]
##                        for l1 in range(self.n_loc)
##                        for l2 in range(self.n_loc)
##                        )
#                        
#                        >=
#                        
#                        gurobipy.quicksum(
#                        self.j_time[l1,l2] *
#                        gurobipy.quicksum(
#                        gurobipy.quicksum(x[i,mode,t] + y[i,mode,t+self.duration_mode[i][mode]] 
#                                for t in range(self.job_early_start[i],self.horizon - self.duration_mode[i][mode])) 
#                                    -1 for mode in self.job_modes[i])-2+gamma_f[j,l1]+gamma_s[i,l2]
#                        for l1 in range(self.n_loc)
#                        for l2 in range(self.n_loc)
#                        )
#                         
#                         
#                        for i in range(self.n_jobs-1)
#                        for j in self.successor[i]
#            )
            
            self.m = m
            
            m.Params.timeLimit = 5*60  # If code doesn't solve after 5 mins give up

            
            print("Running the solver")
            # Run the solver    
            m.optimize()
            
            self.m = m
        
        except GurobiError:
            print("Error!")
            