#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
from bs4 import BeautifulSoup
import scrape_common as sc

base_url = 'https://corona.so.ch'
url = f'{base_url}/bevoelkerung/daten/woechentlicher-situationsbericht/'
d = sc.download(url, silent=True)
soup = BeautifulSoup(d, 'html.parser')
pdf_url = soup.find(href=re.compile(r'\.pdf$')).get('href')
pdf_url = f'{base_url}{pdf_url}'

content = sc.pdfdownload(pdf_url, layout=True, silent=True)

"""
Hospitalisationen im Kanton  Anzahl Personen in Isolation  davon Kontakte in Quarantäne  Anzahl zusätzlicher Personen in Quarantäne nach Rückkehr aus Risikoland  Re- Wert***
6 (6)                        120 (71)                      280 (189)                     388 (280)                                                                1.46 (1.1)
"""

rows = []

date = sc.find(r'S\s?tand: (\d+\.\d+\.20\d{2})', content)
number_of_tests = sc.find(r'PCR-Tes\s?ts\sTotal\s+(\d+\'?\d+)\s', content).replace('\'', '')
res = re.search(r'Hospitalisationen im Kanton.*\d+ \(\d+\)\s+(\d+) \(\d+\)\s+(\d+) \(\d+\)\s+(\d+) \(\d+\)\s+\d\.\d+ \(\d\.\d+\)', content, re.DOTALL)
if res is not None:
    data = sc.DayData(canton='SO', url=pdf_url)
    data.datetime = date
    data.tested = number_of_tests
    data.isolated = res[1]
    data.quarantined = res[2]
    data.quarantine_riskareatravel = res[3]
    rows.append(data)


url = f"{base_url}/index.php?id=27979"
d = sc.download(url, silent=True)
d = d.replace("&nbsp;", " ")

soup = BeautifulSoup(d, 'html.parser')
data_table = soup.find('h2', text=re.compile("Situation Kanton Solothurn")).find_next("table")
if data_table:
    headers = [cell.string for cell in data_table.find('tr').find_all('th')]
    for row in data_table.find_all('tr'):
        data = sc.DayData(canton='SO', url=url)
        col_num = 0
        tmp_date = None
        tmp_time = None
        for cell in row.find_all(['td']):
            if headers[col_num] == 'Datum':
                tmp_date = cell.string.strip()
            elif headers[col_num] == 'Zeit':
                tmp_time = cell.string.strip()
            elif headers[col_num] == 'Bestätigte Fälle (kumuliert)':
                data.cases = cell.string.strip()
            elif headers[col_num] == 'Todesfälle (kumuliert)':
                data.deaths = cell.string.strip()
            elif headers[col_num] == 'Im Kanton Hospitalisierte Personen':
                data.hospitalized = cell.string.strip()
            col_num += 1
        if data and tmp_date and tmp_time and not tmp_date.startswith('bis '):
            data.datetime = f"{tmp_date} {tmp_time}".strip()
            rows.append(data)


# and scrape the main page as well
url = "https://corona.so.ch/"
d = sc.download(url, silent=True)
soup = BeautifulSoup(d, 'html.parser')
title = soup.find('h3', text=re.compile("Situation Kanton Solothurn"))
data = sc.DayData(canton='SO', url=url)
data.datetime = sc.find(r'Stand\s*(.+)\s*Uhr', title.string)
table = title.find_next('table')
for table_row in table.find_all('tr'):
    items = table_row.find_all('td')
    name = items[0].string
    value = items[1].string
    if name == 'Laborbestätigte Infektionen (kumuliert):':
        data.cases = value
        continue
    if name == 'Verstorbene Personen (kumuliert):':
        data.deaths = value
        continue
    if name == 'Aktuell im Kanton hospitalisierte Personen:':
        data.hospitalized = value
        continue
    if name == 'Davon intensivmedizinisch betreut:':
        data.icu = value
        continue
print(data)
if data:
    rows.append(data)


is_first = True
# skip first row
for row in rows:
    if not is_first:
        print('-' * 10)
    is_first = False
    print(row)
