import os
import requests
from bs4 import BeautifulSoup
from decimal import Decimal

CSV_NAME = 'csv'
PRINT_EVEREY_VACS = 50


def create_csv_dir():
    if not os.path.isdir(CSV_NAME):
        os.mkdir(CSV_NAME)


def load_curr_rates(vals):
    r = requests.get('http://www.cbr.ru/scripts/XML_daily.asp')
    cr = BeautifulSoup(r.text, 'lxml')
    cur = {}
    for v in vals:
        try:
            node = cr.find(text=v).parent.parent
            cur[v] = {'value': Decimal(node.value.text.replace(',', '.'))}
        except Exception as err:
            print(err)
    return cur
