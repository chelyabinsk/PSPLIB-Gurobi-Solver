# -*- coding: utf-8 -*-
"""

Final script that evaluates the perfomance of the formulation

"""

from os import walk
from os.path import isfile, join
import os
import problem_converter as converter
import problem_ddt_DYNAMIC_ALL as problem_ddt_DYNAMIC_ALL
import problem_ddt_DYNAMIC_ALL_ESLS as problem_ddt_DYNAMIC_ALL_ESLS
import problem_ddt_DYNAMIC_ALL_ESLS_NON_NAIVE as problem_ddt_DYNAMIC_ALL_ESLS_NON_NAIVE
import problem_see_clean as problem_see_clean

class Tester():
    def __init__(self):
        # Convert all of the input files
        files = self.convert_files("mm")
        
        # Number of locations to be tested
        n_loc = [7]
        prob_move = [0.25,0.5,0.75,1]
        sample_size = 0 + 1
        
#         Create all of the files
        for n in n_loc:
            for prob in prob_move:
                tmp_filename = "{} {} .txt".format(n,prob)
                # Create a text file
                file = open("outputs/"+tmp_filename, "w") 
                file.close()

        c = 0
        startval = 9
        for filename in files:     
#            c += 1
#            if(c > startval):
#                break
#            if(c < startval):
#                continue
            
            
            for n in n_loc:
                for prob in prob_move:
                    for sample_n in range(sample_size):
                        tmp_filename = "{} {} .txt".format(n,prob)
                        
                        #print("{} {} {}".format(n,prob,filename))
                        
#                        obj2 = problem_ddt_DYNAMIC_ALL.Solver(filename,(n,prob))
                        obj2 = problem_ddt_DYNAMIC_ALL_ESLS.Solver(filename,(n,prob),sample_n)
#                        obj2 = problem_see_clean.Solver(filename,(n,prob))
#                        obj2 = problem_ddt_DYNAMIC_ALL_ESLS_NON_NAIVE.Solver(filename,(n,prob))
                        obj2.do_solve()
                        
                        self.obj2 = obj2
                                               
                        can_solve = True
                        
                        try:
                            if(obj2.job_early_start[-1] != obj2.m.getObjective().getValue()):
                                #break
                                pass
                            else:
                                #break
                                pass
                        except:
                            can_solve = False
                            print("no solution")
                            #break
                            
                        # Append the solution to the log
                        with open("outputs/"+tmp_filename,"a") as f:
                            if(can_solve):
                                f.write("{} obj={} t={}\n".format(filename,obj2.m.getObjective().getValue(),obj2.m.RunTime))
                            else:
                                f.write("{} False\n".format(filename))
                        if(n == 1):
                            break            
                    if(n == 1):
                        break
#                        break
#                    break
                
#                break
#            break

        
    def convert_files(self,extension):
        onlyfiles = [f for f in os.listdir("data") if isfile(join("data",f))]
        
        filetype = extension
        
        files = [] 
        for file in onlyfiles:
            if(file[-2:] == filetype):
                filename = file[:-3]
                files.append(filename)
                c = converter.File_converter(filename,filetype)
                
        return files
    
    def share_val(self):
        return self.obj2
    
t = Tester()

def times():
    for x in t.share_val().x:
        if(t.share_val().x[x].x != 0):
            print(t.share_val().x[x])
        if(t.share_val().y[x].x != 0):
            print(t.share_val().y[x])
    t.share_val().t
            