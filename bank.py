#! /usr/bin/env python
import re
import math
import time
import json
import requests
import pandas as pd
import logging as log
import yfinance as yf

from os import path
from datetime import datetime, timedelta

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)

log.basicConfig(format='%(asctime)s - %(name)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S', level=log.DEBUG)
log.warning('Start')
base_path = path.dirname(path.dirname(path.abspath(__file__)))
log.getLogger("urllib3").setLevel(log.WARNING)
log.getLogger("requests").setLevel(log.WARNING)



def isOlder(filename, days=10):
    file_time = path.getmtime(filename)
    return (time.time() - file_time) / 3600 > 24 * days


import PyPDF2


def get_pdf_file():
    pdf_url = r'https://www1.nseindia.com/content/indices/ind_nifty_bank.pdf'
    local_pdf = path.join(base_path, 'resource', 'ind_nifty_bank.pdf')
    ticker_file = path.join(base_path, 'resource', 'ticker.csv')

    if not path.exists(ticker_file):
        pd.DataFrame(columns=['Name', 'Symbol', 'date_time']).to_csv(ticker_file, index=False)

    if (not path.exists(local_pdf)) or isOlder(local_pdf):
        log.info('Downloading the nifty bank pdf')
        r = requests.get(pdf_url, allow_redirects=True)
        open(local_pdf, 'wb').write(r.content)

    # read ticker file
    ticker = pd.read_csv(ticker_file,index_col=False, parse_dates=['date_time'])
    ticker = ticker[ticker['date_time'] > (datetime.now()-timedelta(days=10))]

    # extract data
    pdfFileObj = open(local_pdf, 'rb')
    pdfReader = PyPDF2.PdfFileReader(pdfFileObj)
    _df = pd.DataFrame()
    reader_flag = False
    for line in pdfReader.getPage(0).extractText().split("\n"):
        if 'Top constituents by weightage' in line:
            reader_flag = True
            continue
        if '# QTD,YTD and 1' in line:
            reader_flag = False

        if not reader_flag:
            continue

        data = [i for i in re.split('^(.+?) ([\d.]+)$', line.rstrip().lstrip()) if i]
        _dat = ticker[ticker['Name'] == data[0]]

        if _dat.shape[0] == 0:
            url = r'https://query2.finance.yahoo.com/v1/finance/search'
            res = requests.get(url, headers={'user-agent': 'Mozilla/5.0 Chrome/105.0.0.0'},
                               params={'q': data[0].replace('Ltd.', ''),
                                       'lang': 'en-US', 'region': 'US', 'quotesCount': 10, 'newsCount': 2,
                                       'listsCount': 2, 'enableFuzzyQuery': False,
                                       'quotesQueryId': 'tss_match_phrase_query',
                                       'multiQuoteQueryId': 'multi_quote_single_token_query',
                                       'newsQueryId': 'news_cie_vespa', 'enableCb': True, 'enableNavLinks': True,
                                       'enableEnhancedTrivialQuery': True, 'enableResearchReports': True,
                                       'enableCulturalAssets': True, 'researchReportsCount': 2
                                       })
            _tdf = pd.DataFrame(json.loads(res.text)['quotes'])
            symbol = _tdf[_tdf['exchange'] == 'NSI'].get('symbol').to_list()

            ticker = pd.concat([ticker, pd.DataFrame(
                {'Name': data[0],
                 'Symbol': symbol[0],
                 'date_time': datetime.now()},
                index=[0])])

        data.append(yf.Ticker(_dat.get('Symbol').to_list()[0]).info['regularMarketPrice'])
        _df = pd.concat([_df, pd.DataFrame(data=[data], columns=['Name', 'Weight','cmp'])])

    ticker.to_csv(ticker_file, index=False)
    return _df


df = get_pdf_file()
# print(get_pdf_file())
# df = get_df()

bank = yf.Ticker("^NSEBANK")

df.columns = [re.sub(' +', '_', i.lower()) for i in df.columns]
df['weight'] = df['weight'].str.replace('%', '').astype(float)

df['overall_wt'] = ((bank.info['regularMarketPrice'] * df['weight']) / 100) \
    .astype(float)

df['no_share'] = (df['overall_wt'] / (df['cmp'].astype(float))).apply(math.floor).astype(int)
df['total_amount'] = df['no_share'] * (df['cmp'].astype(float))
df = df.reset_index(drop=True)
log.info("\n{0}".format(df))

log.warning('End')
