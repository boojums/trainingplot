#! /usr/bin/env python

import shutil
import datetime as dt

import mechanize
import csv
import matplotlib.pyplot as plt
import numpy as np

username = 'set me'
password = 'set me'

# TODO: use pandas...
# TODO: consider using Counter class from collections to count neat stats 
# TODO: small sql db for learning/easy querying?

# http://attackpoint.org/printtraining.jsp?userid=470&from-month=11&from-day=14&from-year=2014&to-month=11&to-day=14&to-year=2014&isplan=0&outtype=csv
# http://attackpoint.org/printtraining.jsp?userid=470&isplan=0&outtype=csv

def main():

    get_data()

    filename = 'test.csv'
    with open(filename, 'r') as f:
        logreader = csv.DictReader(f)
        log = [row for row in logreader]

    # Make entry dates play nice with datetime
    for entry in log:
        entry['date'] = dt.datetime.strptime(entry['date'], '%Y-%m-%d')

    week = dt.timedelta(days=7)
    start = dt.datetime(2014, 9, 16)
    end = dt.datetime(2014, 11, 16)

    runpoints = []
    skipoints = []
    runactivities = ('Running', 'Orienteering')
    skiactivities = ('XC Skiing', 'Ski Orienteering')
    var = 'distance(km)'
    #var = 'controls'
    for day in datespan(start, end):
        values = subset(log, var, runactivities, day, day+week)
        distance = sum(values)
        runpoints.append((day, distance))

        values = subset(log, var, skiactivities, day, day+week)
        distance = sum(values)
        skipoints.append((day, distance))

    plt.xkcd()
    fig, ax = plt.subplots(1)

    x, y = zip(*runpoints)
    #ax.scatter(x, y)
    #x, y = zip(*skipoints)
    #ax.scatter(x, y, color='black')
    plt.title('Weekly km, orienteering + running')
    #plt.ylim(ymin=0)

    rects1 = ax.bar(x, y, 3, color='white', linewidth=2)
    ax.xaxis_date()

    # rotate and align the tick labels so they look better
    fig.autofmt_xdate()
    #leg = ax.legend(loc='best', fancybox=True, numpoints=1)
    #leg.get_frame().set_alpha(0.5)


    plt.show()


    #points = [(x['date'], float(x['distance(km)'])) for x in log if (
    #        (x['activity'] == 'Running' or x['activity'] == 'Orienteering') and len(x['distance(km)']) > 0)]


    #startdate = min([e['date'] for e in iter(log)])

    #hack
    #startdate = dt.date(2002,11,18) # a monday

def get_data():
    ''' Use mechanize to browse AP and retrieve my training.'''
    # TODO: save username and password somewhere hidden and open as config
    # TODO: change userid of form, uncheck boxes, etc
    br = mechanize.Browser()
    br.open("http://attackpoint.org")
    br.select_form(nr=0)
    br.form['username'] = username
    br.form['password'] = password
    br.submit()

    br.open("http://attackpoint.org/reports.jsp")
    br.select_form(nr=2)

    # TODO: time range select
    br['fromselected'] = 0
    br['toselected'] = 0

    data = br.submit()
    with open('test.csv', 'w') as f:
        shutil.copyfileobj(data, f)

def datespan(startdate, enddate, delta=dt.timedelta(days=7)):
    """ Generate iterable of dates."""
    currentdate = startdate
    while currentdate < enddate:
        yield currentdate
        currentdate += delta

def subset(log, var, activities, startdate=None, enddate=None):
    """ Return sum of var for all activities in the date range (startdate inclusive)."""
    if startdate == None or enddate == None:
        values = [float(x[var]) for x in log if len(x[var]) > 0 and x['activity'] in activities]
    else:
        values = [float(x[var]) for x in log if (len(x[var]) > 0 and (startdate <= x['date'] < enddate)) and x['activity'] in activities]
    return values

if __name__ == '__main__':
    main()