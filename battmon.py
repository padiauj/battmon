# Battmon - A simple battery monitoring tool for Linux-based operating systems
# Umesh Padia, 2018

# Usage (Python 3): battmon --log OR battmon --graph

# Battmon accesses the battery information stored in /sys/class/power_supply. 
#   * Each power supply (AC, batteries, USB) has its own subdirectory. 
#   * For each power supply <supply>/type will be read to determine whether
#   * the source is a battery. If so, the current time, serial number, 
#   * charging state, and power level will be logged in /var/log/battmon/
#   * for each battery.
# Cron will be used to call this procedure on a regular basis (5 min).
# The program will be called using the --log option

# If battmon is called with the --graph option, a graph of battery history 
# will be displayed (using matplotlib). 

# NOTE: battmon supports Linux kernel 2.6.24 (after 2007) and higher, 
# as ACPI information was moved from /proc/power_supply to 
# /sys/class/poewr_supply

import os
import sys
import time
import csv
import argparse


POWER_SUPPLY_PATH = "/sys/class/power_supply/"
LOG_PATH = "/var/log/battmon"

millis_time = lambda: int(round(time.time() * 1000))


def read_path(path):
    if (not os.path.isfile(path)):
        return ""
    with open(path, 'r') as f:
        return f.read().strip() 

def log_battery_state():
    # if logging dir does not exist, create it. 
    if not os.path.exists(LOG_PATH):
        os.mkdir(LOG_PATH)

    # get all supply names
    supplies = list(os.walk(POWER_SUPPLY_PATH))[0][1]

    for supply in supplies:
        supply_path = os.path.join(POWER_SUPPLY_PATH, supply)
        type = read_path(os.path.join(supply_path, "type"))
        if (type == "Battery"):
            # voltage_now = read_path(os.path.join(supply_path, "voltage_now"))
            # voltage_max = read_path(os.path.join(supply_path, "voltage_max"))
            # voltage_min = read_path(os.path.join(supply_path, "voltage_min"))

            capacity = read_path(os.path.join(supply_path, "capacity"))
            status = read_path(os.path.join(supply_path, "status"))
            manufacturer = read_path(os.path.join(supply_path, "manufacturer"))
            model_name = read_path(os.path.join(supply_path, "model_name"))
            serial_number = read_path(os.path.join(supply_path, "serial_number"))

            time = str(millis_time())
            battery_id = manufacturer + "_" + model_name + "_" + serial_number

            fields = [time, status, capacity]
            with open(os.path.join(LOG_PATH, battery_id + ".log"), 'a') as log:
                writer = csv.writer(log)
                writer.writerow(fields)

def graph_battery():
    pass


log_battery_state()

