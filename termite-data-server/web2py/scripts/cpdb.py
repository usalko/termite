import os
import sys
from collections import deque
import string
import argparse
import io
import operator
import pickle
from collections import deque
import math
import re
import cmd
try:
  import pyreadline as readline
except ImportError:
  import readline
try:
    from gluon import DAL
except ImportError as err:
    print('gluon path not found')
from functools import reduce
import functools


class refTable(object):
    def __init__(self):
        self.columns = None
        self.rows = None

    def getcolHeader(self, colHeader):
        return "{0}".format(' | '.join([string.join(string.strip('**{0}**'.format(item)),
                                                    '') for item in colHeader]))

    def wrapTable(
        self, rows, hasHeader=False, headerChar='-', delim=' | ', justify='left',
            separateRows=False, prefix='', postfix='', wrapfunc=lambda x: x):

        def rowWrapper(row):

            '''---
                    newRows is returned like
                            [['w'], ['x'], ['y'], ['z']]
                                                                    ---'''
            newRows = [wrapfunc(item).split('\n') for item in row]
            self.rows = newRows
            '''---
                        rowList gives like newRows but
                            formatted like [[w, x, y, z]]
                                                                ---'''
            rowList = [[substr or '' for substr in item]
                       for item in map(None, *newRows)]
            return rowList

        logicalRows = [rowWrapper(row) for row in rows]

        columns = map(None, *reduce(operator.add, logicalRows))
        self.columns = columns

        maxWidths = [max(
                     [len(str
                        (item)) for
                      item in column]
                     ) for column
                     in columns]

        rowSeparator = headerChar * (len(prefix) + len(postfix) + sum(maxWidths) +
                                     len(delim) * (len(maxWidths) - 1))

        justify = {'center': str
                   .center,
                   'right': str
                   .rjust,
                   'left': str.
                   ljust
                   }[justify
                     .lower(
                     )]

        output = io.StringIO()

        if separateRows:
            print(rowSeparator, file=output)

        for physicalRows in logicalRows:
            for row in physicalRows:
                print(\
                    prefix + delim.join([
                                        justify(str(item), width) for (
                                        item, width) in zip(row, maxWidths)]
                                        ) + postfix, file=output)

            if separateRows or hasHeader:
                print(rowSeparator, file=output)
                hasHeader = False
        return output.getvalue()

    def wrap_onspace(self, text, width):
        return functools.reduce(lambda line, word, width=width: '{0}{1}{2}'
                      .format(line, ' \n'[(len(
                                           line[line.rfind('\n'
                                                           ) + 1:]) + len(
                                           word.split('\n', 1)[0]) >=
                                           width)], word), text.split(' '))

    def wrap_onspace_strict(self, text, width):
        wordRegex = re.compile(r'\S{' + str(width) + r',}')
        return self.wrap_onspace(
            wordRegex.sub(
                lambda m: self.
                wrap_always(
                    m.group(), width), text
            ), width)

    def wrap_always(self, text, width):
        return '\n'.join(
            [text[width * i:width * (i + 1
                                     )] for i in range(
             int(math.ceil(1. * len(
             text) / width)))])


class tableHelper():
    def __init__(self):
        self.oTable = refTable()

    def getAsRows(self, data):
        return [row.strip().split(',') for row in data.splitlines()]

    def getTable_noWrap(self, data, header=None):
        rows = self.getAsRows(data)
        if header is not None:
            hRows = [header] + rows
        else:
            hRows = rows
        table = self.oTable.wrapTable(hRows, hasHeader=True)
        return table

    def getTable_Wrap(self, data, wrapStyle, header=None, width=65):
        wrapper = None
        if len(wrapStyle) > 1:
            rows = self.getAsRows(data)
            if header is not None:
                hRows = [header] + rows
            else:
                hRows = rows

            for wrapper in (self.oTable.wrap_always,
                            self.oTable.wrap_onspace,
                            self.oTable.wrap_onspace_strict):
                return self.oTable.wrapTable(hRows, hasHeader=True, separateRows=True, prefix='| ', postfix=' |', wrapfunc=lambda x:
                                             wrapper(x, width))
        else:
            return self.getTable_noWrap(data, header)

    def getAsErrorTable(self, err):
        return self.getTable_Wrap(err, None)


class console:
    def __init__(self, prompt, banner=None):
        self.prompt = prompt
        self.banner = banner
        self.commands = {}
        self.commandSort = []
        self.db = None

        for i in dir(self):
            if "cmd_" == i[:4]:
                cmd = i.split("cmd_")[1].lower()
                self.commands[cmd] = getattr(self, i)
                try:
                    self.commandSort.append((int(self
                                                 .commands[cmd].__doc__.split(
                                                 "|")[0]), cmd))
                except:
                    pass

        self.commandSort.sort()
        self.commandSort = [i[1] for i in self.commandSort]

        self.var_DEBUG = False
        self.var_tableStyle = ''

        self.configvars = {}
        for i in dir(self):
            if "var_" == i[:4]:
                var = i.split("var_")[1]
                self.configvars[var] = i

    def setBanner(self, banner):
        self.banner = banner

    def execCmd(self, db):
        self.db = db
        print(self.banner)
        while True:
            try:
                command = raw_input(self.prompt)
                try:
                    self.execCommand(command)
                except:
                    self.execute(command)
            except KeyboardInterrupt:
                break
            except EOFError:
                break
            except Exception as a:
                self.printError(a)
        print("\r\n\r\nBye!...")
        sys.exit(0)

    def printError(self, err):
        sys.stderr.write("Error: {0}\r\n".format(str(err),))
        if self.var_DEBUG:
            pass

    def execute(self, cmd):
        try:
            if not '-table ' in cmd:
                exec ('{0}'.format(cmd))
            else:
                file = None
                table = None

                fields = []
                items = string.split(cmd, ' ')
                invalidParams = []
                table = self.getTable(items[1])
                allowedParams = ['fields', 'file']
                for i in items:
                    if '=' in i and not string.split(i, '=')[0] in allowedParams:
                        try:
                            invalidParams.append(i)
                        except Exception as err:
                            raise Exception('invalid parameter\n{0}'.format(i))
                    else:
                        if 'file=' in i:
                            file = os.path.abspath(string.strip(string.split(
                                i, '=')[1]))
                        if 'fields=' in i:
                            for field in string.split(string.split(i, '=')[1], ','):
                                if field in self.db[table].fields:
                                    fields.append(string.strip(field))

                if len(invalidParams) > 0:
                    print('the following parameter(s) is not valid\n{0}'.format(
                        string.join(invalidParams, ',')))
                else:
                    try:
                        self.cmd_table(table, file, fields)
                    except Exception as err:
                        print('could not generate table for table {0}\n{1}'
                              .format(table, err))
        except Exception as err:
            print('sorry, can not do that!\n{0}'.format(err))

    def getTable(self, tbl):
        for mTbl in db.tables:
            if tbl in mTbl:
                if mTbl.startswith(tbl):
                    return mTbl

    def execCommand(self, cmd):
        words = cmd.split(" ")
        words = [i for i in words if i]
        if not words:
            return
        cmd, parameters = words[0].lower(), words[1:]

        if not cmd in self.commands:
            raise Exception(
                "Command {0} not found. Try 'help'\r\n".format(cmd))

        self.commands[cmd](*parameters)

    '''---
             DEFAULT COMMANDS (begins with cmd_)
                                                     ---'''
    def cmd_clear(self, numlines=100):
        """-5|clear|clear the screen"""
        if os.name == "posix":
            '''---
                        Unix/Linux/MacOS/BSD/etc
                                                    ---'''
            os.system('clear')
        elif os.name in ("nt", "dos", "ce"):
            '''---
                        Windows
                                        ---'''
            os.system('CLS')
        else:
            '''---
                     Fallback for other operating systems.
                                                             ---'''
            print('\n' * numlines)

    def cmd_table(self, tbl, file=None, fields=[]):
        """-4|-table [TABLENAME] optional[file=None] [fields=None]|\
the default tableStyle is no_wrap - use the 'set x y' command to change the style\n\
style choices:
\twrap_always
\twrap_onspace
\twrap_onspace_strict
\tno_wrap (value '')\n
\t the 2nd optional param is a path to a file where the table will be written
\t the 3rd optional param is a list of fields you want displayed\n"""
        table = None
        for mTbl in db.tables:
            if tbl in mTbl:
                if mTbl.startswith(tbl):
                    table = mTbl
                    break
        oTable = tableHelper()
        '''---
                tablestyle:
                        wrap_always
                            wrap_onspace
                                wrap_onspace_strict
                    or set set to "" for no wrapping
                                                                                    ---'''
        tableStyle = self.var_tableStyle
        filedNotFound = []
        table_fields = None
        if len(fields) == 0:
            table_fields = self.db[table].fields
        else:
            table_fields = fields

        for field in fields:
            if not field in self.db[table].fields:
                filedNotFound.append(field)
        if len(filedNotFound) == 0:
            rows = self.db(self.db[table].id > 0).select()
            rows_data = []
            for row in rows:
                rowdata = []
                for f in table_fields:
                    rowdata.append('{0}'.format(row[f]))
                rows_data.append(string.join(rowdata, ','))
            data = string.join(rows_data, '\n')
            dataTable = oTable.getTable_Wrap(data, tableStyle, table_fields)
            print('TABLE {0}\n{1}'.format(table, dataTable))
            if file is not None:
                try:
                    tail, head = os.path.split(file)
                    try:
                        os.makedirs(tail)
                    except:
                        'do nothing, folders exist'
                    oFile = open(file, 'w')
                    oFile.write('TABLE: {0}\n{1}'.format(table, dataTable))
                    oFile.close()
                    print('{0} has been created and populated with all available data from table {1}\n'.format(file, table))
                except Exception as err:
                    print("EXCEPTION: could not create table {0}\n{1}".format(
                        table, err))
        else:
            print('the following fields are not valid [{0}]'.format(
                string.join(filedNotFound, ',')))

    def cmd_help(self, *args):
        '''-3|help|Show's help'''
        alldata = []
        lengths = []

        for i in self.commandSort:
            alldata.append(
                self.commands[i].__doc__.split("|")[1:])

        for i in alldata:
            if len(i) > len(lengths):
                for j in range(len(i)
                               - len(lengths)):
                    lengths.append(0)

            j = 0
            while j < len(i):
                if len(i[j]) > lengths[j]:
                    lengths[j] = len(i[j])
                j += 1

        print("-" * (lengths[0] + lengths[1] + 4))
        for i in alldata:
            print((("%-" + str(lengths[0]) + "s  - %-" + str(
                lengths[1]) + "s") % (i[0], i[1])))
            if len(i) > 2:
                for j in i[2:]: print(("%" + str(lengths[
                                       0] + 9) + "s* %s") % (" ", j))
        print()

    def cmd_vars(self, *args):
        '''-2|vars|Show variables'''
        print("variables\r\n" + "-" * 79)
        for i, j in self.configvars.items():
            value = self.parfmt(repr(getattr(self, j)), 52)
            print("| %20s | %52s |" % (i, value[0]))
            for k in value[1:]: print("| %20s | %52s |" % ("", k))
            if len(value) > 1:
                print("| %20s | %52s |" % ("", ""))
        print("-" * 79)

    def parfmt(self, txt, width):
        res = []
        pos = 0
        while True:
            a = txt[pos:pos + width]
            if not a:
                break
            res.append(a)
            pos += width
        return res

    def cmd_set(self, *args):
        '''-1|set [variable_name] [value]|Set configuration variable value|Values are an expressions (100 | string.lower('ABC') | etc.'''
        value = " ".join(args[1:])
        if args[0] not in self.configvars:
            setattr(self, "var_{0}".format(args[0]), eval(value))
        setattr(self, "var_{0}".format(args[0]), eval(value))

    def cmd_clearscreen(self, numlines=50):
        '''---Clear the console.
                                    ---'''
        if os.name == "posix":
            '''---
                        Unix/Linux/MacOS/BSD/etc
                                                    ---'''
            os.system('clear')
        elif os.name in ("nt", "dos", "ce"):
            '''---
                        Windows
                                        ---'''
            os.system('CLS')
        else:
            '''---
                     Fallback for other operating systems.
                                                             ---'''
            print('\n' * numlines)


class dalShell(console):
    def __init__(self):
        pass

    def shell(self, db):
        console.__init__(self, prompt=">>> ", banner='dal interactive shell')
        self.execCmd(db)


class setCopyDB():
    def __init__(self):
        '''---
                non source or target specific vars
                                                        ---'''
        self.strModel = None
        self.dalPath = None
        self.db = None
        '''---
                    source vars
                                    ---'''
        self.sourceModel = None
        self.sourceFolder = None
        self.sourceConnectionString = None
        self.sourcedbType = None
        self.sourcedbName = None
        '''---
                    target vars
                                    ---'''
        self.targetdbType = None
        self.targetdbName = None
        self.targetModel = None
        self.targetFolder = None
        self.targetConnectionString = None
        self.truncate = False

    def _getDal(self):
        mDal = None
        if self.dalPath is not None:
            global DAL
            sys.path.append(self.dalPath)
            mDal = __import__(
                'dal', globals={}, locals={}, fromlist=['DAL'], level=0)
            DAL = mDal.DAL
            return mDal

    def instDB(self, storageFolder, storageConnectionString, autoImport):
        self.db = DAL(storageConnectionString, folder=os.path.abspath(
            storageFolder), auto_import=autoImport)
        return self.db

    def delete_DB_tables(self, storageFolder, storageType):
        print('delete_DB_tablesn\n\t{0}\n\t{1}'.format(
            storageFolder, storageType))
        dataFiles = [storageType, "sql.log"]
        try:
            for f in os.listdir(storageFolder):
                if ".table" in f:
                    fTable = "{0}/{1}".format(storageFolder, f)
                    os.remove(fTable)
                    print('deleted {0}'.format(fTable))
            for dFile in dataFiles:
                os.remove("{0}/{1}".format(storageFolder, dFile))
                print('deleted {0}'.format(
                    "{0}/{1}".format(storageFolder, dFile)))
        except Exception as errObj:
            print(str(errObj))

    def truncatetables(self, tables=[]):
        if len(tables) != 0:
            try:
                print('table value: {0}'.format(tables))
                for tbl in self.db.tables:
                    for mTbl in tables:
                        if mTbl.startswith(tbl):
                            self.db[mTbl].truncate()
            except Exception as err:
                print('EXCEPTION: {0}'.format(err))
        else:
            try:
                for tbl in self.db.tables:
                    self.db[tbl].truncate()
            except Exception as err:
                print('EXCEPTION: {0}'.format(err))

    def copyDB(self):
        other_db = DAL("{0}://{1}".format(
            self.targetdbType, self.targetdbName), folder=self.targetFolder)

        print('creating tables...')

        for table in self.db:
            other_db.define_table(
                table._tablename, *[field for field in table])
            '''
            should there be an option to truncAte target DB?
            if yes, then change args to allow for choice
            and set self.trancate to the art value

            if self.truncate==True:
                other_db[table._tablename].truncate()
            '''

        print('exporting data...')
        self.db.export_to_csv_file(open('tmp.sql', 'wb'))

        print('importing data...')
        other_db.import_from_csv_file(open('tmp.sql', 'rb'))
        other_db.commit()
        print('done!')
        print('Attention: do not run this program again or you end up with duplicate records')

    def createfolderPath(self, folder):
        try:
            if folder is not None:
                os.makedirs(folder)
        except Exception as err:
            pass

if __name__ == '__main__':
    oCopy = setCopyDB()
    db = None
    targetDB = None
    dbfolder = None
    clean = False
    model = None
    truncate = False

    parser = argparse.ArgumentParser(description='\
samplecmd line:\n\
-f ./blueLite/db_storage -i -y sqlite://storage.sqlite -Y sqlite://storage2.sqlite -d ./blueLite/pyUtils/sql/blueSQL -t True',
                                     epilog='')
    reqGroup = parser.add_argument_group('Required arguments')
    reqGroup.add_argument('-f', '--sourceFolder', required=True, help="path to the 'source' folder of the 'source' DB")
    reqGroup.add_argument('-F', '--targetFolder', required=False, help="path to the 'target' folder of the 'target' DB")
    reqGroup.add_argument('-y', '--sourceConnectionString', required=True, help="source db connection string ()\n\
------------------------------------------------\n\
\
sqlite://storage.db\n\
mysql://username:password@localhost/test\n\
postgres://username:password@localhost/test\n\
mssql://username:password@localhost/test\n\
firebird://username:password@localhost/test\n\
oracle://username/password@test\n\
db2://username:password@test\n\
ingres://username:password@localhost/test\n\
informix://username:password@test\n\
\
------------------------------------------------")
    reqGroup.add_argument('-Y', '--targetConnectionString', required=True,
                          help="target db type (sqlite,mySql,etc.)")
    autoImpGroup = parser.add_argument_group('optional args (auto_import)')
    autoImpGroup.add_argument('-a', '--autoimport', required=False, help='set to True to bypass loading of the model')

    """

    *** removing -m/-M options for now --> i need a
            better regex to match db.define('bla')...with optional db.commit()

    modelGroup=parser.add_argument_group('optional args (create model)')
    modelGroup.add_argument('-m','--sourcemodel'\
                         ,required=False\
                         ,help='to create a model from an existing model, point to the source model')
    modelGroup.add_argument('-M','--targetmodel'\
                         ,required=False\
                         ,help='to create a model from an existing model, point to the target model')

    """

    miscGroup = parser.add_argument_group('optional args/tasks')
    miscGroup.add_argument('-i', '--interactive', required=False, action='store_true', help='run in interactive mode')
    miscGroup.add_argument(
        '-d', '--dal', required=False, help='path to dal.py')
    miscGroup.add_argument('-t', '--truncate', choices=['True', 'False'], help='delete the records but *not* the table of the SOURCE DB')
    miscGroup.add_argument('-b', '--tables', required=False, type=list, help='optional list (comma delimited) of SOURCE tables to truncate, defaults to all')
    miscGroup.add_argument('-c', '--clean', required=False, help='delete the DB,tables and the log file, WARNING: this is unrecoverable')

    args = parser.parse_args()
    db = None
    mDal = None

    try:
        oCopy.sourceFolder = args.sourceFolder
        oCopy.targetFolder = args.sourceFolder
        sourceItems = string.split(args.sourceConnectionString, '://')
        oCopy.sourcedbType = sourceItems[0]
        oCopy.sourcedbName = sourceItems[1]
        targetItems = string.split(args.targetConnectionString, '://')
        oCopy.targetdbType = targetItems[0]
        oCopy.targetdbName = targetItems[1]
    except Exception as err:
        print('EXCEPTION: {0}'.format(err))

    if args.dal:
        try:
            autoImport = True
            if args.autoimport:
                autoImport = args.autoimport
            #sif not DAL in globals:
            #if not sys.path.__contains__():
            oCopy.dalPath = args.dal
            mDal = oCopy._getDal()
            db = oCopy.instDB(args.sourceFolder, args.sourceConnectionString,
                              autoImport)
        except Exception as err:
            print('EXCEPTION: could not set DAL\n{0}'.format(err))
    if args.truncate:
        try:
            if args.truncate:
                if args.tables:
                    tables = string.split(string.strip(args.tables), ',')
                else:
                    oCopy.truncatetables([])
        except Exception as err:
            print('EXCEPTION: could not truncate tables\n{0}'.format(err))
    try:
        if args.clean:
            oCopy.delete_DB_tables(oCopy.targetFolder, oCopy.targetType)
    except Exception as err:
        print('EXCEPTION: could not clean db\n{0}'.format(err))

    """
    *** goes with -m/-M options... removed for now

    if args.sourcemodel:
        try:
            oCopy.sourceModel=args.sourcemodel
            oCopy.targetModel=args.sourcemodel
            oCopy.createModel()
        except Exception as err:
            print('EXCEPTION: could not create model\n\
source model: {0}\n\
target model: {1}\n\
{2}'.format(args.sourcemodel,args.targetmodel,err))
    """

    if args.sourceFolder:
        try:
            oCopy.sourceFolder = os.path.abspath(args.sourceFolder)
            oCopy.createfolderPath(oCopy.sourceFolder)
        except Exception as err:
            print('EXCEPTION: could not create folder path\n{0}'.format(err))
    else:
        oCopy.dbStorageFolder = os.path.abspath(os.getcwd())
    if args.targetFolder:
        try:
            oCopy.targetFolder = os.path.abspath(args.targetFolder)
            oCopy.createfolderPath(oCopy.targetFolder)
        except Exception as err:
            print('EXCEPTION: could not create folder path\n{0}'.format(err))
    if not args.interactive:
        try:
            oCopy.copyDB()
        except Exception as err:
            print('EXCEPTION: could not make a copy of the database\n{0}'.format(err))
    else:
        s = dalShell()
        s.shell(db)
