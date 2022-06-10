import os
import csv
import sys
import threading
from PyQt5.QtSql import QSqlDatabase, QSqlQuery
# from EntityRecognition import EntityRecognition
from csv_read_subwindow import CSVReadSubWindow

# Custome function using sqlite3 to import csv  

class QtDatabase(object):

    def __init__(self, database_path):
        self.database_path = database_path
        self.database_name = f"{os.path.basename(database_path)}{'.db'}"
        self.connection = QSqlDatabase.addDatabase('QSQLITE')
        self.connection.setDatabaseName(self.database_name)
        self.connection.open()
    # @staticmethod
    def create_table(self, table_name, column_names):
        if not self.connection.open():
            print("Database Error: %s" % self.connection.lastError().databaseText())

        query = QSqlQuery()

        # build query string
        column_string = ''
        comma = ', '
        column_names_len = len(column_names)
        for index, column_name in enumerate(column_names):
            if index == column_names_len - 1:
                comma = ''

            column_string += f"{column_name}{' TEXT'}{comma}"

        query_string = f"{'CREATE TABLE IF NOT EXISTS '}{table_name}" \
                       f"{' ('}{'id INTEGER PRIMARY KEY AUTOINCREMENT, '}{column_string}{')'}"

        # create table query
        query.exec(query_string)

    @staticmethod
    def insert_data(table_name, column_names, row):
        insert_query = QSqlQuery()

        # build query string
        column_string = ''
        comma = ', '
        column_names_len = len(column_names)

        # column names
        for index, column_name in enumerate(column_names):
            if index == column_names_len - 1:
                comma = ''
            column_string += f"{column_name}{comma}"
        column_string = f"{'('}{column_string}{')'}{' VALUES '}"

        # values
        comma = ', '
        values_string = ''
        for index in range(column_names_len):
            if index == column_names_len - 1:
                comma = ''
            values_string += f"{'?'}{comma}"
        values_string = f"{'('}{values_string}{')'}"
        column_string += f"{values_string}"

        # query string
        query_string = f"{'INSERT INTO '}{table_name}{column_string}"
        insert_query.prepare(query_string)

        # bind data
        for data in row:
            insert_query.addBindValue(data)

        # insert data
        insert_query.exec()
    
    def insert_csv(self, parent, table_name, csv_file):
        with open(csv_file) as f:
            csv_reader = csv.reader(f, delimiter=',')
            # getting column names
            column_names = next(csv_reader)
            self.create_table(table_name, column_names)

            progress_subwindow = CSVReadSubWindow(csv_file, table_name, column_names, self.database_path)
            progress_subwindow.show_ui()
            
            thread = threading.Thread(target=progress_subwindow.insert_csv_to_db, args=(parent, csv_file, table_name, column_names, self.database_path))
            thread.start()
            return column_names

    def insert_into_merged_timeline(self, selected_columns, merged_timeline_table):
        # create table merged-timeline
        column_name_merged_timeline = ['timestamp', 'event', 'source']
        self.create_table(merged_timeline_table, column_name_merged_timeline)

        # select for each timeline then insert to merged-timeline
        for timeline_name, column_names in selected_columns.items():
            # sort column to make sure the order: [timestamp, event]
            column_sorted = []
            for column_type, column_name in column_names.items():
                if column_type == 'timestamp':
                    if len(column_sorted) > 1:
                        column_sorted.insert(0, column_name)
                    else:
                        column_sorted.append(column_name)
                elif column_type == 'event':
                    column_sorted.append(column_name)
            # build query string
            column_string = ''
            comma = ', '
            column_names_len = len(column_sorted)
            
            # column names
            for index, column_name in enumerate(column_sorted):
                if index == column_names_len - 1:
                    comma = ''
                column_string += f"{column_name}{comma}"

            # select timeline table based on timeline_name
            select_query = QSqlQuery()

            # query string
            query_string = f"{'SELECT '}{column_string}{' FROM '}{timeline_name}"
            select_query.exec(query_string)

            # get data and insert
            while select_query.next():
                # row = [timestamp, event, source]
                row = [select_query.value(column_sorted[0]), select_query.value(column_sorted[1]), timeline_name]
                self.insert_data(merged_timeline_table, column_name_merged_timeline, row)