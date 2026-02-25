# -*- coding: utf-8 -*-
"""
Created on Wed Jul 15 22:24:14 2020.

@author: Rahul Gupta.
"""

import os
import fitz #PyMuPDF 
import shutil


def pdftopng(file_path, pwd):
    """."""
    
    fol = 'PNGs'
    image_path = os.path.join(pwd, fol)
    if os.path.exists(image_path):
        shutil.rmtree(image_path)
        os.makedirs(image_path)
    else:
       os.makedirs(image_path)
        
    doc_ = fitz.open(file_path)
    pages_ = doc_.pageCount
    fol_ = os.path.splitext(os.path.basename(file_path))[0]
    print('  Converting pdf to images ...')
    try:
        if os.path.exists(os.path.join(image_path, fol_)):
            shutil.rmtree(os.path.join(image_path, fol_))
            os.makedirs(os.path.join(image_path, fol_))
        else:
            os.makedirs(os.path.join(image_path, fol_))
        for p in range(pages_):
            print('    Page ' + str(p+1))
            page = doc_.loadPage(p)
            mat = fitz.Matrix(3, 3)
            pix = page.getPixmap(matrix=mat)
            out_name = fol_ + '_'+'page_'+ str(p) + '.png'
            output = os.path.join(image_path, fol_, out_name)
            # print(output)
            pix.writePNG(output)
    except Exception as e:
        print(fol_, e)
    doc_.close()
    return  os.path.join(image_path, fol_)



