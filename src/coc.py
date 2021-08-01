#!/usr/bin/env python3
import logging
import os
import re
import sys
import json
from logging.handlers import TimedRotatingFileHandler

from datetime import datetime, timezone, timedelta
from dateutil.parser import parse

import Constant
from Utils import Others

# Initiate application
Constant.APP_PATH.BASEPATH = '/'.join((os.path.realpath(sys.argv[0]).split('\\')[0:-2]))
Constant.APP_PATH.NAME = os.path.realpath(sys.argv[0]).split('\\')[-1].split('.')[0]
log = logging.getLogger(Constant.APP_PATH.NAME)

for _dir in ('logs', 'resource'):
    _tmp_path = '/'.join((Constant.APP_PATH.BASEPATH, _dir))
    exec(f'Constant.APP_PATH.{_dir.upper()} = r\'{_tmp_path}\'')
    if not os.path.exists(_tmp_path):
        os.mkdir(_tmp_path)

handler = TimedRotatingFileHandler(
    '/'.join((Constant.APP_PATH.LOGS, Constant.APP_PATH.NAME + '.log')),
    when='midnight', backupCount=2)
formatter = logging.Formatter('%(asctime)s %(levelname)s : %(lineno)d : %(message)s')
handler.setFormatter(formatter)
handler.suffix = '%Y%m%d'
handler.extMatch = re.compile(r'^\d{8}$')
log.addHandler(handler)
log.setLevel(logging.INFO)


def datetime_serilizer(o):
    if isinstance(o, datetime):
        return o.__str__()


def date_hook(json_dict):
    for (key, value) in json_dict.items():
        try:
            json_dict[key] = parse(value)
        except:
            pass
    return json_dict


def to_sec(val, t):
    if t.lower() == 's':
        return val
    elif t.lower() == 'm':
        return to_sec(val * 60, 's')
    elif t.lower() == 'h':
        return to_sec(val * 60, 'm')
    elif t.lower() == 'd':
        return to_sec(val * 24, 'h')


def to_times(time_str):
    in_sec = 0
    for i in re.finditer('(\d+\w)', time_str):
        (val, t) = re.match('(\d+)(\w)', i.group()).groups()
        in_sec += to_sec(int(val), t)

    return in_sec


def to_bool(str_val):
    if str_val.title() in ('True', 'Yes', 'Y', 'T', '1'):
        return True
    else:
        return False


log.info('#' * 50)
log.info(Others.Yam('Start'))
log.info('#' * 50)

if os.path.exists(Constant.APP_PATH.RESOURCE + '/coc_db.json') and os.path.isfile(
        Constant.APP_PATH.RESOURCE + '/coc_db.json'):
    with open(Constant.APP_PATH.RESOURCE + '/coc_db.json') as json_filehandler:
        json_data = json.load(json_filehandler)
else:
    log.error(f'COC DB {Constant.APP_PATH.RESOURCE}/coc_db.json is missing')
    sys.exit(1)

if os.path.exists(Constant.APP_PATH.RESOURCE + '/coc_game_db.json') and os.path.isfile(
        Constant.APP_PATH.RESOURCE + '/coc_game_db.json'):
    with open(Constant.APP_PATH.RESOURCE + '/coc_game_db.json') as game_filehandler:
        current_level = json.load(game_filehandler)
else:
    log.error(f'COC Game DB {Constant.APP_PATH.RESOURCE}/coc_game_db.json is missing')
    sys.exit(1)

if os.path.exists(Constant.APP_PATH.RESOURCE + '/coc_game_builder.json') and os.path.isfile(
        Constant.APP_PATH.RESOURCE + '/coc_game_builder.json'):
    with open(Constant.APP_PATH.RESOURCE + '/coc_game_builder.json') as builder_filehandler:
        running_builder = json.load(builder_filehandler, object_hook=date_hook)
else:
    log.error(f'COC Builder DB {Constant.APP_PATH.RESOURCE}/coc_game_builder.json is missing')
    sys.exit(1)

current_th = 10
required_info = {}
priority_list = [1, 2, 3, 4, 5]
completed_time = [[12, 9]]

# re-iterate the builders
next_finish = None
for build in running_builder:
    if build['Status'] is None:
        continue

    if build['Status']:
        finish_time = build['start_time'] + timedelta(
            seconds=json_data[build['Item']]['Levels'][int(build['from_level'])][2] + 600)
        build['Time_to_complete'] = build['end_time'] - datetime.now(tz=timezone.utc)
        build['Time_to_complete'] = build['Time_to_complete'] - timedelta(
            microseconds=build['Time_to_complete'].microseconds)
    else:
        finish_time = build['start_time'] - timedelta(hours=10)
        build['Item'] = ''

    if finish_time > datetime.now(tz=timezone.utc):
        continue

    if build['Status']:
        print(f'{build["Name"]} Builder completed.')
        _update_runner = to_bool(input(f'{build["Name"]} completed building {build["Item"]} [y/n]:'))
    else:
        _update_runner = True

    if _update_runner and build['Status']:
        current_level[build['Item']]['Levels'][str(build['from_level'])] -= 1
        if str(build['from_level'] + 1) in current_level[build['Item']]['Levels']:
            current_level[build['Item']]['Levels'][str(build['from_level'] + 1)] += 1
        else:
            current_level[build['Item']]['Levels'][str(build['from_level'] + 1)] = 1

    # list down other items
    for sub_build in running_builder:
        if (not sub_build['Status']) or sub_build['Name'] == build['Name']:
            continue
        print('{0} updating {1} from {2} to {3}'.format(
            sub_build['Name'],
            sub_build['Item'],
            sub_build['from_level'],
            sub_build['from_level'] + 1
        ))

    _new_runner = to_bool(input(f'Going to schedule new item for {build["Name"]} [y/n]:'))

    if _update_runner and _new_runner:
        for ix, it in enumerate(list(sorted(current_level.keys())), start=1):
            print(f'{ix}. {it}')
        itm = input('Chose the running item from above(1..n):')
        build["Item"] = list(sorted(current_level.keys()))[int(itm) - 1]

        _update_to = int(input(f'{build["Name"]} updating the {build["Item"]} to:'))
        build['from_level'] = _update_to - 1

        _rem_time = input('Remaining time shown:')
        build['start_time'] = datetime.now(tz=timezone.utc) - timedelta(
            seconds=json_data[build['Item']]['Levels'][_update_to - 1][2] - to_times(_rem_time))
        build['end_time'] = build['start_time'] + timedelta(
            seconds=json_data[build['Item']]['Levels'][_update_to - 1][2])

        build['Time_to_complete'] = build['end_time'] - datetime.now(tz=timezone.utc)

        build['Status'] = Constant.Builders.RUNNING
    else:
        build = {
            "Name": build['Name'],
            'Status': Constant.Builders.INACTIVE,
            "Item": "None",
            "start_time": datetime.now(tz=timezone.utc),
            "from_level": 0,
            "end_time": datetime.now(tz=timezone.utc),
            "Time_to_complete": datetime.now(tz=timezone.utc) - datetime.now(tz=timezone.utc)

        }

with open(Constant.APP_PATH.RESOURCE + '/coc_game_builder.json', 'w') as json_filehandler:
    json.dump(running_builder, json_filehandler, default=datetime_serilizer, indent=4)

next_finish = sorted(
    filter(lambda x: x['Status'] is Constant.Builders.RUNNING, running_builder),
    key=lambda x: x['end_time'], reverse=False)[0]

for _name in filter(lambda x: int(current_level[x]['priority']) in priority_list, current_level.keys()):

    ct = json_data[_name]['Cost_Type']
    _total = 0
    required_info[_name] = {'Info': {}}
    _max_level = list()

    _total = sum(current_level[_name]['Levels'].values())
    _diff = json_data[_name]['Count'][current_th - 1] - _total

    if _diff != 0:
        print(f'Add {_diff} more {_name}')
        current_level[_name][0] = _diff

    for idx, _db_level in enumerate(json_data[_name]['Levels'], start=1):
        if _db_level[1] <= current_th:
            _max_level = _db_level.copy()
            _max_level.append(idx)

    current_level[_name]['Max_level'] = _max_level[3]

    for _cl in current_level[_name]['Levels'].keys():
        if int(_cl) == _max_level[3]:
            required_info[_name]['Info'][_cl] = {
                ct: 0,
                'Count': current_level[_name]['Levels'][_cl],
                'more_level': _max_level[3] - int(_cl),
                'percentage': 0,
                'Duration': 0
            }
        for idx in range(int(_cl), _max_level[3]):
            if _cl not in required_info[_name]['Info']:
                required_info[_name]['Info'][_cl] = {
                    ct: 0,
                    'Count': current_level[_name]['Levels'][_cl],
                    'more_level': _max_level[3] - int(_cl),
                    'percentage': 0,
                    'Duration': 0

                }

            required_info[_name]['Info'][_cl][ct] += (
                    json_data[_name]['Levels'][idx][0] * current_level[_name]['Levels'][_cl])

            required_info[_name]['Info'][_cl]['Duration'] += (
                    json_data[_name]['Levels'][idx][2] * current_level[_name]['Levels'][_cl])

        required_info[_name]['Info'][_cl]['percentage'] += (
                ((int(_cl) * 100) / _max_level[3]) * current_level[_name]['Levels'][_cl]
        )
    required_info[_name]['Duration'] = sum([
        required_info[_name]['Info'][items]['Duration']
        for items in required_info[_name]['Info'].keys()])

    required_info[_name]['Completed'] = sum([
        required_info[_name]['Info'][items]['percentage']
        for items in required_info[_name]['Info'].keys()
    ]) / json_data[_name]['Count'][current_th - 1]

overall_duration = str(timedelta(seconds=sum(
    [required_info[k]["Duration"] for k in required_info.keys()]) \
                                         / len(list(filter(lambda x: x['Status'] is not None, running_builder)))))

cent_complete = {}
for ty in sorted(required_info.keys(), key=lambda x: current_level[x]['priority'] and required_info[x]["Completed"],
                 reverse=True):
    log.info(
        f'{ty} with {current_level[ty]["priority"]} priority, completed percentage:{required_info[ty]["Completed"]:.2f}%')
    required_info[ty]["Duration"] = str(timedelta(seconds=required_info[ty]["Duration"]))
    if required_info[ty]["Completed"] < 75:
        log.info(json.dumps(current_level[ty], indent=4))
    elif required_info[ty]["Completed"] == 100:
        if "_100" not in cent_complete.keys():
            cent_complete["_100"] = list()
        cent_complete["_100"].append([ty, current_level[ty]["priority"]])
    elif int(required_info[ty]["Completed"] / 10) == 9:
        if "_90" not in cent_complete.keys():
            cent_complete["_90"] = list()
        cent_complete["_90"].append([ty, current_level[ty]["priority"]])
    elif int(required_info[ty]["Completed"] / 10) == 8:
        if "_80" not in cent_complete.keys():
            cent_complete["_80"] = list()
        cent_complete["_80"].append([ty, current_level[ty]["priority"]])

overall_centage = sum(
    [required_info[k]["Completed"] for k in required_info.keys()]) \
                  / len(required_info.keys())

print()
for _ in cent_complete.keys():
    if len(cent_complete[_]) > 0:
        print(f'List of {_.replace("_", "")}% completed Items:')
        for _i in sorted(cent_complete[_], key=lambda x: x[1]):
            print(f'{_i[1]} - {_i[0]}')
        print()

print()
log.info('#' * 50)
msg_str = f'Priority {",".join(map(str, priority_list))} items completed:{overall_centage:.2f}%'
print(msg_str)
log.info(msg_str)
print(f'with required time frame {overall_duration}')
log.info(f'with required time frame {overall_duration}')
msg_str = ('Next item to complete is {0} from {1} to {2} in {3}'.format(
    next_finish["Item"], next_finish["from_level"],
    next_finish["from_level"] + 1, next_finish["Time_to_complete"]))
print(msg_str)
log.info(msg_str)
log.info('#' * 50)
with open(Constant.APP_PATH.RESOURCE + '/report.json', 'w') as json_filehandler:
    json.dump(required_info, json_filehandler, indent=4)

with open(Constant.APP_PATH.RESOURCE + '/coc_game_db.json', 'w') as game_filehandler:
    json.dump(current_level, game_filehandler, default=datetime_serilizer, indent=4)

log.info('Done')
