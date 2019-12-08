import requests
import pandas as pd
import json
import math
import argparse
from bs4 import BeautifulSoup
from decimal import Decimal


CUR_VALUES = {}

def load_curr_rates(vals):
  r = requests.get('http://www.cbr.ru/scripts/XML_daily.asp')
  cr = BeautifulSoup(r.text, 'lxml')
  cur = {}
  for v in vals:    
      try:
          node = cr.find(text=v).parent.parent
          cur[v] = {'value': Decimal(node.value.text.replace(',', '.'))}
      except:
          pass

  return cur


def calc_salary(from_, to_, gross, curr):  
  if from_ == None:
    from_ = float('NaN')
  if to_ == None:
    to_ = float('NaN')
  if math.isnan(from_) and math.isnan(to_) or gross == None:
    res = float('NaN')
  if math.isnan(from_):
    if gross == False:
      res = to_ / 0.87
    else:
      res = to_
  elif math.isnan(to_):
    if gross == False:
      res = from_ / 0.87
    else:
      res = from_ 
  else:
    res = (from_ + to_) / 2
    if gross == False:
      res /= 0.87
  res *= CUR_VALUES.get(curr, 1)
  
  return res


def get_vac_urls(args):
  vacs = []
  r = requests.get('https://api.hh.ru/vacancies', params={'text':args.text, 'area':args.area, 'per_page':100})
  per_page = r.json()['per_page']
  pages = r.json()['pages']
  for p in range(pages):    
    r = requests.get('https://api.hh.ru/vacancies', params={'page': p, 'per_page':per_page, 'text':args.text, 'area':args.area}).json()['items']
    for i in range(len(r)):       
        vacs.append(r[i]['url'])

  return vacs


def get_vac_df(vacs):  
  det_vac = []
  for vac in vacs:
    det_vac.append(requests.get(vac).json())
    if len(det_vac) % 50 == 0:
      print(f'{len(det_vac)} of {len(vacs)}')
  vac_df = pd.DataFrame(det_vac)[['id', 'name', 'alternate_url', 'description', 'employer', 'employment', 'experience', 'key_skills', 'salary', 'schedule', 'specializations']]

  return vac_df


def get_empl_df(vac_df):
  empls = set()
  for i in range(len(vac_df)):
    try:      
      empls.add(vac_df.employer[i]['url'])
    except KeyError:      
      print(f"Невозможно найти информацию о работодателе в вакансии {vac_df['alternate_url'][i]}")

  det_empl = []
  for empl in empls:
    det_empl.append(requests.get(empl).json())
  empl_df = pd.DataFrame(det_empl)[['id', 'name', 'industries']]

  return empl_df


def get_ind_df(empl_df):
  industries = []
  for i in range(len(empl_df.id)):        
    for j in empl_df.industries[i]:        
        industries.append([empl_df.id[i], j['id'], j['name']])          
  ind_df = pd.DataFrame(industries, columns=['empl_id', 'id', 'name'])

  return ind_df


def get_skills_df(vac_df):
  skills = []
  for i in range(len(vac_df.id)):        
    for j in vac_df.key_skills[i]:        
      skills.append([vac_df.id[i], j['name']])  
  skill_df = pd.DataFrame(skills, columns=['vac_id', 'skill_name'])

  return skill_df


def get_prof_df(vac_df):
  prof = []
  for i in range(len(vac_df.id)):        
    for j in vac_df.specializations[i]:        
      prof.append([vac_df.id[i], j['profarea_id'], j['profarea_name']])
  prof_df = pd.DataFrame(prof, columns=['vac_id', 'prof_id', 'prof_name'])
  prof_df.drop_duplicates(inplace=True)
  
  return prof_df


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument('-t', '--text', help='Текстовая строка поиска вакансий.', required=True)
  parser.add_argument('-a', '--area', help='Регион.', default=1)
  args = parser.parse_args()

  # prepare dataframes
  vacs = get_vac_urls(args)
  vac_df = get_vac_df(vacs)
  empl_df = get_empl_df(vac_df)
  ind_df = get_ind_df(empl_df)
  empl_df.drop('industries', axis=1, inplace=True)
  skill_df = get_skills_df(vac_df)
  vac_df.drop('key_skills', axis=1, inplace=True)
  prof_df = get_prof_df(vac_df)
  vac_df.drop('specializations', axis=1, inplace=True)

  vac_df = vac_df.join(pd.read_json(vac_df.salary.to_json()).T)
  vac_df.drop('salary', axis=1, inplace=True)
  vac_df = vac_df.join(pd.read_json(vac_df.employer.to_json()).T['id'], rsuffix='_empl')
  vac_df.drop('employer', axis=1, inplace=True)
  vac_df.rename(columns={'id_empl':'empl_id'}, inplace=True)

  CUR_VALUES = load_curr_rates(vac_df['currency'].unique().tolist())  
  vac_df['salary'] = vac_df.apply(lambda x: calc_salary(x['from'], x['to'], x['gross'], x['currency']), axis=1)
  vac_df['currency'] = vac_df['currency'].apply(lambda x: 'RUR' if x in CUR_VALUES else x)
  vac_df.drop(['from', 'to', 'gross'], axis=1, inplace=True)

  # export to csv
  empl_df.to_csv('csv/empl.csv', header=True, index=False)
  ind_df.to_csv('csv/ind.csv', header=True, index=False)
  skill_df.to_csv('csv/skills.csv', header=True, index=False)
  prof_df.to_csv('csv/prof.csv', header=True, index=False)
  vac_df[['id', 'name', 'salary', 'currency', 'empl_id']].to_csv('csv/vac.csv', header=True, index=False)

  # join and export all data in 1 file
  empl_df.columns = ['empl_id', 'empl_name']
  ind_df.columns = ['empl_id', 'ind_id', 'ind_name']
  skill_df.columns = ['vac_id', 'skill_name']
  prof_df.columns = ['vac_id', 'prof_id', 'prof_name']
  all_data = vac_df[['id', 'name', 'salary', 'currency', 'empl_id']]
  all_data = pd.merge(all_data, empl_df, how='outer', left_on='empl_id', right_on='empl_id')
  all_data = pd.merge(all_data, ind_df, how='outer', left_on='empl_id', right_on='empl_id')
  all_data = pd.merge(all_data, skill_df, how='outer', left_on='id', right_on='vac_id')
  all_data.drop(['vac_id'], axis=1, inplace=True)
  all_data = pd.merge(all_data, prof_df, how='outer', left_on='id', right_on='vac_id')
  all_data.drop(['vac_id'], axis=1, inplace=True)
  all_data.to_csv('csv/all_data.csv', header=True, index=False)

if __name__ == '__main__':
  main()