#!/usr/bin/env python

import os
import datetime
import pandas as pd

default_columns = ['group','message_id','sender_id','sender_name','message','message_date','message_media', 'fwd_source_id', 'fwd_source_name']

def load_range_params(params):
    date_range = {}

    for p in ['from', 'to']:
        pu = p.upper()
        year = params[f"{pu}_YEAR"]
        month = params[f"{pu}_MONTH"]
        day = params[f"{pu}_DAY"]
        date_range[p] = {
            "year": year,
            "month": month,
            "day": day,
            "timestamp": datetime.datetime.strptime(
                f"{year},{month},{day}",
                '%Y,%m,%d',
            )
        }

    return date_range

def create_dirs(dirs):
    for d in dirs:
        try:
            os.makedirs(d)
        except FileExistsError:
            pass

def process_date(year, month, day, hour, minute):
    year = str(format(year, '02d'))
    month = str(format(month, '02d'))
    day = str(format(day, '02d'))
    hour = str(format(hour, '02d'))
    minute = str(format(minute, '02d'))

    return (
        datetime.datetime.strptime(f"{year},{month},{day}", '%Y,%m,%d'),
        f"{year}-{month}-{day}, {hour}:{minute}",
    )

def is_in_range(date_range, timestamp):
    return date_range['from']['timestamp'] <= timestamp and date_range['to']['timestamp'] >= timestamp

def update_csv(rows, archive, sep=';', columns=default_columns):
    df = pd.DataFrame(rows, columns=columns)
    with open(archive, 'w+') as f:
        df.to_csv(f, sep=sep)
    return True
