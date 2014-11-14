#! /usr/bin/env python

import shutil
import datetime as dt
import argparse

import mechanize
import csv
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

username = 'cristina'
password = 'fillmein'

# TODO: consider using Counter class from collections to count neat stats 
# TODO: small sql db for learning/easy querying?

# http://attackpoint.org/printtraining.jsp?userid=470&from-month=11&from-day=14&from-year=2014&to-month=11&to-day=14&to-year=2014&isplan=0&outtype=csv
# http://attackpoint.org/printtraining.jsp?userid=470&isplan=0&outtype=csv

def main():
    parser = argparse.ArgumentParser(description='Plot training stuff')
    parser.add_argument('--fetch', action='store_true', default=False)    
    parser.add_argument('-s', '--start', help='Start date in format yyyy-mm-dd',  
                    type=lambda s: dt.datetime.strptime(s, '%Y-%m-%d'), required=False)
    parser.add_argument('-e', '--end', help='End date in format yyyy-mm-dd', required=False,
                    type=lambda s: dt.datetime.strptime(s, '%Y-%m-%d'))

    args = parser.parse_args()
    if args.fetch:
        get_data()

    filename = 'test.csv'
    df = pd.read_csv(filename, parse_dates=[0])
    df = df.set_index(pd.DatetimeIndex(df['date']))

    running = df[df['activity'] == 'Running']
    start = dt.datetime(2014, 9, 16)
    end = dt.datetime(2014, 11, 16)
    running = running[running['date'] > start]
    running = running.resample('W', how='sum')   

    plt.xkcd()
    fig, ax = plt.subplots(1)
    plt.title('Weekly km, orienteering + running')
    rects1 = ax.bar(running.index, running['distance(km)'], 3, color='white', linewidth=2)
    ax.xaxis_date()
    fig.autofmt_xdate()
    
    #plt.savefig('test.png')
    plt.show()

    

def get_data():
    ''' Use mechanize to browse AP and retrieve my training.'''
    # TODO: save username and password somewhere hidden and open as config
    # TODO: change userid of form, uncheck boxes, etc
    br = mechanize.Browser()
    br.set_handle_robots(False)
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