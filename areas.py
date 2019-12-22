import requests
import pandas as pd
from pandas.io.json import json_normalize
import tools


def download_areas():    
    r = requests.get('https://api.hh.ru/areas')
    ar = r.json()
    df = pd.concat([json_normalize(ar), 
                    json_normalize(ar, record_path=['areas']*1), 
                    json_normalize(ar, record_path=['areas']*2)])
    df.drop(['areas'], axis=1, inplace=True)
    tools.create_csv_dir()
    df.to_csv(f'{tools.CSV_NAME}/areas.csv', header=True, index=False)
