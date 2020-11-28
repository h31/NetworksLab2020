import csv
import re

'''Parse csv with options'''


def retrieve_options():
    with open('options.csv', mode='r') as options_file:
        reader = csv.reader(options_file)
        regex = re.compile('\([^()]*\)')
        options_dict = {int(row[0]): re.sub(regex, '', row[1]).replace('-', '_').replace('\n', '_').replace('.', '_').
            replace('/', '_').rstrip().replace(' ', '_').lower() for row in reader}
        print(options_dict)


if __name__ == "__main__":
    retrieve_options()
