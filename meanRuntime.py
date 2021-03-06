#!/usr/bin/env python
# -*- coding: utf8 -*-

# My imports
from __future__ import division
import numpy as np
from datetime import datetime as d
import matplotlib.pyplot as plt
plt.rcParams['xtick.direction'] = 'in'
plt.rcParams['ytick.direction'] = 'in'
plt.rcParams['axes.spines.right'] = False
plt.rcParams['axes.spines.top'] = False
plt.rcParams['axes.linewidth'] = 2
plt.rcParams['xtick.major.width'] = 2
plt.rcParams['ytick.major.width'] = 2

def getTimeStamp(line):
    """Get the time stamp from the logfile"""
    line = line.split()
    ymd = map(int, line[0].split('-'))
    line = line[1].split(':')
    h = int(line[0])
    m = int(line[1])
    line = line[-1].split(',')
    s = int(line[0])
    ms = int(line[1])

    return d(*ymd, hour=h, minute=m, second=s, microsecond=ms)


if __name__ == '__main__':
    startTimes = []
    endTimes = []
    with open('captain.log', 'r') as lines:
        for line in lines:
            if 'Starting the initial minimization routine' in line:
                startTimes.append(line.strip())
            elif 'Final parameters' in line:
                endTimes.append(line.strip())

    while len(startTimes) > len(endTimes):
        startTimes.pop(-1)

    startTimes = map(getTimeStamp, startTimes)
    endTimes = map(getTimeStamp, endTimes)

    dt = np.array([(e-s).total_seconds() for e, s in zip(endTimes, startTimes)])

    print 'Median runtime: %.2fs' % np.median(dt)
    print '  Mean runtime: %.2fs' % np.mean(dt)

    plt.hist(dt, bins=20)
    plt.xlabel('Runtime [s]')
    plt.show()
