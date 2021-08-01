#!/usr/bin/env python3
from logging.handlers import TimedRotatingFileHandler

from requests_html import HTMLSession
from bs4 import BeautifulSoup

import numpy as np
import json
import re
import os
import logging
import sys

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

log.info(Others.Yam('Start'))
log.info('#' * 50)

session = HTMLSession()
BASE_URL = r'https://coc.guide'
urls = ['defense', 'resource', 'army', 'trap']

item_urls = list()
json_data = {}
blacklist = ['goblinth02', 'townhall12', 'townhall13', 'townhall14', 'siegeworkshop', 'freezebomb', 'halloweenbomb',
             'santatrap', 'shrinktrap', 'tornadotrap']

for url in urls:
    html_doc = session.get(BASE_URL + '/' + url)
    soup = BeautifulSoup(html_doc.text, 'html.parser') \
        .find('div', attrs={'class': 'items'}) \
        .find_all('div', attrs={'class': 'item-link'})
    for s in soup:
        item_urls.append(BASE_URL + s.find('a').get('href'))


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


for item_url in item_urls:
    html_doc = session.get(item_url)
    soup = BeautifulSoup(html_doc.text, 'html.parser')
    _pos = {'spend': 0, 'TH': None}
    _name = soup.find('div', attrs={'role': 'main'}).find('h1').text

    if item_url.split('/')[-1].lower() in blacklist:
        log.debug(f'Ignoring {_name}')
        continue
    else:
        log.info(f'Running {_name}')
    json_data[_name] = {
        'Count': list(),
        'Levels': list(),
        'Cost_Type': None,
    }

    # Table 1
    table_soup = soup.find('div', attrs={'class': 'sticky-table-wrapper'}).find('table')
    for tr in table_soup.find_all('tr'):
        td = tr.find_all('td')
        if len(td) == 0:
            _p = 0
            for th in tr.find_all('th'):
                if th.find('img') is not None and th.find('img').get('alt').lower() in ['gold', 'elixir',
                                                                                        'dark elixir']:
                    json_data[_name]['Cost_Type'] = th.find('img').get('alt')
                    _pos['spend'] = _p
                elif th.text.strip().upper() == 'TH':
                    _pos['TH'] = _p
                elif th.find('img') is not None and th.find('img').get('src').endswith('clock.png'):
                    _pos['Duration'] = _p
                _p += 1
        else:
            val = 0
            time_d = td[_pos['Duration']].text.replace(' ', '')
            if time_d != 'None':
                val = int(to_times(td[_pos['Duration']].text.replace(' ', '')))
            json_data[_name]['Levels'].append([int(td[_pos['spend']].text.replace(',', '')),
                                               int(td[_pos['TH']].text.replace(', ', '')),
                                               val])
        # Table 2
        table_soup = soup.find_all('table', attrs={'class': 'info-table'})[1]
        table_head = table_soup.find('thead').find_all('th')
        table_body = table_soup.find('tbody').find_all('td')

        zero_list = np.zeros(int(table_head[0].text.strip()) - 1, np.int).tolist()
        json_data[_name]['Count'].extend(zero_list)
        for _i in range(0, len(table_body)):
            json_data[_name]['Count'].append(int(table_body[_i].text.strip()))

with open(Constant.APP_PATH.RESOURCE + '/coc_db.json', 'w') as json_filehandler:
    json.dump(json_data, json_filehandler, indent=4)




log.info('#' * 50)
log.info(Others.Yam('Done'))
log.info('#' * 50)
