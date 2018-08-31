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


import os
import sys
import datetime
import time
import csv
import argparse
import matplotlib.pyplot as plt
import numpy as np

from PyQt4 import QtGui
from PyQt4.QtGui import QSizePolicy, QTableWidget, QTableWidgetItem, QHeaderView
from PyQt4.QtCore import QTimer, Qt
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT
from matplotlib.figure import Figure

# Fancier styling for the graph
plt.style.use('ggplot')

POWER_SUPPLY_PATH = "/sys/class/power_supply/"
LOG_PATH = "/var/log/battmon"
BATTERY_DATA_FILES = ["capacity", "status", "technology", "energy_now", "energy_full_design", "voltage_now"]
REQUIRED_DATA_FILES = ["capacity", "status", "energy_now", "energy_full_design", "voltage_now"]
LOG_FILE_FIELDS = ["time", "status", "capacity", "energy_now", "voltage_now"]
BATTERY_NAME_FILES = ["manufacturer", "model_name", "serial_number"]

# How often the GUI will update battery data in milliseconds
UPDATE_INTERVAL = 5000

millis_time = lambda: int(round(time.time() * 1000))
MILLIS_IN_DAY = 86400000
MILLIS_IN_WEEK = 7 * MILLIS_IN_DAY
MILLIS_IN_MONTH = 30 * MILLIS_IN_DAY
MILLIS_IN_TOTAL = millis_time() 

def title_name(s):
    return " ".join([x.capitalize() for x in s.split("_")])

def check_state(battery, battery_state):
    for attribute in REQUIRED_DATA_FILES:
        if (battery_state[attribute] == ""):
            print("Battery " + battery + " is missing attribute" + 
                    attribute + ".", file=sys.stderr)
            return False
    return True

def is_float(s):
    try: 
        n = float(s)
    except ValueError:
        return False
    return True

# Creates a human readable version of the battery state data
def get_clean_states(data):
    states = {}
    for battery in data:
        states[battery] = {}
        for field in data[battery]:
            if ("energy" in field.lower() and data[battery][field] != ""):
                states[battery][field] = str(int(data[battery][field])/ 1.0e6) + " Wh"
            elif ("voltage" in field.lower() and data[battery][field] != ""):
                states[battery][field] = str(int(data[battery][field])/ 1.0e6) + " V"
            else:
                states[battery][field] = data[battery][field]
    return states

# Reads the entire contents of the file specified. If no such file exists, an
# empty string is returned. The contents is stripped of whitespace at the ends.
# Catches IOError if file doesn't exist or is not readable, then exits
def read_path(path):
    try:
        if (not os.path.isfile(path)):
            return ""
        with open(path, 'r') as f:
            return f.read().strip() 
    except IOError:
        print("Could not read file: " + path + " Exiting ...", file=sys.stderr)
        sys.exit() 

# Reads the battery/ies information from POWER_SUPPLY_PATH according to the 
# kernel specifications and returns a nested dictionary with format:
# { "<manufacturer>_<model_name>_<serial_number>" : { "capacity" : <capacity>
# , "status" : <status>, ... }}
def get_battery_states():
    # get all supply names
    supplies = list(os.walk(POWER_SUPPLY_PATH))[0][1]
    battery_states = {}
    for supply in supplies:
        supply_path = os.path.join(POWER_SUPPLY_PATH, supply)
        type = read_path(os.path.join(supply_path, "type"))
        if (type == "Battery"):
            battery_id =  "_".join([read_path(os.path.join(supply_path, bnf))
                for bnf in BATTERY_NAME_FILES])
            battery_states[battery_id] = {}
            for bdf in BATTERY_DATA_FILES:
                battery_states[battery_id][bdf] = read_path(
                        os.path.join(supply_path, bdf))
            battery_states[battery_id]["time"] = millis_time() 
    return battery_states

# Logs the information from get_battery_states() to individual log files for
# each battery under LOG_PATH
# Catches IOError if LOG_PATH is unwritable, then exits
def log_battery_state():
    states = get_battery_states() 
    try:
        # if logging dir does not exist, create it. 
        if not os.path.exists(LOG_PATH):
            os.mkdir(LOG_PATH)
        for battery in states:
            if (check_state(battery, states[battery])):
                fields = [states[battery][x] for x in LOG_FILE_FIELDS] 
                with open(os.path.join(LOG_PATH, battery + ".log"), 'a') as log:
                    writer = csv.writer(log)
                    writer.writerow(fields)
    except IOError:
        print("Could not write to directory: " + LOG_PATH + " Exiting ...", file=sys.stderr)
        sys.exit() 

# Retrieves battery history from the logfiles in LOG_PATH
# Recall that CSV log format is: Time (millis), Status, Capacity. Battery ID 
# derived from the log name, stored in LOG_PATH/<battery_id>.log
def get_battery_history(offset):
    logfiles = [f for f in os.listdir(LOG_PATH) 
            if os.path.isfile(os.path.join(LOG_PATH, f))]
    history = {}
    cutoff = millis_time() - offset
    for logfile in logfiles:
        battery_id = os.path.splitext(logfile)[0].strip()
        data = { x : [] for x in LOG_FILE_FIELDS }
        with open(os.path.join(LOG_PATH, logfile), 'r') as log:
            reader = csv.DictReader(log, LOG_FILE_FIELDS, restval=0)
            for row in reader:
                for f in row:
                    if (is_float(row[f])):
                        row[f] = float(row[f])
                        if ("energy" in f or "voltage" in f):
                            row[f] /= 1.0e6
                if (row["time"] >= cutoff):
                    # convert UNIX millisecond timestamp to datetime object
                    row["time"] = datetime.datetime.fromtimestamp(
                            row["time"] / 1000.0)
                    for k in row:
                        data[k].append(row[k])
            history[battery_id] = data
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
        main_layout = QtGui.QHBoxLayout() 
        graph_layout = QtGui.QVBoxLayout() 
        self.info_layout = QtGui.QVBoxLayout()

        # sizing policies
        fixed_policy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        hpref_policy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        vpref_policy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)

        states = get_battery_states() 
        self.battery_widgets = {}
        for battery in sorted(states.keys()):
            battinfo_gbox = QtGui.QGroupBox("Battery: " +  battery) 
            battinfo_vbox = QtGui.QVBoxLayout() 

            table = QTableWidget() 
            table.setRowCount(len(BATTERY_DATA_FILES))
            table.setColumnCount(2)
            table.verticalHeader().setVisible(False)
            table.horizontalHeader().setVisible(False)
            table.horizontalHeader().setResizeMode(QHeaderView.Stretch)
            table.verticalHeader().setResizeMode(QHeaderView.Stretch)
            table.setMinimumHeight(50) 
            table.setSizePolicy(vpref_policy)

            battinfo_vbox.addWidget(table)
            progress = QtGui.QProgressBar(self)
            battinfo_vbox.addWidget(progress)
            progress.setSizePolicy(hpref_policy)
            progress.setFormat("%v%")

            self.battery_widgets[battery] = {}
            self.battery_widgets[battery]["table"] = table
            self.battery_widgets[battery]["progress"] = progress

            battinfo_gbox.setSizePolicy(vpref_policy)
            battinfo_gbox.setLayout(battinfo_vbox)
            self.info_layout.addWidget(battinfo_gbox)

        # Checkbox to select fields to graph
        fields_gbox = QtGui.QGroupBox("Show:") 
        fields_hbox = QtGui.QHBoxLayout() 
        self.capacity = QtGui.QCheckBox("Capacity")
        self.voltage = QtGui.QCheckBox("Voltage")
        self.energy = QtGui.QCheckBox("Energy")

        self.energy.clicked.connect(self.plot)
        self.voltage.clicked.connect(self.plot)
        self.capacity.clicked.connect(self.plot)

        fields_hbox.addWidget(self.capacity)
        fields_hbox.addWidget(self.energy)
        fields_hbox.addWidget(self.voltage)
        fields_gbox.setLayout(fields_hbox)
        fields_gbox.setSizePolicy(fixed_policy)

        graph_layout.addWidget(fields_gbox)

        # Radio buttons to restrict timeframe to graph
        timeframe_gbox = QtGui.QGroupBox("Time Frame:") 
        timeframe_hbox = QtGui.QHBoxLayout() 
        self.day = QtGui.QRadioButton("Day")
        self.week = QtGui.QRadioButton("Week")
        self.month = QtGui.QRadioButton("Month")
        self.all = QtGui.QRadioButton("All")

        self.day.clicked.connect(self.plot)
        self.week.clicked.connect(self.plot)
        self.month.clicked.connect(self.plot)
        self.all.clicked.connect(self.plot)

        timeframe_hbox.addWidget(self.day)
        timeframe_hbox.addWidget(self.week)
        timeframe_hbox.addWidget(self.month)
        timeframe_hbox.addWidget(self.all)
        timeframe_gbox.setLayout(timeframe_hbox)
        timeframe_gbox.setSizePolicy(fixed_policy)

        graph_layout.addWidget(timeframe_gbox)
        graph_layout.addWidget(self.toolbar)
        graph_layout.addWidget(self.canvas)

        main_layout.addLayout(self.info_layout) 
        main_layout.addLayout(graph_layout) 
        main_layout.addWidget(QtGui.QSizeGrip(self), 0, Qt.AlignBottom | Qt.AlignRight)
        self.setLayout(main_layout)

        # Default graph is week data
        self.week.setChecked(True)
        self.capacity.setChecked(True)
        self.energy.setChecked(True)
        self.voltage.setChecked(True)

        # populate initial data
        self.update() 


    def update_battery_data(self):
        states = get_battery_states()
        clean_states = get_clean_states(states)
        for battery in self.battery_widgets:
            if battery in states:
                table = self.battery_widgets[battery]["table"]
                for i, field in enumerate(BATTERY_DATA_FILES):
                    table.setItem(i, 0, QTableWidgetItem(title_name(field)))
                    table.setItem(i, 1, QTableWidgetItem(clean_states[battery][field]))
                progress = self.battery_widgets[battery]["progress"]
                new_capacity = int(states[battery]["capacity"])
                # contrary to specifications "capacity" can be larger than 100
                if (new_capacity > 100):
                    progress.setRange(0,new_capacity) 
                else:
                    progress.setRange(0,100) 
                progress.setValue(int(states[battery]["capacity"]))

    def update(self):
        self.update_battery_data() 
        self.plot() 

    def plot(self):
        # determine the proper (x-axis range) offset 
        if (self.day.isChecked()):
            offset = MILLIS_IN_DAY
        elif (self.week.isChecked()):
            offset = MILLIS_IN_WEEK
        elif (self.month.isChecked()):
            offset = MILLIS_IN_MONTH
        else:
            offset = MILLIS_IN_TOTAL

        # determine the fields to plot
        fields = [] 
        if (self.capacity.isChecked()):
            fields.append("capacity")
        if (self.energy.isChecked()):
            fields.append("energy_now")
        if (self.voltage.isChecked()):
            fields.append("voltage_now")

        # clear plot
        self.figure.clear() 
        columns = 1
        rows = len(fields)

        # get battery data from logs
        history = get_battery_history(offset)
        for idx, field in enumerate(fields):
            ax = self.figure.add_subplot(rows, columns, idx+1)
            for battery in sorted(history.keys()):
                if (idx == 0):
                    ax.plot(history[battery]["time"], history[battery][field], label=battery)
                else:
                    ax.plot(history[battery]["time"], history[battery][field])
                ax.set_xlabel("Time")
                ax.set_ylabel(title_name(field).split(" ")[0])
            self.figure.autofmt_xdate()

        # refresh canvas
        self.figure.legend()
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
        # fill the widgets with the current battery data every UPDATE_INTERVAL
        timer = QTimer()
        timer.timeout.connect(main.update)
        timer.setInterval(UPDATE_INTERVAL)
        timer.start()
        sys.exit(app.exec_())
    if (not args.log and not args.graph):
        parser.print_help()

if __name__ == "__main__":
    main()
