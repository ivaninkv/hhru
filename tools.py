import os

CSV_NAME = 'csv'

def create_csv_dir():
    if not os.path.isdir(CSV_NAME):
        os.mkdir(CSV_NAME)