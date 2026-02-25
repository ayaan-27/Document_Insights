import os
import sys
import time

import psycopg2
import psycopg2.extras as extras
import textract_extraction as textract_extraction


#import scripts.textract_extraction as textract_extraction
#upload_folder = r'C:\Users\priyaranjan.kumar\Downloads'


upload_folder = 'uploads'


def connect_db():

    DB_HOST = "3.139.198.182"
    DB_NAME = "DeepInsights"
    DB_USER = "postgres"
    DB_PASS = "DI123"

    conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER,
                            password=DB_PASS, host=DB_HOST)
    return conn


def get_files_to_process(conn):

    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    s = "SELECT * FROM document_information where ocr_done = false"
    cur.execute(s)  # Execute the SQL
    list_users = cur.fetchall()
    files_to_process_list = []
    content = {}

    for result in list_users:
        content = {'id': result['id'], 'filename': result['filename']}
        files_to_process_list.append(content)

    return files_to_process_list


def call_extraction(id_, filename, filepath):

    image_list = textract_extraction.input_(filepath)
    print(id_, image_list, filename)
    form_df, line_df = textract_extraction.call_textract_(
        id_, image_list, filename)
    processed_form_df, processed_line_df = textract_extraction.df_processing(
        form_df, line_df)

    return processed_form_df, processed_line_df


def update_db_after_process(conn, id_list):

    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    for each_id in id_list:
        ocr_done = True
        cur.execute(
            "UPDATE document_information SET ocr_done = %s WHERE  id= %s", (ocr_done, each_id))
        conn.commit()


def execute_values(conn, df, table):

    tuples = [tuple(x) for x in df.to_numpy()]
    cols = ','.join(list(df.columns))
    # SQL query to execute
    query = "INSERT INTO %s(%s) VALUES %%s" % (table, cols)
    cursor = conn.cursor()
    try:
        extras.execute_values(cursor, query, tuples)
        conn.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        print("Error: %s" % error)
        conn.rollback()
        cursor.close()
        return 1
    print("the dataframe is inserted")
    cursor.close()


def close_db(conn):
    try:
        if conn is not None:
            conn.close()
            #LOGGER.info('Database connection closed')
    except Exception as error:
        # LOGGER.exception(error)
        raise error


def main():
    """."""
    while True:
        try:
            conn = connect_db()
            files_to_process_list = get_files_to_process(conn)

            if len(files_to_process_list) == 0:
                print("no files to process going to sleep")
                time.sleep(10)

            else:
                id_list = []
                for each_filename in files_to_process_list:
                    id_ = str(each_filename['id'])
                    filename = each_filename['filename']
                    print('\nWorking on ', id_, filename, '\n\n')

                    # call textract
                    try:
                        filepath = os.path.join(upload_folder, filename)
                        form_df, line_df = call_extraction(id_, filename, filepath)

                        execute_values(conn, line_df, 'line_level_data')
                        execute_values(conn, form_df, 'extracted_document_data')
                        id_list.append(id_)
                    except Exception as ex:
                        print('Extraction Error for file', id_, filename, '\n\n', ex, '\n\n\n\n')

                update_db_after_process(conn, id_list)
                time.sleep(10)
        except Exception as e:
            print(e)
        finally:
            close_db(conn)


if __name__ == "__main__":
    main()
