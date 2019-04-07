#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pdm
from criticalpath import Node
import csv
from numpy import mean as mean
#import numpy as np
#from scipy.sparse import csr_matrix
#from scipy.sparse.csgraph import dijkstra
from topolsort import Other_Sort as ts
import random_location_data as loc_gen

class Inputs():
    def __init__(self,path,filename,random_parameters,run_num=0):
        self.path = path
        self.filename = filename
        self.run_num = run_num
        
        self.read_durations()
        self.read_precedence()
        self.read_resources()
        self.read_info()
        self.calculate_job_mode_resource()
        self.calculate_min_time_between_i_and_j()
        self.calculate_max_planning_horizon()
        self.calculate_precedence()
        #self.early_start_finish_pdm()
        #self.early_start_finish_activity_on_nodes()
        self.connectivity = self.find_following_jobs()

        self.n_loc,self.prop_move = random_parameters
        # Number of locations
        # Proportion of jobs that can move their location        
        
        self.job_locations()
        
    def read_durations(self):
        # Read the csv input file in
        with open(self.path+self.filename + "_durations.csv","r") as f:
            reader = csv.reader(f)
            input_list = list(reader)
            
        # Exclue the first (column names) row
        self.data_list = input_list[1:]
        
        # Find number of row
        n_rows = len(self.data_list)
        # find number of jobs
        self.n_jobs = int(self.data_list[n_rows-1][0])
                
        # find max number of modes
        self.n_modes = 0
        for row in self.data_list:
            if(int(row[1]) > self.n_modes):
                self.n_modes = int(row[1])
                
    def read_precedence(self):
        # Start by reading the self.successor data
        with open(self.path+self.filename+"_precedence.csv","r") as f:
            reader = csv.reader(f)
            input_list = list(reader)
        # Drop the first (column names) row
        self.relations_table = input_list[1:]
    
    def read_resources(self):
        # Read in file of max availabilities
        with open(self.path+self.filename+"_resources.csv") as f:
            reader = csv.reader(f)
            input_list = list(reader)
            
        # Exclue the first (column names) row
        self.resource_list = input_list[1:][0]
        tmp = []
        for i in self.resource_list:
            tmp.append(eval(i))
        self.resource_list = tmp
        self.n_res_types = len(self.resource_list)
        
        # Go through the table to build an array of self.successor
        self.successor = []
        for row in self.relations_table:
            tmp_row = []
            
            if(int(row[2]) != 0):
                for i in range(3,len(row)):
                    if(row[i] != ""):
                        tmp_row.append(int(row[i])-1)
                self.successor.append(tmp_row)
                
    def read_info(self):
        with open(self.path+self.filename+"_info.csv") as f:
            reader = csv.reader(f)
            input_list = list(reader)        
        self.horizon = int(input_list[0][1])
        self.n_renewable = int(input_list[0][2])
        self.n_nonrenewable = int(input_list[0][3])
    
    def calculate_job_mode_resource(self):
        # 1) find durations for each job with mode
        # 2) Find modes for each job
        # 3) Create a list of resource required for each job + mode
        self.job_mode_resource = [[[0]*self.n_res_types]]
        job_nr = 0
        self.duration_mode = [[0]]  # My d^{job}_{i,m} variable
        self.job_modes = [[0]]
        new_job = False
        for row in self.data_list:
            if(job_nr != int(row[0])):
                job_nr = int(row[0])
                new_job = True
            else:
                new_job = False
            if(new_job):
                tmp_dur = [int(row[2])]  # List of durations for diferent modes
                tmp_mode = [int(row[1])-1]  # List of modes for different modes (?)
                tmp_res = [row[3:]]  # List of resources required for each mode
                if(job_nr > 1):
                    #print(tmp_dur,tmp_mode,tmp_res)
                    self.duration_mode.append(tmp_dur)
                    self.job_modes.append(tmp_mode)
                    self.job_mode_resource.append(tmp_res)
            else:
                tmp_dur.append(int(row[2]))
                tmp_mode.append(int(row[1])-1)
                tmp_res.append(row[3:])
                
        # Convert string entries to int
        self.job_mode_resource = [[[int(z) for z in y] for y in x] for x in self.job_mode_resource]

    def calculate_min_time_between_i_and_j(self):
        # find d^{min}_{i,j} which is basically just stores minumum time
        # difference between jobs i and j
        self.min_time_between_i_and_j = [[-1 for col in range(self.n_jobs)] for row in range(self.n_jobs)]
        # Say that -1 is missing
        for i in range(self.n_jobs - 1):
            for j in (self.successor[i]):
                self.min_time_between_i_and_j[i][j] = min(self.duration_mode[i])
                #print(i,j,min(self.duration_mode[i]))

    def calculate_max_planning_horizon(self):
        # find maximum planning horizon
        # TODO: Improve this
#        self.max_t = 0
#        for row in self.data_list:
#            self.max_t = self.max_t + int(row[2])    
#        self.times_list = list(range(0,self.max_t+2))  # +2 because I need t=0 and t=(n+1)
#        
        # Say that -1 is missing
        tmp = 0
        for i in range(self.n_jobs - 1):
                tmp += int(max(self.duration_mode[i]))
        self.max_t = tmp 
        
        # self.successor[i]
        # self.duration_mode[i,m]
        
    def calculate_precedence(self):
        # Find precedence relation by converting self.successor
        self.precedence = []
        for i in range(self.n_jobs):
            pos = (self.n_jobs - i - 1)
            tmp = []
            for j in range(self.n_jobs - 1):
                if(pos in self.successor[j]):
                    #print(pos,j,self.successor[j])
                    tmp.append(j)
            self.precedence.append(tmp)
        self.precedence.reverse()
        
    def early_start_finish_pdm(self):
        print("Creating linked list pdm, min")
        object_reference = []
        for i in range(self.n_jobs):
            pos = (self.n_jobs - i - 1)
        
            # If on last node (in my case it's the first case, as I'm going backwards)
            if(pos == self.n_jobs - 1):
                self.pdm_list = [pdm.Process(pos,min(self.duration_mode[pos]))]
                object_reference = [pos]
            else:
                tmp_list = []
                for j in self.successor[pos]:
                    print(self.successor[pos],pos,j)
                    tmp_list.append(self.pdm_list[object_reference.index(j)])
                    if(not pos in object_reference):
                        object_reference.append(pos)
                self.pdm_list.append(pdm.Process(pos,min(self.duration_mode[pos]),tmp_list))
            
        # Use this list to figure out latest and earliest start times
        self.pdm_list.reverse()
        
        # Initialise the activity on note object
        self.p = Node('project')
        
        # Initialise list of objects for critical_path object
        self.object_list = []
        
        print("Create list for critical path")
        for job in self.pdm_list:
            self.p.add(Node(job.name,duration=job.duration,lag=0))
        
        print("Creating links")
        for job in self.pdm_list:
            for i in job.next_processes:
                self.p.link(job.name,i.name)
        self.p.update_all()
                
        # Pre calculate earliest start time
        job_early_start = []
        for i in range(len(self.pdm_list)):
            job_early_start.append(self.p.get_or_create_node(i).es)
        
        
        print("Creating linked list pdm, max")
        object_reference = []
        for i in range(self.n_jobs):
            pos = (self.n_jobs - i - 1)
        
            # If on last node (in my case it's the first case, as I'm going backwards)
            if(pos == self.n_jobs - 1):
                self.pdm_list = [pdm.Process(pos,min(self.duration_mode[pos]))]
                object_reference = [pos]
            else:
                tmp_list = []
                for j in self.successor[pos]:
                    tmp_list.append(self.pdm_list[object_reference.index(j)])
                    if(not pos in object_reference):
                        object_reference.append(pos)
                self.pdm_list.append(pdm.Process(pos,min(self.duration_mode[pos]),tmp_list))
            
        # Use this list to figure out latest and earliest start times
        self.pdm_list.reverse()
        
    def early_start_finish_activity_on_nodes(self):
        # Initialise the activity on note object
        self.p = Node('project')
        
        # Initialise list of objects for critical_path object
        self.object_list = []
        
        print("Create list for critical path")
        for job in self.pdm_list:
            self.p.add(Node(job.name,duration=job.duration,lag=0))
        
        print("Creating links")
        for job in self.pdm_list:
            for i in job.next_processes:
                self.p.link(job.name,i.name)
        self.p.update_all()
                
        # Pre calculate earliest start time
        job_late_start = []
        for i in range(len(self.pdm_list)):
            job_late_start.append(self.p.get_or_create_node(i).ls)
            
         # Pre calculate earliest start time
        job_early_start = []
        for i in range(len(self.pdm_list)):
            job_early_start.append(self.p.get_or_create_node(i).es)
            
        # Workout early-late start times
        early_start = [0]*self.n_jobs

        tmp = 0        
        for j in self.duration_mode:
            tmp += max(j)
        late_start = [tmp]*self.n_jobs
        
        # How do I workout this???
        job_late_start = [0,0,3,7]
                
        #job_early_start = early_start
        #job_late_start = late_start
            
        self.ls = job_late_start
        self.es = job_early_start
        
    def find_following_jobs(self):
        # Using code I found online, create a topological sort
        top_sort = ts(self.successor)
        return(top_sort.create_dic())
#        for i in range(self.n_jobs-1):
#            for j in self.successor[i]:
#                top_sort.addEdge(i,j)
#        return(top_sort.topologicalSort())
        
    def job_locations(self):
        n_loc = self.n_loc
        n_jobs = self.n_jobs 
        move_frac = self.prop_move  # Proportion of jobs that have more than 1 location
        travel_bounds = (1,1)  # Range of travel times
        
        rand_loc = loc_gen.Location_Generator(n_loc,n_jobs,move_frac,travel_bounds,self.run_num)
        
        # Create a matrix of data but for now use fixed one
        self.j_move = rand_loc.make_pos_data()
        
        # Create matrix of travel times between locations
        self.j_travel = rand_loc.make_travel_times_data()