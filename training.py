#! /usr/bin/env python

import shutil
import datetime as dt
import argparse
from collections import OrderedDict

import mechanize
import matplotlib
matplotlib.use('Agg')   # necessary for remote usage to avoid DISPLAY error
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from bokeh.plotting import ColumnDataSource, figure, show, output_file
from bokeh.models import HoverTool

from settings import *


months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


# http://attackpoint.org/printtraining.jsp?userid=470&from-month=11&from-day=14&from-year=2014&to-month=11&to-day=14&to-year=2014&isplan=0&outtype=csv
# http://attackpoint.org/printtraining.jsp?userid=470&isplan=0&outtype=csv


def main():
    parser = argparse.ArgumentParser(description='Plot training stuff')
    parser.add_argument('--fetch', action='store_true', default=False)
    parser.add_argument('-s', '--start', help='Start date in format yyyy-mm-dd',
                        type=lambda s: dt.datetime.strptime(s, '%Y-%m-%d'),
                        required=False)
    parser.add_argument('-e', '--end', help='End date in format yyyy-mm-dd',
                        required=False,
                        type=lambda s: dt.datetime.strptime(s, '%Y-%m-%d'))
    parser.add_argument('-f', '--filename', required=False)

    args = parser.parse_args()
    if args.fetch:
        filename = 'test.csv'
        data = get_all_training_data()
        with open('test.csv', 'w') as f:
            shutil.copyfileobj(data, f)

    if args.filename:
        filename = args.filename

    columns = ["date", "hour", "activity", "workout", "keywords",
                "time", "i0", "i1", "i2", "i3", "i4", "i5",
                "distance(km)", "climb(m)", "intensity", "t-intensity",
                "ahr", "mhr", "controls", "spiked", "rhr", "sleep",
                "weight(kg)", "injured", "sick", "restday", "shoes", "route",
                "description", "private note"]
    df = pd.read_csv(filename, parse_dates=[0], names=columns, skiprows=[0])
    df = df.set_index(pd.DatetimeIndex(df['date']))

    # Not good for exact dates b/c leap years
    #df['doy'] = df.index.dayofyear
    df['month'] = map(lambda date: date.month, df['date'])
    df['dom'] = map(lambda date: date.day, df['date'])
    df['moday'] = map(lambda month, day:str(month) + '-' + str(day), df['month'], df['dom'])

    df = df[df['activity'] == 'Orienteering']

    jjdata = read_jj('data/jj.txt')
    source = get_day_counts_diff_source(jjdata, df)
    #s1 = plot_counts_data(df, title='Cristina')
    #s2 = plot_counts_data(jj, title='J-J')
    plot_counts_data(source, 'Cristina-J-J')

    #filename = 'cristina_jj.html'
    #p = vplot(s1,s2,s3)
    #save(p)


def plot_xkcd(data):
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


def get_day_counts_source(data):

    colors = [
        '#ffffff', '#efedf5', '#dadaeb', '#bcbddc', '#9e9ac8', '#807dba', '#6a51a3', '#54278f', '#3f007d'
    ]
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

    return source

def get_day_counts_diff_source(data1, data2):

    colors = [
        '#af8dc3', '#f7f7f7', '#7fbf7b', '#666666'
        ]
    days = range(1, 32)
    # We need to have values for every
    # pair of month/day names. Map the count to a color.
    month = []
    day = []
    color = []
    count = []
    counts1 = data1.moday.value_counts()
    counts2 = data2.moday.value_counts()
    for x, m in enumerate(months):
        for d in days:
            month.append(m)
            day.append(d)
            try:
                daily_count1 = counts1[str(x+1)+'-'+str(d)]
            except KeyError:
                daily_count1 = 0
            try:
                daily_count2 = counts2[str(x+1)+'-'+str(d)]
            except KeyError:
                daily_count2 = 0

            if ((d == 31) and (m in ['Feb', 'Apr', 'Jun', 'Sep', 'Nov'])) or ((m == 'Feb') and (d == 30)):
                daily_count = 'Both'
                c = 1
            elif (daily_count1 == 0) and (daily_count2 > 0):
                daily_count = 'Cristina'
                c = 0
            elif (daily_count2 == 0) and (daily_count1 > 0):
                daily_count = 'J-J'
                c = 2
            elif (daily_count2 == 0) and (daily_count1 == 0):
                daily_count = 'Neither'
                c = 3
            else:
                daily_count = 'Both'
                c = 1

            count.append(daily_count)
            color.append(colors[c])

    source = ColumnDataSource(
        data=dict(month=month, day=day, color=color, count=count)
    )

    return source


def plot_counts_data(source, title='Test'):
    ''' Create day/month grid plot of data. 
    source is a ColumnDataSource with month, day, color, count
    '''

    filename = 'odays_{}.html'.format(title.lower())
    output_file(filename, mode="cdn")

    TOOLS = "resize,hover,save,pan,box_zoom,wheel_zoom"

    p = figure(title=title,
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

    #return p
    show(p)      # show the plot


def read_jj(filename):
    ''' Read in list of dates in 12/19/1978 format'''
    with open(filename) as f:
        dates = [line.strip().split('/') for line in f]

    dates = [dt.date(int(x[2]), int(x[0]), int(x[1])) for x in dates]
    month = map(lambda date: date.month, dates)
    dom = map(lambda date: date.day, dates)
    moday = map(lambda month, day:str(month) + '-' + str(day), month, dom)

    data = pd.DataFrame({'date': dates, 'month':month , 'dom': dom, 'moday':moday})

    return data


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


def subset(log, activities, startdate=None, enddate=None):
    """ Return subset for given activities in the date range (startdate inclusive)."""
    subset = log[log['activity'].isin(activities)]

    if startdate and enddate:
        subset = subset[(subset['date'] >= startdate) & (subset['date'] < enddate)]

    return subset

if __name__ == '__main__':
    main()