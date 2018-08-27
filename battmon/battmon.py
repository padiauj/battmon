#!/usr/bin/python3

# Battmon - A simple battery monitoring tool for Linux-based operating systems
# Umesh Padia, 2018

# Usage (Python 3): battmon --log OR battmon --graph

# Battmon accesses the battery information stored in /sys/class/power_supply. 
#   * Each power supply (AC, batteries, USB) has its own subdirectory. 
#   * For each power supply <supply>/type will be read to determine whether
#   * the source is a battery. If so, the current time, serial number, 
#   * charging state, and power level will be logged in /var/log/battmon/
#   * for each battery as <manufacturer>_<model>_<serial>.log .
# Cron will be used to call this procedure on a regular basis (5 min).
# The program will be called using the --log option

# If battmon is called with the --graph option, a graph of battery history 
# will be displayed (using matplotlib). 

# NOTE: battmon supports Linux kernel 2.6.24 (after 2007) and higher, 
# as ACPI information was moved from /proc/power_supply to 
# /sys/class/poewr_supply

# Kernel specifications for /sys/class/power_supply: 
# https://www.kernel.org/doc/Documentation/ABI/testing/sysfs-class-power

# TODO: tolerate missing information, and error correcting code 

import os
import sys
import datetime
import time
import csv
import argparse
import matplotlib.pyplot as plt
import numpy as np

from PyQt4 import QtGui
from PyQt4.QtGui import QSizePolicy
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT
from matplotlib.figure import Figure

plt.style.use('ggplot')

POWER_SUPPLY_PATH = "/sys/class/power_supply/"
LOG_PATH = "/var/log/battmon"
MILLIS_IN_DAY = 86400000

millis_time = lambda: int(round(time.time() * 1000))

# Reads the entire contents of the file specified. If no such file exists, an
# empty string is returned. The contents is stripped of whitespace at the ends.
def read_path(path):
    if (not os.path.isfile(path)):
        return ""
    with open(path, 'r') as f:
        return f.read().strip() 

# Reads the battery/ies information from POWER_SUPPLY_PATH according to the 
# kernel specifications and returns a nested dictionary with format:
# { "<manufacturer>_<model_name>_<serial_number>" : { "capacity" : <capacity>
# , "status" : <status>}}
def get_battery_states():
    # get all supply names
    supplies = list(os.walk(POWER_SUPPLY_PATH))[0][1]
    battery_data_files = ["capacity", "status"]
    battery_name_files = ["manufacturer", "model_name", "serial_number"]
    battery_states = {}
    for supply in supplies:
        supply_path = os.path.join(POWER_SUPPLY_PATH, supply)
        type = read_path(os.path.join(supply_path, "type"))
        if (type == "Battery"):
            battery_id =  "_".join([read_path(os.path.join(supply_path, bnf))
                for bnf in battery_name_files])
            battery_states[battery_id] = {}
            for bdf in battery_data_files:
                battery_states[battery_id][bdf] = read_path(
                        os.path.join(supply_path, bdf))
    return battery_states

# Logs the information from get_battery_states() to individual log files for
# each battery under LOG_PATH
def log_battery_state():
    # if logging dir does not exist, create it. 
    if not os.path.exists(LOG_PATH):
        os.mkdir(LOG_PATH)
    states = get_battery_states() 
    time = str(millis_time())
    for battery in states:
        print(states[battery])
        fields = [time, states[battery]["status"][0].upper(), 
                states[battery]["capacity"]]
        with open(os.path.join(LOG_PATH, battery + ".log"), 'a') as log:
            writer = csv.writer(log)
            writer.writerow(fields)

# Retrieves battery history from the logfiles in LOG_PATH
# Recall that CSV log format is: Time (millis), Status, Capacity. Battery ID 
# derived from the log name, stored in LOG_PATH/<battery_id>.log
def get_battery_history(offset):
    logfiles = [f for f in os.listdir(LOG_PATH) 
            if os.path.isfile(os.path.join(LOG_PATH, f))]
    history = {}
    cutoff = millis_time() - offset
    for logfile in logfiles:
        reader = csv.reader(open(os.path.join(LOG_PATH, logfile), 'r'))
        time = []
        capacity = []
        for row in reader:
            timestamp = int(row[0])
            if (timestamp >= cutoff):
                # convert UNIX millisecond timestamp to datetime object
                time.append(
                        datetime.datetime.fromtimestamp(timestamp / 1000.0))
                capacity.append(int(row[2]))
        history[os.path.splitext(logfile)[0].strip()] = (time, capacity)
    return history

# Editing NavigationToolbar2QT to remove extraneous buttons
class NavigationToolbar(NavigationToolbar2QT):
    toolitems = [t for t in NavigationToolbar2QT.toolitems if
                             t[0] in ('Home', 'Pan', 'Zoom', 'Save')]

# Battery Graph GUI (PyQt4)
class Window(QtGui.QDialog):
    def __init__(self, parent=None):
        super(Window, self).__init__(parent)

        self.setWindowTitle("Battmon") 

        # a figure instance to plot on
        self.figure = Figure()

        # this is the Canvas Widget that displays the `figure`
        # it takes the `figure` instance as a parameter to __init__
        self.canvas = FigureCanvasQTAgg(self.figure)

        # this is the Navigation widget
        # it takes the Canvas widget and a parent
        self.toolbar = NavigationToolbar(self.canvas, self)

        # set the layout
        layout = QtGui.QVBoxLayout()

        # Radio buttons to restrict timeframe to graph
        timeframe_gbox = QtGui.QGroupBox("Time Frame:") 
        timeframe_hbox = QtGui.QHBoxLayout() 
        self.day = QtGui.QRadioButton("Day")
        self.week = QtGui.QRadioButton("Week")
        self.month = QtGui.QRadioButton("Month")
        self.all = QtGui.QRadioButton("All")

        self.day.clicked.connect(lambda: self.plot(MILLIS_IN_DAY))
        self.week.clicked.connect(lambda: self.plot(7*MILLIS_IN_DAY))
        self.month.clicked.connect(lambda: self.plot(30*MILLIS_IN_DAY))
        self.all.clicked.connect(lambda: self.plot(millis_time()))

        timeframe_hbox.addWidget(self.day)
        timeframe_hbox.addWidget(self.week)
        timeframe_hbox.addWidget(self.month)
        timeframe_hbox.addWidget(self.all)
        timeframe_gbox.setLayout(timeframe_hbox)

        fixed_policy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        hpref_policy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        timeframe_gbox.setSizePolicy(fixed_policy)

        states = get_battery_states() 
        for battery in states:
            battinfo_gbox = QtGui.QGroupBox("Battery: " +  battery) 
            battinfo_vbox = QtGui.QVBoxLayout() 
            battinfo_vbox.addWidget(QtGui.QLabel("Status: " + states[battery]["status"]))
            progress = QtGui.QProgressBar(self)
            battinfo_vbox.addWidget(progress)
            progress.setValue(int(states[battery]["capacity"]))
            progress.setSizePolicy(hpref_policy)
            battinfo_gbox.setSizePolicy(hpref_policy)
            battinfo_gbox.setLayout(battinfo_vbox)
            layout.addWidget(battinfo_gbox)

        # fix timeframe and battery information size policy so that they don't
        # resize when the window resizes

        layout.addWidget(timeframe_gbox)
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        self.setLayout(layout)

        # Default graph is all data (maybe switch this to weekly to make 
        # an initially quick graph?)
        self.all.setChecked(True)
        self.plot(millis_time())

    def plot(self, offset):
        # clear plot
        self.figure.clear() 
        ax = self.figure.add_subplot(111)
        # get battery data from logs
        history = get_battery_history(offset)
        # plot data
        for battery in history:
            ax.plot(history[battery][0], history[battery][1],
                    label=battery, marker='o')
        ax.set_xlabel("Date")
        ax.set_ylabel("Charge")
        self.figure.autofmt_xdate()
        self.figure.legend()

        # refresh canvas
        self.canvas.draw()

def main():
    parser = argparse.ArgumentParser(description="Battmon - A simple battery monitoring tool for Linux-based operating systems")
    parser.add_argument("--log", action="store_true", help="log current battery charge and status")
    parser.add_argument("--graph", action="store_true", help="show battery history graph GUI")
    args = parser.parse_args()

    if args.log:
        log_battery_state()
    if args.graph:
        app = QtGui.QApplication(sys.argv)
        main = Window()
        main.show()
        sys.exit(app.exec_())
    if (not args.log and not args.graph):
        parser.print_help()

if __name__ == "__main__":
    main()
