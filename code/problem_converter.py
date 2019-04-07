#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""


Script to convert .mm files into 3 files for my solver
"""

class File_converter:
    def __init__(self,filename,filetype):
        #filename = "c154_3"
        # Start by opening the file
        with open("data/" + filename + "."+filetype,"r") as f:
            content = f.readlines()
        content = [x.strip() for x in content]
        
        reading_precedence = False
        reading_durations = False
        reading_resources = False
        
        horizon = 0
        
        # Go through the file to find relevant information
        for line in content:
            # Find number of jobs
            if("jobs (incl." in line or "jobs  (incl." in line):
                startPos = line.index(":")
                n_jobs = eval(line[startPos + 1:])
            # Find horizon value
            if("horizon " in line):
                startPos = line.index(":")
                horizon = eval(line[startPos + 1:])
            # Find the number of renewable resources
            if("- renewable" in line):
                startPos = line.index(":")
                endPos = line[startPos:].index("R")
                n_renewable = eval(line[startPos + 1:startPos + endPos])
            # Find the number of non-renewable resources
            if("- nonrenewable" in line):
                startPos = line.index(":")
                endPos = line[startPos:].index("N")
                n_nonrenewable = eval(line[startPos + 1:startPos + endPos])
            # Find start of the precedence table
            if("PRECEDENCE RELATIONS:" in line):
                reading_precedence = True
                precedence_table = []
                continue
            # **** indicates the end of table
            if("****" in line):
                reading_precedence = False
                reading_durations = False
                reading_resources = False
            # Append all of the lines into one list
            if(reading_precedence):
                precedence_table.append(line)
             # Find start of the duratios table
            if("REQUESTS/DURATIONS" in line):
                reading_durations = True
                durations_table = []
                continue
            # Append al of the lines into the list
            if(reading_durations):
                durations_table.append(line)
            # If the start of Resources table
            if("RESOURCEAVAILABILITIES" in line or "RESOURCE AVAILABILITIES" in line):
                reading_resources = True
                resources_table = []
                continue
            # Append al of the lines into the list
            if(reading_resources):
                resources_table.append(line)
                
        # Now I should have all of the tables in lists
        # Have to clean them up a bit to export as .csv files
        
        # Start with the precedence table
        export_precedence = []
        for row in precedence_table:
            export_precedence.append(",".join(row.split())+"\n")
            
        
        # Now do durations
        export_durations = []
        # Need to add value in the first column 
        durations_table2 = durations_table
        norm_len = len(durations_table[3])
        num = 1
        max_len = list(map(int, durations_table[2].split()))
        for i in range(0,len(durations_table2)):
            if(i > 2):
                x = list(map(int, durations_table[i].split()))
                #if(filename == "J5036_5"):                    
                #    print(len(x),len(max_len),durations_table[i])
                    #print(durations_table2[i],len(durations_table[i]),norm_len)
                if(len(x) < len(max_len)):
                    durations_table2[i] = str(num) + " " + durations_table2[i]
                else:
                    num = num + 1
        for row in durations_table2:
            export_durations.append(",".join(row.split())+"\n")
        # Remove the 2nd line
        export_durations.pop(1)
    
            
        # Finally with Resources
        export_resources = []
        for row in resources_table:
            export_resources.append(",".join(row.split())+"\n")
            
        # And in conclusion, write these tables to files
        with open("data/converted/"+ filename + "_precedence.csv","w") as f:
            for item in export_precedence:
                f.write(item)
        with open("data/converted/"+ filename + "_durations.csv","w") as f:
            for item in export_durations:
                f.write(item)
        with open("data/converted/"+ filename + "_resources.csv","w") as f:
            for item in export_resources:
                f.write(item)
        with(open("data/converted/" + filename + "_info.csv","w")) as f:
            f.write(str(n_jobs) + "," + str(horizon) + "," + str(n_renewable) + ","
                        + str(n_nonrenewable) + "\n")