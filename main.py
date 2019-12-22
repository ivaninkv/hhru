import argparse
import areas
import vacancies


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-da', '--download_area',
                        help='Скачать справочник регионов.', action='store_true')
    parser.add_argument('-t', '--text', help='Поисковый запрос.')
    parser.add_argument('-a', '--area', help='Регион.', default=113)
    args = parser.parse_args()
    if args.download_area:
        areas.download_areas()
    if args.text:
        vacancies.download_vacancies(args.text, args.area)


if __name__ == '__main__':
    main()
