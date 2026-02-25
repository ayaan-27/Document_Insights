from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import psycopg2
import psycopg2.extras as extras
from flask_cors import CORS, cross_origin
from flask_session import Session
from flask import json
from flask import Response
import json
import decimal
import os
from werkzeug.utils import secure_filename
from datetime import datetime
import logging
import pandas as pd
LOGGER = logging.getLogger("logger")

app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = "uploads"
app.secret_key = "ayaan_k27"
CORS(app)

DB_HOST = "3.139.198.182"
DB_NAME = "DeepInsights"
DB_USER = "postgres"
DB_PASS = "DI123"

conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER,
                        password=DB_PASS, host=DB_HOST)

#login and Auth


# List Of APIs
# get a document based on document ID
@app.route('/documents', methods=["GET","POST"])
def doc_id():
    if request.method == 'POST':
        try:
            req_json= request.json
            doc_id = req_json['doc_id']
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            s = "SELECT * FROM document_information where id='{}'".format(doc_id)
            cur.execute(s)  # Execute the SQL
            list_users = cur.fetchall()
            response = []
            content = {}
            for result in list_users:
                content = {'id': result['id'], 'name': result['name'], 'task': result['task'], 'docType': result['doc_type'], 'timeData': {'lastModified': result['last_modified'], 'startDate': result['start_date'], 'endDate': result['end_date']}, 'userdata': {
                'processor': result['processor'], 'qc': result['qc'], 'manager': result['manager']}, 'flags': {'processed': result['processed'], 'verified': result['verified'], 'seen': result['seen']}}
                response.append(content)
                content = {}
            return jsonify(response[0])
        except Exception as error:
             LOGGER.exception(error)
             raise error


# single endpoint to get documents for all the roles

# @app.route('/get_docs', methods=["GET","POST"])
# def get_docs():
#     if request.method == 'POST':
#         try:
#             req_json= request.json
#             role = req_json['role']
#             username = req_json['username']
#             cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
#             list_docs= list()
#             if role== 'Document Processor':
#                 s = "SELECT * FROM document_information where processor='{}'".format(username)
#                 cur.execute(s)  # Execute the SQL
#                 list_docs = cur.fetchall()
#             if role== 'QC':
#                 s = "SELECT * FROM document_information where qc='{}'".format(username)
#                 cur.execute(s)  # Execute the SQL
#                 list_docs = cur.fetchall()
#             if role== 'Manager':
#                 s = "SELECT * FROM document_information where manager='{}'".format(username)
#                 cur.execute(s)  # Execute the SQL
#                 list_docs = cur.fetchall()
#             response = []
#             content = {}
#             for result in list_docs:
#                 content = {'id': result['id'], 'name': result['name'], 'task': result['task'], 'docType': result['doc_type'], 'timeData': {'lastModified': result['last_modified'], 'startDate': result['start_date'], 'endDate': result['end_date']}, 'userdata': {
#                 'processor': result['processor'], 'qc': result['qc'], 'manager': result['manager']}, 'flags': {'processed': result['processed'], 'verified': result['verified'], 'seen': result['seen']}}
#                 response.append(content)
#                 content = {}
#             return jsonify(response) # data= response, start date, end date
#         except Exception as error:
#             LOGGER.exception(error)
#             raise error

@app.route('/get_docs', methods=["GET","POST"])
def get_docs():
    if request.method == 'POST':
        try:
            req_json= request.json
            role = req_json['role']
            username = req_json['username']
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            list_docs= list()
            if role== 'Document Processor':
                s = "SELECT * FROM document_information where processor='{}'".format(username)
                df = pd.read_sql(s, conn)
                df['Status']=''
                for i in range(len(df)):
                    if (df['processed'][i]== False):
                        df['Status'][i]= 'Pending'
                    if (df['processed'][i]== True):
                        df['Status'][i]= 'Done'    
            if role== 'QC':
                s = "SELECT * FROM document_information where qc='{}'".format(username)
                df = pd.read_sql(s, conn)
                df['Status']=''
                for i in range(len(df)):
                    if (df['verified'][i]== False):
                        df['Status'][i]= 'Pending'
                    if (df['verified'][i]== True):
                        df['Status'][i]= 'Done' 
            if role== 'Manager':
                s = "SELECT * FROM document_information where manager='{}'".format(username)
                df = pd.read_sql(s, conn)
                df['Status']=''
                for i in range(len(df)):
                    if (df['processor'][i]== 'none'):
                        df['Status'][i]= 'Unassigned'
                    if (df['processed'][i]== True and df['qc'][i]== 'none'):
                        df['Status'][i]= 'Processed'
                    if (df['processor'][i]!= 'none' and df['processed'][i]== False):
                        df['Status'][i]= 'In Processing'
                    if (df['qc'][i]!= 'none' and df['verified'][i]== False):
                        df['Status'][i]= 'In QC'
                    if (df['processed'][i]== True and df['verified'][i]== True ):
                        df['Status'][i]= 'Done'
            df = df[['id','name','task','doc_type','Status','last_modified','start_date','end_date','processor','qc','manager','processed','verified','seen','filename']]
            df["last_modified"] = df["last_modified"].astype(str)
            df["last_modified"] = df["last_modified"].replace("NaT","")
            df.rename(columns={'doc_type':'docType','start_date':'startDate','end_date':'endDate','last_modified':'lastModified'},inplace=True)
            df_data = df.to_dict(orient='records')
            resp = jsonify({"val": df_data})
            return resp
        except Exception as error:
            LOGGER.exception(error)
            raise error


# get role from the users table and using if condition combine the three queries for processor,qc and manager, make a data frame
# @app.route('/doc_processor', methods=["GET","POST"])
# def doc_processor():
#     if request.method == 'POST':
#         try:
#             req_json= request.json
#             processor = req_json['processor']
#             cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
#             s = "SELECT * FROM document_information where processor='{}'".format(
#             processor)
#             cur.execute(s)  # Execute the SQL
#             list_users = cur.fetchall()
#             response = []
#             content = {}
#             for result in list_users:
#                 content = {'id': result['id'], 'name': result['name'], 'task': result['task'], 'docType': result['doc_type'], 'timeData': {'lastModified': result['last_modified'], 'startDate': result['start_date'], 'endDate': result['end_date']}, 'userdata': {
#                 'processor': result['processor'], 'qc': result['qc'], 'manager': result['manager']}, 'flags': {'processed': result['processed'], 'verified': result['verified'], 'seen': result['seen']}}
#                 response.append(content)
#                 content = {}
#             conn.commit()
#             return jsonify(response) # data= response, start date, end date
#         except Exception as error:
#             LOGGER.exception(error)
#             raise error


# # getting documents for the qc
# @app.route('/doc_qc', methods=["GET","POST"])
# def doc_qc():
#     if request.method == 'POST':
#         try:
#             req_json= request.json
#             qc = req_json['qc']
#             cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
#             s = "SELECT * FROM document_information where qc='{}'".format(qc)
#             cur.execute(s)  # Execute the SQL
#             list_users = cur.fetchall()
#             response = []
#             content = {}
#             for result in list_users:
#                 content = {'id': result['id'], 'name': result['name'], 'task': result['task'], 'docType': result['doc_type'], 'timeData': {'lastModified': result['last_modified'], 'startDate': result['start_date'], 'endDate': result['end_date']}, 'userdata': {
#                 'processor': result['processor'], 'qc': result['qc'], 'manager': result['manager']}, 'flags': {'processed': result['processed'], 'verified': result['verified'], 'seen': result['seen']}}
#                 response.append(content)
#                 content = {}
#             return jsonify(response)
#         except Exception as error:
#             LOGGER.exception(error)
#             raise error



# # getting documents for the manager
# @app.route('/doc_manager', methods=["GET","POST"])
# def doc_manager():
#     if request.method == 'POST':
#         try:
#             req_json= request.json
#             manager = req_json['manager']
#             cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
#             s = "SELECT * FROM document_information where manager='{}' ORDER BY start_date DESC".format(manager)
#             cur.execute(s)  # Execute the SQL
#             list_users = cur.fetchall()
#             response = []
#             content = {}
#             for result in list_users:
#                 content = {'id': result['id'], 'name': result['name'], 'task': result['task'], 'docType': result['doc_type'], 'timeData': {'lastModified': result['last_modified'], 'startDate': result['start_date'], 'endDate': result['end_date']}, 'userdata': {
#                     'processor': result['processor'], 'qc': result['qc'], 'manager': result['manager']}, 'flags': {'processed': result['processed'], 'verified': result['verified'], 'seen': result['seen']}}
#                 response.append(content)
#                 content = {}
#             return jsonify(response)
#         except Exception as error:
#             LOGGER.exception(error)
#             raise error

# update document last modified time


@app.route('/updatetime', methods=["POST", "GET"])
def update_time():
    if request.method == 'POST':
        try:
            req_json= request.json
            id= req_json['id']
            last_modified = datetime.now()
            #last_modified = last_modified.strftime("%d/%m/%Y %H:%M:%S")
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute(
                "UPDATE document_information SET last_modified = %s WHERE id= %s", (last_modified, id))
            conn.commit()
            LOGGER.info('Last modified time updated in db')
            return ('', 204)
        except Exception as error:
            LOGGER.exception(error)
            raise error

# first access time by processor


@app.route('/access_time', methods=["POST", "GET"])
def access_time():
    if request.method == 'POST':
        try:
            req_json= request.json
            id= req_json['id']
            access_time = datetime.now()
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute(
                "UPDATE document_information SET access_time_proc = %s WHERE id= %s and access_time_proc IS NULL", (access_time, id))
            conn.commit()
            LOGGER.info('First access time for processor captured in db')
            return ('', 204)
        except Exception as error:
            LOGGER.exception(error)
            raise error

# submit time for processor


@app.route('/submit_time', methods=["POST", "GET"])
def submit_time():
    if request.method == 'POST':
        try:
            req_json= request.json
            id= req_json['id']
            submit_time = datetime.now()
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute(
                "UPDATE document_information SET submit_time_proc = %s WHERE id= %s", (submit_time, id))
            conn.commit()
            LOGGER.info('Processor submit time captured in db')
            return ('', 204)
        except Exception as error:
            LOGGER.exception(error)
            raise error


# first access time for QC


@app.route('/access_time_qc', methods=["POST", "GET"])
def access_time_qc():
    if request.method == 'POST':
        try:
            req_json= request.json
            id= req_json['id']
            access_time = datetime.now()
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute(
                "UPDATE document_information SET access_time_qc = %s WHERE id= %s and access_time_qc IS NULL", (access_time, id))
            conn.commit()
            LOGGER.info('First access time for QC captured in db')
            return ('', 204)
        except Exception as error:
            LOGGER.exception(error)
            raise error


# submit time for QC


@app.route('/submit_time_qc', methods=["POST", "GET"])
def submit_time_qc():
    if request.method == 'POST':
        try:
            req_json= request.json
            id= req_json['id']
            submit_time = datetime.now()
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute(
                "UPDATE document_information SET submit_time_qc = %s WHERE id= %s", (submit_time, id))
            conn.commit()
            LOGGER.info('QC submit time captured in db')
            return ('', 204)
        except Exception as error:
            LOGGER.exception(error)
            raise error

# turning processed= true in database


@app.route('/updateprocessed', methods=["POST", "GET"])
def update_processed():
    if request.method == 'POST':
        try:
            req_json= request.json
            id= req_json['id']
            processed = True
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute(
                "UPDATE document_information SET processed = %s WHERE  id= %s", (processed, id))
            conn.commit()
            LOGGER.info('Processed updated to true in database')
            return ('', 204) 
        except Exception as error:
            LOGGER.exception(error)
            raise error  


# turning verified= true in database


@app.route('/updateverified', methods=["POST", "GET"])
def update_verified():
    if request.method == 'POST':
        try:
            req_json= request.json
            id= req_json['id']
            verified = True
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute(
                "UPDATE document_information SET verified = %s WHERE  id= %s", (verified, id))
            conn.commit()
            LOGGER.info('Verified updated to true in database')
            return ('', 204)
        except Exception as error:
            LOGGER.exception(error)
            raise error  

# for the button send back to processor


@app.route('/returntoprocessor', methods=["POST", "GET"])
def returntoprocessor():
    if request.method == 'POST':
        try:
            req_json= request.json
            id= req_json['id']
            processed = False
            verified = False
            qc = 'none'
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute("UPDATE document_information SET processed = %s, verified= %s, qc= %s WHERE  id= %s",
                        (processed, verified, qc, id))
            conn.commit()
            LOGGER.info('Document returned to processor by QC')
            return ('', 204)
        except Exception as error:
            LOGGER.exception(error)
            raise error 

# Remove a document

@app.route('/remove_document', methods=["POST", "GET"])
def remove_document():
    if request.method == 'POST':
        try:
            req_json= request.json
            id= req_json['id']
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            s= "DELETE FROM document_information where id='{}'".format(id)
            cur.execute(s)
            conn.commit()
            LOGGER.info('Document Removed from the table')
            return ('', 204)
        except Exception as error:
            LOGGER.exception(error)
            raise error 

# getting data for 'Your Team' table
@app.route('/get_team_data', methods=["POST", "GET"])
def get_team_data():
    if request.method == 'POST':
        try:
            req_json= request.json
            manager= req_json['manager']
            start_date= req_json['startdate']
            end_date= req_json['enddate']
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            s= "SELECT username,role from users where reports_to= '{}'".format(manager)
            cur.execute(s)
            list_users= cur.fetchall()
            df= pd.DataFrame(list_users, columns= ['Name','Role'])
            df['Pending']= ''
            df['Completed']= ''
            df['Accuracy']= ''
            df['AHT']= ''
            for i in range(len(df)):
                if df['Role'][i]=='Document Processor':
                    cur.execute("SELECT COUNT(*) from document_information where processor= %s AND processed= %s  AND start_date>= %s AND end_date<= %s",(df['Name'][i],False,start_date,end_date))
                    pending_docs = cur.fetchall()[0]
                    df['Pending'][i]= pending_docs[0]
                if df['Role'][i]=='QC':
                    cur.execute("SELECT COUNT(*) from document_information where qc= %s AND verified= %s AND start_date>= %s AND end_date<= %s",(df['Name'][i],False,start_date,end_date))
                    pending_docs = cur.fetchall()[0]
                    df['Pending'][i]= pending_docs[0]
            for i in range(len(df)):
                if df['Role'][i]=='Document Processor':
                    cur.execute("SELECT COUNT(*) from document_information where processor= %s AND processed= %s AND start_date>= %s AND end_date<= %s",(df['Name'][i],True,start_date,end_date))
                    complete_docs = cur.fetchall()[0]
                    df['Completed'][i]= complete_docs[0]
                if df['Role'][i]=='QC':
                    cur.execute("SELECT COUNT(*) from document_information where qc= %s AND verified= %s AND start_date>= %s AND end_date<= %s",(df['Name'][i],True,start_date,end_date))
                    complete_docs = cur.fetchall()[0]
                    df['Completed'][i]= complete_docs[0]
            for i in range(len(df)):
                if df['Role'][i]=='Document Processor':
                    cur.execute("WITH T1 AS (SELECT count(*) as no_fields from extracted_document_data e JOIN document_information d ON e.id=d.id where d.processor= %s AND d.start_date>= %s AND d.end_date<= %s),T2 AS (SELECT count(*) as incorrect_fields from extracted_document_data e JOIN document_information d ON e.id=d.id where e.wrong= True and d.processor= %s AND d.start_date>= %s AND d.end_date<= %s) SELECT ROUND (((CAST(T1.no_fields as numeric) - CAST(T2.incorrect_fields as numeric)) / NULLIF(CAST(T1.no_fields as numeric),0) * 100), 2) as mean_accuracy FROM T1, T2",(df['Name'][i],start_date,end_date,df['Name'][i],start_date,end_date))
                    accuracy = cur.fetchall()[0]
                    if accuracy[0]!= None:
                        df['Accuracy'][i]= str(accuracy[0]) + '%'
            for i in range(len(df)):
                if df['Role'][i]=='Document Processor':
                    cur.execute("WITH T1 AS (SELECT SUM(ROUND(Extract(epoch FROM (submit_time_proc - access_time_proc))/60)) AS minutes from document_information where processor= %s AND start_date>= %s AND end_date<= %s), T2 AS (SELECT count(*) as no_docs from document_information where processor= %s AND start_date>= %s AND end_date<= %s) SELECT ROUND((CAST(T1.minutes as numeric) / NULLIF(CAST(T2.no_docs as numeric),0)), 2) as avg_processing_time FROM T1, T2", (df['Name'][i],start_date,end_date,df['Name'][i],start_date,end_date))
                    aht_processor = cur.fetchall()[0]
                    if aht_processor[0]!= None:
                        df['AHT'][i]= str(aht_processor[0]) + ' min '
                if df['Role'][i]=='QC':
                    cur.execute("WITH T1 AS (SELECT SUM(ROUND(Extract(epoch FROM (submit_time_qc - access_time_qc))/60)) AS minutes from document_information where qc= %s AND start_date>= %s AND end_date<= %s), T2 AS (SELECT count(*) as no_docs from document_information where qc= %s AND start_date>= %s AND end_date<= %s) SELECT ROUND((CAST(T1.minutes as numeric) / NULLIF(CAST(T2.no_docs as numeric),0)), 2) as avg_processing_time FROM T1, T2", (df['Name'][i],start_date,end_date,df['Name'][i],start_date,end_date))
                    aht_qc = cur.fetchall()[0]
                    if aht_qc[0]!= None:
                        df['AHT'][i]= str(aht_qc[0]) + ' min '
            
            df_cols = ['Name', 'Role', 'Pending', 'Completed', 'Accuracy', 'AHT']
            df_data = df.to_dict(orient='records')
            resp = jsonify({"val": df_data, "columns": df_cols})
            return resp
        except Exception as error:
            LOGGER.exception(error)
            raise error 

# endpoint to update qc table

@app.route('/update_qctable', methods=["POST", "GET"])
def update_qctable():
    if request.method == 'POST':
        try:
            req_json= request.json
            id= req_json['id']
            key= req_json['key']
            final_value= req_json['final_value']
            comment= req_json['comment']
            modified = datetime.now()
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute("INSERT INTO qc_table(id,edit_time,key,final_value,comment) VALUES(%s,%s,%s,%s,%s)",
                        (id, modified, key, final_value, comment))
            conn.commit()
            LOGGER.info('Changes by QC captured in QC table')
            return ('', 204)
        except Exception as error:
            LOGGER.exception(error)
            raise error

# add new document for manager
@app.route('/add_newdoc', methods=["POST", "GET"])
def add_newdoc():
    if request.method == 'POST':
        try:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            req_data = request.form.getlist('data')
            data_dict = json.loads(req_data[0])
            id = data_dict['id']
            name = data_dict['name']
            task = data_dict['task']
            doc_type = data_dict['docType']
            start_date = data_dict['startDate']
            end_date = data_dict['endDate']
            last_modified = data_dict['lastModified']
            processor = data_dict['processor']
            qc = data_dict['qc']
            manager = data_dict['manager']
            flag_processed = data_dict['processed']
            flag_verified = data_dict['verified']
            flag_seen = data_dict['seen']
            ocr_done = False

            file = request.files.getlist("file")[0]
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            cur.execute("INSERT INTO document_information(id,name,task,doc_type,start_date,end_date,processor,qc,manager,processed,verified,seen,last_modified,filename, ocr_done) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                        (id, name, task, doc_type, start_date, end_date, processor, qc, manager, flag_processed, flag_verified, flag_seen, last_modified, filename, ocr_done))
            conn.commit()
            LOGGER.info('Document is added and uploaded in database')
            return ('', 204)
        except Exception as error:
            LOGGER.exception(error)
            raise error

# fetch the uploaded file
@app.route('/fetch_document', methods=["GET","POST"])
def fetch_document():
    if request.method == 'POST':
        try:
            req_json= request.json
            id= req_json['id']
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            s = "SELECT filename from document_information where id= '{}'".format(id)
            cur.execute(s)
            file_name = cur.fetchall()[0]
            LOGGER.info('Document is fetched for display in UI')
            return f"https://deepinsights-data-2022.s3.us-east-2.amazonaws.com/DI-uploads/prod-files/{id}/{file_name[0]}"
        except Exception as error:
            LOGGER.exception(error)
            raise error

# assigning the processed document to the QA
@app.route('/assignqc', methods=["POST", "GET"])
def assign_qc():
    if request.method == 'POST':
        try:
            req_json= request.json
            id= req_json['id']
            qc= req_json['qc']
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute(
                "UPDATE document_information SET qc = %s WHERE  id= %s", (qc, id))
            conn.commit()
            LOGGER.info('Document is assigned to QC')
            return ('', 204)
        except Exception as error:
            LOGGER.exception(error)
            raise error


# assigning the unassigned document to the processor
@app.route('/assignprocessor', methods=["POST", "GET"])
def assign_processor():
    if request.method == 'POST':
        try:
            req_json= request.json
            id= req_json['id']
            processor = req_json['processor']
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute(
                "UPDATE document_information SET processor = %s WHERE  id= %s", (processor, id))
            conn.commit()
            LOGGER.info('Document is assigned to processor')
            return ('', 204)
        except Exception as error:
            LOGGER.exception(error)
            raise error

# fetch user info


@app.route('/users', methods=["GET"])
def user():
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        s = "SELECT * FROM users"
        cur.execute(s)  # Execute the SQL
        list_users = cur.fetchall()
        response = []
        content = {}
        for result in list_users:
            content = {'username': result['username'], 'name': result['name'],
                        'password': result['password'], 'role': result['role'], 'reportsTo': result['reports_to']}
            response.append(content)
            content = {}
        return jsonify(response)
    except Exception as error:
        LOGGER.exception(error)
        raise error

# fetch username


@app.route('/fetch_user', methods=["GET","POST"])
def username_():
    if request.method == 'POST':
        try:
            req_json= request.json
            username = req_json['username']
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            s = "SELECT * FROM users where username= '{}'".format(username)
            cur.execute(s)  # Execute the SQL
            list_users = cur.fetchall()
            response = []
            content = {}
            for result in list_users:
                content = {'username': result['username'], 'name': result['name'],
                        'password': result['password'], 'role': result['role'], 'reportsTo': result['reports_to']}
                response.append(content)
                content = {}
            return jsonify(response)
        except Exception as error:
            LOGGER.exception(error)
            raise error

# getting team data


@app.route('/reports_to', methods=["GET","POST"])
def reports_():
    if request.method == 'POST':
        try:
            req_json= request.json
            reports_to = req_json['reports_to']
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            s = "SELECT * FROM users where reports_to= '{}'".format(reports_to)
            cur.execute(s)  # Execute the SQL
            list_users = cur.fetchall()
            response = []
            content = {}
            for result in list_users:
                content = {'username': result['username'], 'name': result['name'],
                        'password': result['password'], 'role': result['role'], 'reportsTo': result['reports_to']}
                response.append(content)
                content = {}
            return jsonify(response)
        except Exception as error:
            LOGGER.exception(error)
            raise error

# current session


@app.route('/currentsession', methods=["GET"])
def session():
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("SELECT * FROM current_session")  # Execute the SQL
        list_users = cur.fetchall()
        response = []
        content = {}
        for result in list_users:
            content = {'id': result['id'], 'username': result['username']}
            response.append(content)
            content = {}
        return jsonify(response)
    except Exception as error:
        LOGGER.exception(error)
        raise error

# fetch extracted document data


@app.route('/extracted_data', methods=["GET","POST"])
def extracted_data():
    if request.method == 'POST':
        try:
            req_json= request.json
            id = req_json['id']
            response = []
            cur2 = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            s2 = "SELECT key,value,confidence,page,wrong FROM extracted_document_data where id= '{}'".format(
                id)
            cur2.execute(s2)
            s3 = "SELECT key,edit_time,initial_value,final_value FROM audit_trail where id= '{}'".format(
                id)
            cur3 = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur3.execute(s3)
            list_values2 = cur2.fetchall()
            list_values3 = cur3.fetchall()
            content = {'id': id, 'auditTrail': [], 'data': []}
            for result in list_values3:
                content['auditTrail'].append({'key': result['key'], 'editTime': result['edit_time'],
                                            'initialValue': result['initial_value'], 'finalValue': result['final_value']})
            for result in list_values2:
                content['data'].append({'confidence': result['confidence'], 'value': result['value'],
                                        'key': result['key'], 'info': {'wrong': result['wrong'], 'page': result['page']}})
            response.append(content)
            return jsonify(response)
        except Exception as error:
            LOGGER.exception(error)
            raise error

# update the extracted data from the document


@app.route('/update', methods=['POST', 'GET'])
def update_data():
    if request.method == 'POST':
        try:
            req_json= request.json
            id= req_json['id']
            key= req_json['key']
            value= req_json['value']
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute(
                "UPDATE extracted_document_data SET value = %s WHERE key = %s and id= %s", (value, key, id))
            conn.commit()
            LOGGER.info('Changes to extracted data updated in the database')
            return ('', 204)
        except Exception as error:
            LOGGER.exception(error)
            raise error

# updating the wrong field in the database

@app.route('/incorrect_fields', methods=['POST', 'GET'])
def field_incorrect():
    if request.method == 'POST':
        try:
            req_json= request.json
            id= req_json['id']
            key= req_json['key']
            wrong = True
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute(
                "UPDATE extracted_document_data SET wrong = %s WHERE id= %s and key= %s", (wrong, id, key))
            conn.commit()
            LOGGER.info('Update the wrong field in database')
            return ('', 204)
        except Exception as error:
            LOGGER.exception(error)
            raise error


# Metrices

# to display float output to the UI
class Encoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            return float(obj)

# getting average documents per employee


@app.route('/doc_emp', methods=['GET'])
def doc_emp():
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        s = "WITH T1 AS (SELECT count(id) as RA from document_information), T2 AS (SELECT count(DISTINCT username) as RB from users where role='Document Processor') SELECT ROUND(CAST(T1.RA AS numeric) / NULLIF(CAST(T2.RB AS numeric),0)) as doc_emp FROM T1, T2"
        cur.execute(s)
        a = cur.fetchall()
        return json.dumps(a, cls=Encoder)
    except Exception as error:
        LOGGER.exception(error)
        raise error

# mean accuracy

@app.route('/mean_acc', methods=['GET'])
def mean_acc():
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        s = "WITH T1 AS (SELECT count(*) as no_fields from extracted_document_data),T2 AS (SELECT count(*) as incorrect_fields from extracted_document_data where wrong= True) SELECT ROUND (((CAST(T1.no_fields AS numeric) - CAST(T2.incorrect_fields AS numeric)) / NULLIF(CAST(T1.no_fields AS numeric),0) * 100)) as mean_accuracy FROM T1, T2"
        cur.execute(s)
        a = cur.fetchall()
        return json.dumps(a, cls=Encoder)
    except Exception as error:
        LOGGER.exception(error)
        raise error

# Accuracy for processor

@app.route('/mean_acc_proc', methods=['GET','POST'])
def mean_acc_proc():
    if request.method == 'POST':
        try:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            req_json= request.json
            processor= req_json['processor']
            start_date= req_json['startdate']
            end_date= req_json['enddate']
            cur.execute("WITH T1 AS (SELECT count(*) as no_fields from extracted_document_data e JOIN document_information d ON e.id=d.id where d.processor= %s AND d.start_date>= %s AND d.end_date<= %s),T2 AS (SELECT count(*) as incorrect_fields from extracted_document_data e JOIN document_information d ON e.id=d.id where e.wrong= True and d.processor= %s AND d.start_date>= %s AND d.end_date<= %s) SELECT ROUND (((CAST(T1.no_fields as numeric) - CAST(T2.incorrect_fields as numeric)) / NULLIF(CAST(T1.no_fields as numeric),0) * 100), 2) as mean_accuracy FROM T1, T2", (processor,start_date,end_date, processor,start_date,end_date))
            a = cur.fetchall()
            return json.dumps(a, cls=Encoder)
        except Exception as error:
            LOGGER.exception(error)
            raise error

# documents per day

@app.route('/doc_day', methods=['GET'])
def doc_day():
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        s = "WITH T1 AS (SELECT count(id) as no_doc from document_information), T2 AS (SELECT max(start_date)-min(start_date) as days from document_information) SELECT ROUND(CAST(T1.no_doc AS numeric) / NULLIF(CAST(T2.days AS numeric),0)) as doc_emp FROM T1, T2"
        cur.execute(s)
        a = cur.fetchall()
        return json.dumps(a, cls=Encoder)
    except Exception as error:
        LOGGER.exception(error)
        raise error

# average processing time


@app.route('/avg_proc_time', methods=['GET'])
def avg_proc_time():
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        s = "WITH T1 AS (SELECT SUM(ROUND(Extract(epoch FROM (submit_time_proc - access_time_proc))/60)) AS minutes from document_information), T2 AS (SELECT count(*) as no_docs from document_information) SELECT ROUND((CAST(T1.minutes as numeric) / NULLIF(CAST(T2.no_docs as numeric),0)), 2) as avg_processing_time FROM T1, T2"
        cur.execute(s)
        a = cur.fetchall()
        return json.dumps(a, cls=Encoder)
    except Exception as error:
        LOGGER.exception(error)
        raise error

# AHT for processor

@app.route('/aht_processor', methods=['POST', 'GET'])
def aht_processor():
    if request.method == 'POST':
        try:
            req_json= request.json
            processor= req_json['processor']
            start_date= req_json['startdate']
            end_date= req_json['enddate']
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute("WITH T1 AS (SELECT SUM(ROUND(Extract(epoch FROM (submit_time_proc - access_time_proc))/60)) AS minutes from document_information where processor= %s AND start_date>= %s AND end_date<= %s), T2 AS (SELECT count(*) as no_docs from document_information where processor= %s AND start_date>= %s AND end_date<= %s) SELECT ROUND((CAST(T1.minutes as numeric) / NULLIF(CAST(T2.no_docs as numeric),0)), 2) as avg_processing_time FROM T1, T2", (processor,start_date,end_date,processor,start_date,end_date))
            a = cur.fetchall()
            return json.dumps(a, cls=Encoder)
        except Exception as error:
            LOGGER.exception(error)
            raise error

# AHT for qc


@app.route('/aht_qc', methods=['POST', 'GET'])
def aht_qc():
    if request.method == 'POST':
        try:
            req_json= request.json
            qc= req_json['qc']
            start_date= req_json['startdate']
            end_date= req_json['enddate']
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute("WITH T1 AS (SELECT SUM(ROUND(Extract(epoch FROM (submit_time_qc - access_time_qc))/60)) AS minutes from document_information where qc= %s AND start_date>= %s AND end_date<= %s), T2 AS (SELECT count(*) as no_docs from document_information where qc= %s AND start_date>= %s AND end_date<= %s) SELECT ROUND((CAST(T1.minutes as numeric) / NULLIF(CAST(T2.no_docs as numeric),0)), 2) as avg_processing_time FROM T1, T2", (qc,start_date,end_date,qc,start_date,end_date))
            a = cur.fetchall()
            return json.dumps(a, cls=Encoder)
        except Exception as error:
            LOGGER.exception(error)
            raise error

# corrections identified by QA

@app.route('/corrections', methods=['GET','POST'])
def corrections():
    if request.method=='POST':
        try:
            req_json= request.json
            start_date= req_json['startdate']
            end_date= req_json['enddate']
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute("SELECT count(*) from qc_table q JOIN document_information d ON q.id=d.id WHERE d.start_date>= %s AND d.end_date<= %s",(start_date,end_date))
            a = cur.fetchall()
            return jsonify(a)
        except Exception as error:
            LOGGER.exception(error)
            raise error

# DEEP INSIGHTS PERFORMANCE SUMMARY

# documents processed

@app.route('/doc_processed', methods=['GET'])
def doc_processed():
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        s = "SELECT Count(*) from document_information where processed= True"
        cur.execute(s)
        a = cur.fetchall()
        return jsonify(a)
    except Exception as error:
        LOGGER.exception(error)
        raise error

# fields identified

@app.route('/fields_identified', methods=['GET'])
def fields_identified():
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        s = "SELECT Count(*) from extracted_document_data"
        cur.execute(s)
        a = cur.fetchall()
        return jsonify(a)
    except Exception as error:
        LOGGER.exception(error)
        raise error
# high confidence extractions


@app.route('/high_conf_extraction', methods=['GET'])
def high_conf_extraction():
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        s = "SELECT Count(*) from extracted_document_data where confidence> 90"
        cur.execute(s)
        a = cur.fetchall()
        return jsonify(a)
    except Exception as error:
        LOGGER.exception(error)
        raise error
# low confidence extractions


@app.route('/low_conf_extraction', methods=['GET'])
def low_conf_extraction():
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        s = "SELECT Count(*) from extracted_document_data where confidence< 90"
        cur.execute(s)
        a = cur.fetchall()
        return jsonify(a)
    except Exception as error:
        LOGGER.exception(error)
        raise error

# uncaptured values
@app.route('/uncaptured_val', methods=['GET'])
def uncaptured_val():
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        s = "SELECT Count(*) from extracted_document_data where value=''"
        cur.execute(s)
        a = cur.fetchall()
        return jsonify(a)
    except Exception as error:
        LOGGER.exception(error)
        raise error

# no of validated documents

@app.route('/documents_validated', methods=['GET'])
def documents_validated():
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        s = "SELECT Count(*) from document_information where verified= True"
        cur.execute(s)
        a = cur.fetchall()
        return jsonify(a)
    except Exception as error:
        LOGGER.exception(error)
        raise error

# edited fields

@app.route('/edited_fields', methods=['GET'])
def edited_fields():
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        s = "SELECT Count(*) from audit_trail"
        cur.execute(s)
        a = cur.fetchall()
        return jsonify(a)
    except Exception as error:
        LOGGER.exception(error)
        raise error

# high confidence modifications


@app.route('/high_conf_mod', methods=['GET'])
def high_conf_mod():
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        s = "SELECT Count(*) from extracted_document_data E JOIN audit_trail A on E.id= A.id and E.key=A.key where E.confidence> 90"
        cur.execute(s)
        a = cur.fetchall()
        return jsonify(a)
    except Exception as error:
        LOGGER.exception(error)
        raise error

# low confidence modifications


@app.route('/low_conf_mod', methods=['GET'])
def low_conf_mod():
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        s = "SELECT Count(*) from extracted_document_data E JOIN audit_trail A on E.id= A.id and E.key=A.key where E.confidence< 90"
        cur.execute(s)
        a = cur.fetchall()
        return jsonify(a)
    except Exception as error:
        LOGGER.exception(error)
        raise error

# updated missing values

@app.route('/updated_missing_val', methods=['GET'])
def updated_missing_val():
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        s = "SELECT Count(*) from audit_trail where initial_value='' and final_value <> ''"
        cur.execute(s)
        a = cur.fetchall()
        return jsonify(a)
    except Exception as error:
        LOGGER.exception(error)
        raise error

# unassigned docs

@app.route('/unassigned_docs', methods=['GET'])
def unassigned_docs():
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        s = "SELECT COUNT(*) from document_information where (processor= 'none') OR (qc= 'none' AND processed = true)"
        cur.execute(s)
        a = cur.fetchall()
        return jsonify(a)
    except Exception as error:
        LOGGER.exception(error)
        raise error

# documents being processed

@app.route('/being_processed', methods=['GET','POST'])
def being_processed():
    if request.method == 'POST':
        try:
            req_json= request.json
            start_date= req_json['startdate']
            end_date= req_json['enddate']
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute("SELECT COUNT(*) from document_information where processor != 'none' AND processed= False AND start_date>= %s AND end_date<= %s",(start_date,end_date))
            a = cur.fetchall()
            return jsonify(a)
        except Exception as error:
            LOGGER.exception(error)
            raise error

# in QC

@app.route('/in_qc', methods=['GET','POST'])
def in_qc():
    if request.method == 'POST':
        try:
            req_json= request.json
            start_date= req_json['startdate']
            end_date= req_json['enddate']
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute("SELECT COUNT(*) from document_information where qc != 'none' AND verified= False AND start_date>= %s AND end_date<= %s",(start_date,end_date))
            a = cur.fetchall()
            return jsonify(a)
        except Exception as error:
            LOGGER.exception(error)
            raise error

# completed documents

@app.route('/docs_completed', methods=['GET'])
def docs_completed():
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        s = "SELECT COUNT(*) from document_information where processed= True AND verified= True"
        cur.execute(s)
        a = cur.fetchall()
        return jsonify(a)
    except Exception as error:
        LOGGER.exception(error)
        raise error

# completed for processor
@app.route('/docs_completed_proc', methods=['GET','POST'])
def docs_completed_proc():
    if request.method == 'POST':
        try:
            req_json= request.json
            processor= req_json['processor']
            start_date= req_json['startdate']
            end_date= req_json['enddate']
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute("SELECT COUNT(*) from document_information where processor= %s AND processed= %s AND start_date>= %s AND end_date<= %s",(processor,True,start_date,end_date))
            a = cur.fetchall()[0]
            return jsonify(a[0])
        except Exception as error:
            LOGGER.exception(error)
            raise error

#completed for QC
@app.route('/docs_completed_qc', methods=['GET','POST'])
def docs_completed_qc():
    if request.method == 'POST':
        try:
            req_json= request.json
            qc= req_json['qc']
            start_date= req_json['startdate']
            end_date= req_json['enddate']
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute("SELECT COUNT(*) from document_information where qc= %s AND verified= %s AND start_date>= %s AND end_date<= %s",(qc,True,start_date,end_date))
            a = cur.fetchall()[0]
            return jsonify(a[0])
        except Exception as error:
            LOGGER.exception(error)
            raise error

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000, threaded="True", debug=True)
