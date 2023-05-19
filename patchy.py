#!/usr/bin/env python3
import csv
import sys
import getopt
import os
from datetime import datetime, timedelta
from math import floor
from calendar import monthrange


DATA_DIR = "~/.patchy/"
BALANCE_FILE = os.path.expanduser(DATA_DIR) + "balance.csv"
THIS_MONTH = int(datetime.now().month)
LAST_MONTH = (datetime.now().replace(day=1) - timedelta(days=1)).month
MONTH_FILE = os.path.expanduser(DATA_DIR) + str(datetime.now().year) + "_" + str(THIS_MONTH) + ".csv"
HOLIDAY_FILE = os.path.expanduser(DATA_DIR) + "holidays.csv"
DAY_GOAL = 8.4
DATE_FORMAT = "%Y-%m-%d_%H-%M-%S"
PUBLIC_HOLIDAYS = [
    datetime(year=datetime.now().year, month=1, day=2).date(),
    datetime(year=datetime.now().year, month=4, day=7).date(),
    datetime(year=datetime.now().year, month=4, day=10).date(),
    datetime(year=datetime.now().year, month=5, day=18).date(),
    datetime(year=datetime.now().year, month=5, day=29).date(),
    datetime(year=datetime.now().year, month=8, day=1).date(),
    datetime(year=datetime.now().year, month=12, day=25).date(),
    datetime(year=datetime.now().year, month=12, day=26).date()
]
HOLIDAYS = []
REDUCTION_PRE_HOLIDAY = 1
use_py3status = False
patched_in = False


class Colors:
    YELLOW = ["\033[38;5;11m", "#FFFF00"]
    RED = ["\033[38;5;9m", "#FF0000"]
    GREEN = ["\033[38;5;10m", "#00FF00"]
    WHITE = ["\033[38;5;15m", "#FFFFFF"]
    LIGHT_GREEN = ["\033[38;5;155m", "#b3f542"]


def read_holidays():
    if not os.path.isfile(HOLIDAY_FILE):
        return []
    with open(HOLIDAY_FILE, 'r') as file:
        csvreader = csv.reader(file, delimiter=',')
        for entry in csvreader:
            if len(entry) == 1:
                start = datetime.strptime(entry[0], DATE_FORMAT).replace(hour=0, minute=0, second=0, microsecond=0)
                end = datetime.strptime(entry[0], DATE_FORMAT).replace(hour=23, minute=59, second=59, microsecond=999)
                HOLIDAYS.append((start, end))
            else:
                start = datetime.strptime(entry[0], DATE_FORMAT)
                end = datetime.strptime(entry[1], DATE_FORMAT)
                HOLIDAYS.append((start, end))


def argparse(argv):
    patch = None
    opts, args = getopt.getopt(argv, "hpsv")
    for opt, arg in opts:
        if opt == '-h':
            print('"patchy.py" prints the current balance')
            print('"patchy.py -p" patches you in/out')
            print('"patchy.py -s" use py3status compatible output')
            sys.exit()
        elif opt in ("-p"):
            patch = True
        elif opt in ("-s"):
            global use_py3status
            use_py3status = True
    return patch


# Aggregates the last month and saves the resulting balance into balancefile
def aggregate_last_month():
    return 0


# Loads the current balance from the balance file and calculates the final balance with the current months patchings
def load_balance():
    balance = 0.0
    if os.path.exists(BALANCE_FILE):
        with open(BALANCE_FILE, 'r') as file:
            csvreader = csv.reader(file, delimiter=',')
            data = list()
            for entry in csvreader:
                data.append(entry)
            last = data[-1]
            if int(last[0]) != LAST_MONTH:
                balance = aggregate_last_month()
            else:
                balance = float(last[1])
    if os.path.exists(MONTH_FILE):
        patchings = dict()
        with open(MONTH_FILE, 'r') as file:
            csvreader = csv.reader(file, delimiter=',')
            for entry in csvreader:
                start = datetime.strptime(entry[0], DATE_FORMAT)
                if entry[1] != '':
                    end = datetime.strptime(entry[1], DATE_FORMAT)
                else:
                    end = datetime.now()
                if start.date() in patchings:
                    patchings[start.date()].append((start,end))
                else:
                    patchings[start.date()] = [(start, end)]
        for i in range(1, monthrange(datetime.now().year, datetime.now().month)[1]):
            if i > datetime.now().day:
                break
            d = datetime(datetime.now().year, datetime.now().month, i)
            pensum = calculate_pensum(d)
            if d.date() not in patchings:
                continue
            for start, end in patchings[d.date()]:
                balance = balance + ((end - start).total_seconds() / 3600)
            balance = balance - pensum

    return balance


def calculate_pensum(d):
    pensum = 0
    if d.date() in PUBLIC_HOLIDAYS:
        return 0
    for start, end in HOLIDAYS:
        if start <= d <= end:
            return 0
    if d.weekday() < 5:
        pensum = DAY_GOAL
    if (d + timedelta(days=1)).date() in PUBLIC_HOLIDAYS:
        pensum = DAY_GOAL - REDUCTION_PRE_HOLIDAY
    return pensum


def calculate_todays_balance():
    if not os.path.exists(MONTH_FILE):
        return 0.0
    daily_balance = 0.0
    with open(MONTH_FILE, 'r') as file:
        csvreader = csv.reader(file, delimiter=',')
        for entry in csvreader:
            start = datetime.strptime(entry[0], DATE_FORMAT)
            a = start.date()
            b = datetime.now().date()
            c = datetime.now()
            if start.date() == datetime.now().date():
                if entry[1] != '':
                    end = datetime.strptime(entry[1], DATE_FORMAT)
                else:
                    end = datetime.now()
                daily_balance = daily_balance + ((end - start).total_seconds() / 3600)
            if start.date() < datetime.now().date() and entry[1] == '':
                return -1
    return daily_balance


def print_status(balance):
    color = Colors.YELLOW
    today = calculate_todays_balance()
    if today == -1:
        color = Colors.RED
        if use_py3status:
            print("Fix yo patchings")
            print(color[1])
        else:
            print(color[0] + "Fix yo patchings")
        exit(1)
    pensum = calculate_pensum(datetime.now())
    today_left = pensum - today
    if today_left <= 0:
        if patched_in:
            color = Colors.GREEN
        else:
            color = Colors.WHITE
    else:
        if patched_in:
            color = Colors.LIGHT_GREEN
        else:
            color = Colors.YELLOW
    message = str(floor(today)) + ":" + str(floor((today*60)%60)) + \
        "h (" + str(floor(today_left)) + ":" + str(floor((today_left*60)%60)) + "h), " + \
        str(floor(balance)) + ":" + str(floor((balance*60)%60)) + "h"
    if use_py3status:
        print(message)
        print(color[1])
    else:
        print(color[0] + str(floor(today)) + ":" + str(floor((today*60)%60)) +
          "h (" + str(floor(today_left)) + ":" + str(floor((today_left*60)%60)) + "h), " +
          str(floor(balance)) + ":" + str(floor((balance*60)%60)) + "h")


def delete_last_row(file):
    file.seek(0, os.SEEK_END)
    pos = file.tell() - 1
    while pos > 0 and file.read(1) != "\n":
        pos -= 1
        file.seek(pos, os.SEEK_SET)
    if pos > 0:
        file.seek(pos, os.SEEK_SET)
        file.truncate()
        file.write("\n")


def patch():
    now = datetime.now().strftime(DATE_FORMAT)
    if not os.path.isfile(MONTH_FILE):
        open(MONTH_FILE, 'x')
    with open(MONTH_FILE, 'r+') as file:
        csvreader = csv.reader(file, delimiter=',')
        csvwriter = csv.writer(file, delimiter=',', lineterminator="\n")
        entries = list()
        for entry in csvreader:
            entries.append(entry)
        if len(entries) > 0:
            start = datetime.strptime(entries[-1][0], DATE_FORMAT)
            end = entries[-1][1]
        if len(entries) == 0 or end != '':
            new_start = datetime.now().strftime(DATE_FORMAT)
            entry = [new_start, '']
            csvwriter.writerow(entry)
        else:
            new_end = datetime.now()
            diff = (new_end - start).total_seconds() / 3600
            entry = [start.strftime(DATE_FORMAT), new_end.strftime(DATE_FORMAT), diff]
            delete_last_row(file)
            csvwriter.writerow(entry)


def main(argv):
    if not os.path.isdir(os.path.expanduser(DATA_DIR)):
        os.mkdir(os.path.expanduser(DATA_DIR))
    read_holidays()
    to_patch = argparse(argv)
    balance = load_balance()
    if to_patch is None:
        print_status(balance)
    elif to_patch:
        patch()


if __name__ == "__main__":
    main(sys.argv[1:])
