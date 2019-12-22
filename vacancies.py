import requests
import pandas as pd
import math
import tools


CUR_VALUES = {}


def calc_salary(from_, to_, gross, curr):
    if from_ is None:
        from_ = float('NaN')
    if to_ is None:
        to_ = float('NaN')
    if math.isnan(from_) and math.isnan(to_) or gross is None:
        res = float('NaN')
    if math.isnan(from_):       
        res = to_ if gross else to_ / 0.87
    elif math.isnan(to_):
        res = from_ if gross else from_ / 0.87        
    else:
        res = (from_ + to_) / 2
        if not gross:
            res /= 0.87
    res *= CUR_VALUES.get(curr, 1)
    return res


def get_vac_urls(search_text, area):
    vacs = []
    r = requests.get('https://api.hh.ru/vacancies',
                     params={'text': search_text, 'area': area, 'per_page': 100})
    per_page = r.json()['per_page']
    pages = r.json()['pages']
    for p in range(pages):
        r = requests.get('https://api.hh.ru/vacancies', params={
                         'page': p, 'per_page': per_page, 'text': search_text, 'area': area}).json()['items']
        for i in range(len(r)):
            vacs.append(r[i]['url'])
    return vacs


def get_vac_df(vacs):
    det_vac = []
    for vac in vacs:
        det_vac.append(requests.get(vac).json())
        if len(det_vac) % tools.PRINT_EVEREY_VACS == 0:
            print(f'{len(det_vac)} of {len(vacs)} vacancies.')
    vac_df = pd.DataFrame(det_vac)[['id', 'name', 'alternate_url', 'description', 'employer',
                                    'employment', 'experience', 'key_skills', 'salary', 'schedule', 'specializations']]
    return vac_df


def download_vacancies(search_text, area):
    df = get_vac_df(get_vac_urls(search_text, area))
    df = df.join(pd.read_json(df.salary.to_json()).T)
    df.drop('salary', axis=1, inplace=True)
    df = df.join(pd.read_json(df.employer.to_json()).T['id'], rsuffix='_empl')
    df.drop('employer', axis=1, inplace=True)
    df.rename(columns={'id_empl': 'empl_id'}, inplace=True)
    CUR_VALUES = tools.load_curr_rates(df['currency'].unique().tolist())
    df['salary'] = df.apply(lambda x: calc_salary(
        x['from'], x['to'], x['gross'], x['currency']), axis=1)
    df['currency'] = df['currency'].apply(
        lambda x: 'RUR' if x in CUR_VALUES else x)
    df.drop(['from', 'to', 'gross'], axis=1, inplace=True)
    df[['id', 'name', 'salary', 'currency', 'empl_id']].to_csv(
        f'{tools.CSV_NAME}/vac.csv', header=True, index=False)
