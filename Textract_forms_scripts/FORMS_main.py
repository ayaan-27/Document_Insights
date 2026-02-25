# -*- coding: utf-8 -*-
"""
Created on Thu Oct 14 16:48:47 2021

@author: priyaranjan.kumar
"""


import boto3
import cv2
import os
import pandas as pd
import shutil
from trp import Document

import analyze_table_forms
import value_confidences
import value_confidences_min

textract = boto3.client('textract', region_name='eu-west-1', verify=False)


def call_textract_(image_):
    
    with open(image_, "rb") as document:
        response = textract.analyze_document(Document = {'Bytes': document.read(),},FeatureTypes = ["FORMS","TABLES"])

        #table response
        table_df_li = analyze_table_forms.table_(response)  #table_df is list of dataframes
        
        #iterate over df
        for i in range(len(table_df_li)):
            save_results(table_df_li[i], image_, "table_"+ str(i+1))
    
        
        #form response
        form_df_1 = analyze_table_forms.form_(response)   #form_df is dataframe
        form_df_2 = analyze_table_forms.alter_coord_form_df(image_, form_df_1)
        confidence_df = value_confidences.extract_field_and_confidences(response)
        form_df = form_df_2.join(confidence_df["Value Confidence"], how = "right")
        
        confidence_df2 = value_confidences_min.extract_field_and_confidences(response)
        form_df = form_df.join(confidence_df2["Value Confidence minm"], how = "right")
        
        save_results(form_df, image_, "form")

        #line_reponse
        line_df = analyze_table_forms.line_(response)
        line_df = analyze_table_forms.alter_coord(image_, line_df)
        save_results(line_df, image_, "line")
        print('result saved')

        #word response               
                
            
def save_results(df, image, extra):
    pwd = os.getcwd()
    folder_name = os.path.splitext(os.path.basename(image))[0]
    tsv_path = os.path.join(pwd,'tsvs',folder_name)
    if not os.path.exists(tsv_path): 
        os.makedirs(tsv_path)
    df.to_csv(os.path.join(tsv_path ,(folder_name + "_" + extra + ".tsv")), sep = "\t")
    
    
    
# Helper commands
#image_ = r'C:\Users\priyaranjan.kumar\OneDrive - Mphasis\sample_poc_workflow\Type_1_CI772786246103_021532596872409-000001.png'
#call_textract_(image_)
