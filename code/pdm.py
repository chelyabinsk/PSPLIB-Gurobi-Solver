#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Oct 19 18:43:54 2018

@author: pirate
"""

# Precedence Diagram Method (PDM)
# https://gist.github.com/vinzBad/497cd98fbc61b1afd50e

class Process(object):
    def __init__(self, name, duration, next_processes=[]):
        self.name = name
        self.duration = duration
        self.previous_processes = []
        self.next_processes = next_processes
        for process in next_processes:
            process.previous_processes.append(self)

    def earliest_starting_point(self):
        assert isinstance(self.previous_processes, list)
        #print("Computing earliest starting point of {0}...".format(self.name))
         # return zero when there are no previous processes
        if len(self.previous_processes) == 0:
            return 0
        # return the latest of the earliest ending points of the previous processes
        return max(self.previous_processes, key=lambda p: p.earliest_ending_point()).earliest_ending_point()

    def earliest_ending_point(self):
        #print("Computing earliest ending point of {0}...".format(self.name))
        # the earliest ending point is the earliest starting point plus the duration
        earliest_ending_point = self.earliest_starting_point() + self.duration
        #print("The earliest ending point of {0} is {1}".format(self.name, earliest_ending_point))
        return earliest_ending_point

    def latest_starting_point(self):
        latest_starting_point = self.latest_ending_point() - self.duration
        return latest_starting_point

    def latest_ending_point(self):
        assert isinstance(self.next_processes, list)
        if len(self.next_processes) == 0:
            return self.earliest_ending_point()
        return min(self.next_processes, key=lambda p: p.latest_starting_point()).latest_starting_point()

    def free_buffer(self):
        raise NotImplementedError(":P")

    def total_buffer(self):
        raise NotImplementedError(":P")

    def __repr__(self):
        return "{0}: {1}, Prev: {2} Next: {3}".format(self.name,
                                                      self.duration,
                                                      [p.name for p in self.previous_processes],
                                                      [p.name for p in self.next_processes])


#d = Process("D", 5)
#c = Process("C", 4, [d])
#b = Process("B", 2, [d])
#a = Process("A", 3, [b,c])