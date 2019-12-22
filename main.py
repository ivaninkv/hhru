import argparse
import areas


def main():    
    parser = argparse.ArgumentParser()        
    parser.add_argument('-da', '--download_area', help='Скачать справочник регионов.', action='store_true')
    args = parser.parse_args()
    if args.download_area:
        areas.download_areas()
        

if __name__ == '__main__':
  main()