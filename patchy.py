import csv
import sys
import getopt
import os
from datetime import datetime, timedelta
from math import floor


DATA_DIR = "~/.patchy/"
BALANCE_FILE = os.path.expanduser(DATA_DIR) + "balance.csv"
THIS_MONTH = int(datetime.now().month)
LAST_MONTH = (datetime.now().replace(day=1) - timedelta(days=1)).month
MONTH_FILE = os.path.expanduser(DATA_DIR) + str(datetime.now().year) + "_" + str(THIS_MONTH) + ".csv"
DAY_GOAL = 8.4
DATE_FORMAT = "%Y-%m-%d_%H-%M-%S"


class Colors:
    YELLOW = "\033[38;5;11m"
    RED = "\033[38;5;9m"
    GREEN = "\033[38;5;10m"


def argparse(argv):
    patch = None
    opts, args = getopt.getopt(argv,"hp")
    for opt, arg in opts:
        if opt == '-h':
            print ('"patchy.py" prints the current balance')
            print ('"patchy.py -p" patches you in/out')
            sys.exit()
        elif opt in ("-p", "patch"):
            patch = True
    return patch


# Aggregates the last month and saves the resulting balance into balancefile
def aggregate_last_month():
    return 0


# Loads the current balance from the balance file and calculates the final balance with the current months patchings
def load_balance():
    balance = 0.0
    if os.path.exists(BALANCE_FILE):
        with open(BALANCE_FILE, 'r') as file:
            csvreader = csv.reader(file,delimiter=',')
            data = list()
            for entry in csvreader:
                data.append(entry)
            last = data[-1]
            if int(last[0]) != LAST_MONTH:
                balance = aggregate_last_month()
            else:
                balance = float(last[1])
    if os.path.exists(MONTH_FILE):
        with open(MONTH_FILE, 'r') as file:
            csvreader = csv.reader(file, delimiter=',')
            for entry in csvreader:
                if entry[2] != '':
                    balance = balance + float(entry[2])
                else:
                    start = datetime.strptime(entry[0], DATE_FORMAT)
                    end = datetime.now()
                    diff = (end - start).total_seconds() / 3600
                    balance = balance + diff
    return balance


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
        print(color + "Fix yo patchings")
        exit(1)
    today_left = DAY_GOAL - today
    balance = balance + today
    if today_left <= 0:
        color = Colors.GREEN
    print(color + str(floor(today)) + ":" + str(floor((today*60)%60)) +
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
    with open(MONTH_FILE, 'r+') as file:
        csvreader = csv.reader(file, delimiter=',')
        csvwriter = csv.writer(file, delimiter=',', lineterminator="\n")
        entries = list()
        for entry in csvreader:
            entries.append(entry)
        start = datetime.strptime(entries[-1][0], DATE_FORMAT)
        end = entries[-1][1]
        if end != '':
            new_start = datetime.now().strftime(DATE_FORMAT)
            entry = [new_start, '', '']
            csvwriter.writerow(entry)
        else:
            new_end = datetime.now()
            diff = (new_end - start).total_seconds() / 3600
            entry = [start.strftime(DATE_FORMAT), new_end.strftime(DATE_FORMAT), diff]
            delete_last_row(file)
            csvwriter.writerow(entry)


def main(argv):
    if not os.path.isdir(DATA_DIR):
        os.mkdir(DATA_DIR)
    to_patch = argparse(argv)
    balance = load_balance()
    if to_patch is None:
        print_status(balance)
    elif to_patch:
        patch()


if __name__ == "__main__":
    main(sys.argv[1:])
