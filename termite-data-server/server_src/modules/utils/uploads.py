import csv
import os


SPREADSHEET_DIR = None
PLAINTEXT_DIR = None


def spreadsheet_dir(request):
    global SPREADSHEET_DIR
    if not SPREADSHEET_DIR:
        SPREADSHEET_DIR = os.path.join(request.folder, 'uploads', 'csv')
    return SPREADSHEET_DIR


def plaintext_dir(request):
    global PLAINTEXT_DIR
    if not PLAINTEXT_DIR:
        PLAINTEXT_DIR = os.path.join(request.folder, 'uploads', 'plaintext')
    return PLAINTEXT_DIR


def save_spreadsheet(request, name, ssheet):
    if not os.path.isdir(spreadsheet_dir(request)):
        os.makedirs(spreadsheet_dir(request))
    ss_fpath = os.path.join(spreadsheet_dir(request), name + '.csv')
    with open(ss_fpath, 'w', encoding='utf-8') as outfile:
        fieldnames = set(ssheet[0])
        writer = csv.DictWriter(outfile, fieldnames=fieldnames, delimiter=',', quotechar='"')
        writer.writeheader()
        for r in ssheet[1:]:
            row = {k:v for k, v in r.items() if k in fieldnames}
            writer.writerow(row)


def save_plaintext(request, name, ptext):
    if not os.path.isdir(plaintext_dir(request)):
        os.makedirs(plaintext_dir(request))
    pt_fpath = os.path.join(plaintext_dir(request), name + '.txt')
    with open(pt_fpath, 'w', encoding='utf-8') as outfile:
        outfile.write(ptext)

