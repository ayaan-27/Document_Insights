# -*- coding: utf-8 -*-
"""
Created on Wed Aug 25 13:27:47 2021

@author: priyaranjan.kumar
"""


import cv2
import numpy as np
import pandas as pd
from trp import Document
import trp


def table_(response):
    #
    
    dataframes_li = []
    
    def map_blocks(blocks, block_type):
        return {
        block['Id']: block
        for block in blocks
        if block['BlockType'] == block_type
        }


    blocks = response['Blocks']
    tables = map_blocks(blocks, 'TABLE')
    cells = map_blocks(blocks, 'CELL')
    words = map_blocks(blocks, 'WORD')
    selections = map_blocks(blocks, 'SELECTION_ELEMENT')
    
    def get_children_ids(block):
        for rels in block.get('Relationships', []):
            if rels['Type'] == 'CHILD':
                yield from rels['Ids']
                
    
    for table in tables.values():
        
        # Determine all the cells that belong to this table
        table_cells = [cells[cell_id] for cell_id in get_children_ids(table)]
    
        # Determine the table's number of rows and columns
        n_rows = max(cell['RowIndex'] for cell in table_cells)
        n_cols = max(cell['ColumnIndex'] for cell in table_cells)
        content = [[None for _ in range(n_cols)] for _ in range(n_rows)]
    
        # Fill in each cell
        for cell in table_cells:
            cell_contents = [
                words[child_id]['Text']
                if child_id in words
                else selections[child_id]['SelectionStatus']
                for child_id in get_children_ids(cell)
            ]
            i = cell['RowIndex'] - 1
            j = cell['ColumnIndex'] - 1
            content[i][j] = ' '.join(cell_contents)

        # We assume that the first row corresponds to the column names
        dataframe = pd.DataFrame(content[1:], columns=content[0])
        dataframes_li.append(dataframe)
        
        
    return dataframes_li
 
       
    
def form_(response):
    #
    doc_form = Document(response)
    for page in doc_form.pages:
        dict_form_key, dict_form_value = [], []
        for field in page.form.fields:
            
            dict_form_key.append({ 'key': str(field.key),
                            'confidence': round(float(field.key.confidence),2),
                              'x1' : float(field.key.geometry.polygon[0].x), 'y1':float(field.key.geometry.polygon[0].y),
                              'x2' : float(field.key.geometry.polygon[1].x), 'y2':float(field.key.geometry.polygon[1].y),
                              'x3' : float(field.key.geometry.polygon[2].x), 'y3':float(field.key.geometry.polygon[2].y),
                              'x4' : float(field.key.geometry.polygon[3].x), 'y4':float(field.key.geometry.polygon[3].y)
                              })
            
            if str(field.value) == 'None':
                X1, Y1 = float(field.key.geometry.polygon[0].x), float(field.key.geometry.polygon[0].y)
                X2, Y2 = float(field.key.geometry.polygon[1].x), float(field.key.geometry.polygon[1].y)
                X3, Y3 = float(field.key.geometry.polygon[2].x), float(field.key.geometry.polygon[2].y)
                X4, Y4 = float(field.key.geometry.polygon[3].x), float(field.key.geometry.polygon[3].y)
                
                dict_form_value.append({'value' : str(field.value),
                                        'X1' : X1, 'Y1':Y1,
                                        'X2' : X2, 'Y2':Y2,
                                        'X3' : X3, 'Y3':Y3,
                                        'X4' : X4, 'Y4':Y4    
                                        })
                
            else:
                dict_form_value.append({'value' : str(field.value),
                                'X1' : float(field.value.geometry.polygon[0].x), 'Y1':float(field.value.geometry.polygon[0].y),
                                'X2' : float(field.value.geometry.polygon[1].x), 'Y2':float(field.value.geometry.polygon[1].y),
                                'X3' : float(field.value.geometry.polygon[2].x), 'Y3':float(field.value.geometry.polygon[2].y),
                                'X4' : float(field.value.geometry.polygon[3].x), 'Y4':float(field.value.geometry.polygon[3].y)     
                                })

      
    df_form_key = pd.DataFrame(dict_form_key)
    df_form_value = pd.DataFrame(dict_form_value)
    
    #combine both
    dataframe_form = df_form_key.join(df_form_value, on=None, how='right',)
    return dataframe_form


def line_(response):
    doc = trp.Document(response)
    bbox = trp.BoundingBox(width=1, height=1, left=0, top=0)
    lines = doc.pages[0].getLinesInBoundingBox(bbox)
    
    dict_line = []
    for line in lines:
        dict_line.append({'line' : str(line.text), 'confidence': round(float(line.confidence),2),
                            'x1' : float(line.geometry.polygon[0].x), 'y1':float(line.geometry.polygon[0].y),
                            'x2' : float(line.geometry.polygon[1].x), 'y2':float(line.geometry.polygon[1].y),
                            'x3' : float(line.geometry.polygon[2].x), 'y3':float(line.geometry.polygon[2].y),
                            'x4' : float(line.geometry.polygon[3].x), 'y4':float(line.geometry.polygon[3].y)
                        })
                            
    dataframe_line = pd.DataFrame(dict_line)
    return dataframe_line


def alter_coord(image, line_df):
    
    '''  It will change the coordinates in ratio to absolute coordinates'''
    
    img = cv2.imread(image)
    each_page_df = line_df
      
    #for each_page_df in Df_textract_LINE:
    img_length = img.shape[0]
    img_width = img.shape[1]

    # Multiply x values by width and y values by length.
      
    each_page_df['x1'] = (each_page_df['x1']*img_width).apply(np.floor)
    each_page_df['x2'] = (each_page_df['x2']*img_width).apply(np.floor)
    each_page_df['x3'] = (each_page_df['x3']*img_width).apply(np.ceil)
    each_page_df['x4'] = (each_page_df['x4']*img_width).apply(np.floor)

    each_page_df['y1'] =(each_page_df['y1']*img_length).apply(np.floor)
    each_page_df['y2'] =(each_page_df['y2']*img_length).apply(np.ceil)
    each_page_df['y3'] =(each_page_df['y3']*img_length).apply(np.ceil)
    each_page_df['y4'] =(each_page_df['y4']*img_length).apply(np.ceil)
  
    return each_page_df


def alter_coord_form_df(image, form_df):
    
    '''  It will change the coordinates in ratio to absolute coordinates'''
    
    img = cv2.imread(image)
    each_page_df = form_df
      
    #for each_page_df in Df_textract_LINE:
    img_length = img.shape[0]
    img_width = img.shape[1]

    # Multiply x values by width and y values by length.
      
    each_page_df['X1'] = (each_page_df['X1']*img_width).apply(np.floor)
    each_page_df['X2'] = (each_page_df['X2']*img_width).apply(np.floor)
    each_page_df['X3'] = (each_page_df['X3']*img_width).apply(np.ceil)
    each_page_df['X4'] = (each_page_df['X4']*img_width).apply(np.floor)

    each_page_df['Y1'] =(each_page_df['Y1']*img_length).apply(np.floor)
    each_page_df['Y2'] =(each_page_df['Y2']*img_length).apply(np.ceil)
    each_page_df['Y3'] =(each_page_df['Y3']*img_length).apply(np.ceil)
    each_page_df['Y4'] =(each_page_df['Y4']*img_length).apply(np.ceil)
    
    each_page_df['x1'] = (each_page_df['x1']*img_width).apply(np.floor)
    each_page_df['x2'] = (each_page_df['x2']*img_width).apply(np.floor)
    each_page_df['x3'] = (each_page_df['x3']*img_width).apply(np.ceil)
    each_page_df['x4'] = (each_page_df['x4']*img_width).apply(np.floor)

    each_page_df['y1'] =(each_page_df['y1']*img_length).apply(np.floor)
    each_page_df['y2'] =(each_page_df['y2']*img_length).apply(np.ceil)
    each_page_df['y3'] =(each_page_df['y3']*img_length).apply(np.ceil)
    each_page_df['y4'] =(each_page_df['y4']*img_length).apply(np.ceil)
  
    return each_page_df
        
        
                