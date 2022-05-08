#!/usr/bin/env .venv/bin/python3
# -*- coding: utf-8 -*-

import argparse
import subprocess
import os
import shutil


DEFAULT_DATASET = 'infovis'
DATASETS = [DEFAULT_DATASET, '20newsgroups', 'nsfgrants', 'nsf25k', 'nsf10k', 'nsf1k', 'poliblogs', 'gjp', 'fomc', 'CR_financial_collapse',
            'CR_stock_market_plunge', 'FCIC_final_report', 'FCIC_first_hearing', 'FR_federal_open_market_committee', 'FR_monetary_policy_hearings']

DEFAULT_MODEL = 'mallet'
MODELS = [DEFAULT_MODEL, 'treetm', 'stmt', 'stm', 'gensim']


def sh_exec(command):
    p = subprocess.Popen(command, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT)
    while p.poll() is None:
        line = str(p.stdout.readline(), encoding='utf-8').rstrip('\n')
        if len(line) > 0:
            print(line)


def Demonstrate(dataset, model, is_quiet, force_overwrite):
    database_folder = 'data/demo/{}/corpus'.format(dataset)
    corpus_folder = 'data/demo/{}/corpus'.format(dataset)
    model_folder = 'data/demo/{}/model-{}'.format(dataset, model)
    app_name = '{}_{}'.format(dataset, model)

    def PrepareDataset():
        executable = 'bin/fetch_dataset.sh'
        sh_exec([executable, dataset])

    def PrepareModel():
        executable = 'bin/setup_{}.sh'.format(model)
        command = [executable]
        sh_exec(command)

    def PrepareOthers():
        executable = 'bin/setup_mallet.sh'
        command = [executable]
        sh_exec(command)

        executable = 'bin/setup_corenlp.sh'
        command = [executable]
        sh_exec(command)

    def TrainModel():
        executable = 'bin/train_{}.py'.format(model)
        command = [executable, corpus_folder, model_folder]
        if is_quiet:
            command.append('--quiet')
        if force_overwrite:
            command.append('--overwrite')
        sh_exec(command)

    def ImportModel():
        executable = 'bin/read_{}.py'.format(model)
        command = [executable, app_name, model_folder,
                   corpus_folder, database_folder]
        if is_quiet:
            command.append('--quiet')
        if force_overwrite:
            command.append('--overwrite')
        sh_exec(command)

    print('--------------------------------------------------------------------------------')
    print('Build a topic model ({}) using a demo dataset ({})'.format(model, dataset))
    print('  database = {}'.format(database_folder))
    print('    corpus = {}'.format(corpus_folder))
    print('     model = {}'.format(model_folder))
    print('       app = {}'.format(app_name))
    print('--------------------------------------------------------------------------------')

    PrepareDataset()
    PrepareModel()
    PrepareOthers()
    TrainModel()
    ImportModel()


def process_spreadsheet(spreadsheet: str, datasets_folder: str):
    dataset_name = os.path.splitext(os.path.basename(spreadsheet))[0]
    dataset_folder = os.path.join(datasets_folder, dataset_name)
    if not os.path.exists(dataset_folder):
        os.mkdir(dataset_folder)
    corpus_folder = os.path.join(dataset_folder, 'corpus')
    if not os.path.exists(corpus_folder):
        os.mkdir(corpus_folder)
    else:
        shutil.rmtree(corpus_folder)
        os.mkdir(corpus_folder)

    model = 'mallet'
    model_folder = os.path.join(os.path.abspath('tools'), model)
    is_quiet = False
    force_overwrite = True

    # Import into corpus sqlite database
    executable = 'bin/import_corpus.py'
    command = [executable, corpus_folder, spreadsheet]
    sh_exec(command)

    # Export into corpus sqlite database
    executable = 'bin/export_corpus.py'
    command = [executable, corpus_folder, os.path.join(corpus_folder, 'corpus.txt')]
    sh_exec(command)

    # Install mallet
    executable = 'bin/setup_mallet.sh'
    command = [executable]
    sh_exec(command)

    # Install corenlp
    executable = 'bin/setup_corenlp.sh'
    command = [executable]
    sh_exec(command)

    # Train
    executable = 'bin/train_{}.py'.format(model)
    command = [executable, corpus_folder, model_folder]
    if is_quiet:
        command.append('--quiet')
    if force_overwrite:
        command.append('--overwrite')
    sh_exec(command)

    # Import
    executable = 'bin/read_{}.py'.format(model)
    application_name = dataset_name
    # Overwrite application
    application_folder = os.path.join(os.path.abspath('apps'), application_name)
    if os.path.exists(application_folder):
        shutil.rmtree(application_folder)
    command = [executable, application_name, model_folder,
                corpus_folder, corpus_folder]
    if is_quiet:
        command.append('--quiet')
    if force_overwrite:
        command.append('--overwrite')
    sh_exec(command)

    print(spreadsheet)


def main():
    # parser = argparse.ArgumentParser( description = 'Import a MALLET topic model as a web2py application.' )
    # parser.add_argument( 'dataset'     , nargs = '?', type = str, default = DEFAULT_DATASET, choices = DATASETS, help = 'Dataset identifier' )
    # parser.add_argument( 'model'       , nargs = '?', type = str, default = DEFAULT_MODEL  , choices = MODELS  , help = 'Model type' )
    # parser.add_argument( '--quiet'     , const = True, default = False, action = 'store_const', help = 'Show fewer debugging messages' )
    # parser.add_argument( '--overwrite' , const = True, default = False, action = 'store_const', help = 'Overwrite any existing model'  )
    # args = parser.parse_args()
    # Demonstrate( args.dataset, args.model, args.quiet, args.overwrite )

    datasets_folder = 'data'
    # List all spreadsheets
    folder = 'dataset_src/uploads/csv'
    for spreadsheet in os.listdir(folder):
        process_spreadsheet(os.path.join(os.path.abspath(folder), spreadsheet),
                            os.path.abspath(datasets_folder))


if __name__ == '__main__':
    main()
