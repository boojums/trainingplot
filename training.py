#! /usr/bin/env python

import shutil
import datetime as dt
import argparse

import mechanize
import csv
import matplotlib
matplotlib.use('Agg')   # necessary for remote usage to avoid DISPLAY error
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from settings import *

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
        data = get_all_training_data()
        with open('test.csv', 'w') as f:
            shutil.copyfileobj(data, f)

    filename = 'test.csv'
    columns = ["date","hour","activity","workout","keywords",
                "time","i0","i1","i2","i3","i4","i5",
                "distance(km)","climb(m)","intensity","t-intensity",
                "ahr","mhr","controls","spiked","rhr","sleep",
                "weight(kg)","injured","sick","restday","shoes","route",
                "description","private note"]
    df = pd.read_csv(filename, parse_dates=[0], names=columns, skiprows=[0])
    df = df.set_index(pd.DatetimeIndex(df['date']))
    
    # Not good for exact dates b/c leap years
    #df['doy'] = df.index.dayofyear
    df['month'] = map(lambda date: date.month, df['date'])
    df['dom'] = map(lambda date: date.day, df['date'])
    df['moday'] = map(lambda month, day:str(month) + '-' + str(day), df['month'], df['dom'])

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
    
    plt.savefig('test.png')
    #plt.show()

def orienteering_days_of_year(data):
    ''' Get list of days of the year where activity has occurreed. ''' 
    orienteering = df[df['activity'] == 'Orienteering']
    modays = df.moday.unique()
    alldates = [str(x.month) + '-' + str(x.day) for x in [dt.date(1996, 1,1)+dt.timedelta(days=i) for i in range(366)]]
    missing = [x for x in alldates if x not in modays]

def plot_missing_days(data):
    from collections import OrderedDict

    from bokeh.plotting import ColumnDataSource, figure, show, output_file, save
    from bokeh.models import HoverTool
    
    colors = [
        '#ffffff', '#efedf5', '#dadaeb', '#bcbddc', '#9e9ac8', '#807dba', '#6a51a3', '#54278f', '#3f007d'
    ]
    months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    days = range(1, 32)
    # We need to have values for every
    # pair of month/day names. Map the count to a color.
    month = []
    day = []
    color = []
    count = []
    counts = data.moday.value_counts()
    for x, m in enumerate(months):
        for d in days:
            month.append(m)
            day.append(d)
            try:
                daily_count = counts[str(x+1)+'-'+str(d)]
            except KeyError:
                daily_count = 0
            count.append(daily_count)
            c = 0 if daily_count == 0 else min(daily_count, 8)
            color.append(colors[c])

    source = ColumnDataSource(
        data=dict(month=month, day=day, color=color, count=count)
    )

    output_file('orienteering_days.html', mode="cdn")

    TOOLS = "resize,hover,save,pan,box_zoom,wheel_zoom"

    p = figure(title="Cristina's orienteering sessions per day of year",
        x_range=[1,31], y_range=list(reversed(months)),
        x_axis_location="above", plot_width=900, plot_height=400,
        toolbar_location="left", tools=TOOLS)

    p.rect("day", "month", 1, 1, source=source,
        color="color", line_color=None)

    p.grid.grid_line_color = None
    p.axis.axis_line_color = None
    p.axis.major_tick_line_color = None
    p.axis.major_label_text_font_size = "5pt"
    p.axis.major_label_standoff = 0
    p.xaxis.major_label_orientation = np.pi/3

    hover = p.select(dict(type=HoverTool))
    hover.tooltips = OrderedDict([
        ('date', '@month @day'),
        ('count', '@count'),
    ])

    save(p)      # show the plot    


def get_all_training_data():
    ''' Use mechanize to browse AP and retrieve my training.'''
    # TODO: change userid of form, uncheck boxes, etc
    br = mechanize.Browser()
    br.set_handle_robots(False)
    br.open("http://attackpoint.org")
    br.select_form(nr=0)
    br.form['username'] = USERNAME
    br.form['password'] = PASSWORD
    br.submit()

    br.open("http://attackpoint.org/reports.jsp")
    br.select_form(nr=2)

    # TODO: time range select
    br['fromselected'] = 0
    br['toselected'] = 0

    data = br.submit()
    
    return data

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