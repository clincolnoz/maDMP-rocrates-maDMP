import copy
import json
import jsonschema
import os
import sys
import urllib
import argparse

class color:
   PURPLE = '\033[95m'
   CYAN = '\033[96m'
   DARKCYAN = '\033[36m'
   BLUE = '\033[94m'
   GREEN = '\033[92m'
   YELLOW = '\033[93m'
   RED = '\033[91m'
   BOLD = '\033[1m'
   UNDERLINE = '\033[4m'
   END = '\033[0m'

    
def read_json_url(url):
    response = urllib.request.urlopen(url)
    data = json.loads(response.read())
    return data


def read_json_local(path):
    with open(path, 'r') as in_file:
        data = json.load(in_file)
    return data

def findDiff(d1, d2, path="", report=[]):
    for k in d1:
        #print(k)
        if (k not in d2):
            print (path, ":")
            print (k + " as key not in d2", "\n")
            report.append(''.join((path, ":")))
            report.append(''.join((k + " as key not in d2", "\n")))
        else:
            if type(d1[k]) is dict:
                if path == "":
                    path = k
                else:
                    path = path + "->" + k
                findDiff(d1[k],d2[k], path, report)
            elif isinstance(d1[k], list):
                for idx, item in enumerate(d1[k]):
                    if isinstance(item, dict):
                        #path = path + "->" + k + '_' + str(idx)
                        findDiff(d1[k][idx],d2[k][idx], path, report)
            else:
                if d1[k] != d2[k]:
                    print (path, ":")
                    print (" - ", k," : ", d1[k])
                    print (" + ", k," : ", d2[k])
                    report.append(''.join((path, ":")))
                    report.append(''.join((" - ", k," : ", d1[k])))
                    report.append(''.join((" + ", k," : ", d2[k], '\n')))
    return report

def write_report(args, report):
    if not args.path_report:
        path_report = os.path.join(os.path.split(args.path_d1)[0], 'report.txt')
    else:
        path_report = args.path_report
    with open(path_report, 'w') as fn:
        for i in report:
            fn.write(str(i) + '\n')

# print ("comparing d1 to d2:")
# print (findDiff(d1,d2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-path_d1', '--path_d1', type=str, required=True, help='path of first dictionary to compare')   
    parser.add_argument('-path_d2', '--path_d2', type=str, required=True, help='path of second dictionary to compare')   
    parser.add_argument('-path_report', '--path_report', type=str, help='path to save comparison report. If none defaults to path of first dict',
                        default=None)   
    args = parser.parse_args()

    d1 = read_json_local(args.path_d1)
    d2 = read_json_local(args.path_d2)
    print ("comparing d1 to d2:")
    report = findDiff(d1,d2)
    write_report(args, report)
    