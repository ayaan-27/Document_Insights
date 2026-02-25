import boto3
import cv2
import os
import pandas as pd
import shutil
from trp import Document
import ntpath
import time 

import analyze_table_forms
import pdf_to_png
import value_confidences
import value_confidences_min


textract = boto3.client('textract', region_name='eu-west-1', verify=False)

def input_(input_file_path):
    
    pwd = os.getcwd()
    image_file_list = []
    
    folder_ = os.path.splitext(os.path.basename(input_file_path))[0]
    tsv_path = os.path.join(pwd,'tsvs',folder_)
    if not os.path.exists(tsv_path): 
        os.makedirs(tsv_path)
        
        
    if input_file_path.endswith(".pdf") :
        # call pdftopng and return pnglocation
        png_location = pdf_to_png.pdftopng(input_file_path, pwd)
        image_file_list = sorted([os.path.join(png_location, file) for file in os.listdir(png_location)], key=os.path.getctime)
    
    else:
        if input_file_path.endswith(".png") :
            image_file_list = [input_file_path]
            
        else:
            image_file_list =[]
            print("file format not supported")
        
    return image_file_list


def path_leaf(path):
    head, tail = ntpath.split(path)
    return tail or ntpath.basename(head)


def call_textract_(id_, image_list, filename, mode = 'BOTH'):
    
    #iterate over image_list
    for image_ in image_list:
        
        print("image_list", image_list)
        print("image", image_)
        if path_leaf(image_).split('.')[1] == 'pdf':
            page_no = path_leaf(image_).split('.')[0].split('_page_').pop()
            #doc_filename = '_'.join(path_leaf(image_).split('.')[0].split('_')[:-2])
        else:
            page_no=0
            #doc_filename = '_'.join(path_leaf(image_).split('.')[0].split('_'))

        if mode == 'BOTH':
            
            with open(image_, "rb") as document:
                response = textract.analyze_document(Document = {'Bytes': document.read(),},FeatureTypes = ["FORMS","TABLES"])
        
                #table response
                table_df_li = analyze_table_forms.table_(response)  #table_df is list of dataframes
                
                #iterate over df
                for i in range(len(table_df_li)):
                    table_df_li[i]["filename"] = filename
                    table_df_li[i]["page"] = page_no
                    save_results(table_df_li[i], image_, str(id_)+"_table_"+ str(i+1))
                
                
                #form response
                form_df_1 = analyze_table_forms.form_(response)   #form_df is dataframe
                form_df_2 = analyze_table_forms.alter_coord_form_df(image_, form_df_1)
                confidence_df = value_confidences.extract_field_and_confidences(response)
                form_df = form_df_2.join(confidence_df["Value Confidence"], how = "right")
                
                confidence_df2 = value_confidences_min.extract_field_and_confidences(response)
                form_df = form_df.join(confidence_df2["Value Confidence minm"], how = "right")
                form_df['filename'] = filename
                form_df['page'] = page_no
                form_df['id'] = id_ 
                form_df['wrong']= False
                #save_results(form_df, image_, "form")

                
                #########
                #line_reponse
                line_df = analyze_table_forms.line_(response)
                line_df = analyze_table_forms.alter_coord(image_, line_df)
                line_df['filename'] = filename
                line_df['page'] = page_no   
                line_df['id'] = id_
                #save_results(line_df, image_, "line")
                
            return form_df,line_df
        
        
def save_results(df, image, extra):
    
    pwd = os.getcwd()
    folder_name = os.path.splitext(os.path.basename(image))[0]
    tsv_path = os.path.join(pwd,'tsvs',folder_name)
    if not os.path.exists(tsv_path): 
        os.makedirs(tsv_path)
    print(os.path.join(tsv_path ,(folder_name + "_" + extra + ".tsv")))    
    df.to_csv(os.path.join(tsv_path ,(folder_name + "_" + extra + ".tsv")), sep = "\t")
  
    
      
def df_processing(form_df, line_df):
    
    line_df["x1y1"] = line_df[["x1","y1"]].apply(tuple, axis=1)
    line_df["x2y2"] = line_df[["x2","y2"]].apply(tuple, axis=1)
    line_df["x3y3"] = line_df[["x3","y3"]].apply(tuple, axis=1)
    line_df["x4y4"] = line_df[["x4","y4"]].apply(tuple, axis=1)
    line_df["Coordinates"] = line_df[["x1y1","x2y2","x3y3","x4y4"]].apply(tuple, axis=1)
    line_df.drop(columns=["x1y1","x2y2","x3y3","x4y4","x1","y1","x2","y2","x3","y3","x4","y4"],inplace=True)
    
    
    form_df["x1y1"] = form_df[["x1","y1"]].apply(tuple, axis=1)
    form_df["x2y2"] = form_df[["x2","y2"]].apply(tuple, axis=1)
    form_df["x3y3"] = form_df[["x3","y3"]].apply(tuple, axis=1)
    form_df["x4y4"] = form_df[["x4","y4"]].apply(tuple, axis=1)
    form_df["Coordinates"] = form_df[["x1y1","x2y2","x3y3","x4y4"]].apply(tuple, axis=1)
    form_df.drop(columns=["x1y1","x2y2","x3y3","x4y4","x1","y1","x2","y2","x3","y3","x4","y4","X1","Y1","X2","Y2","X3","Y3","X4","Y4"],inplace=True)
    
    columns_titles = ['id','key','value','confidence','Value Confidence', 'Value Confidence minm', 'filename', 'page', 'Coordinates','wrong']
    form_df = form_df.reindex(columns=columns_titles)
    form_df.rename(columns={'Value Confidence':'value_confidence','Value Confidence minm':'value_confidence_minm'},inplace=True)

    return form_df, line_df





    
    

