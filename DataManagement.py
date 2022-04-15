# Copyright (c) 2022 Taner Esat <t.esat@fz-juelich.de>

import numpy as np 
import os
import time
import json

def saveData(generalSettings, scheme, comment, additionalInformation, data, experimentType='data'):
    currentDate = time.strftime('%Y-%m-%d', time.localtime())

    if experimentType == 'TF':
        folder = os.path.join(generalSettings['TF_Folder'], currentDate)
    else:
        folder = os.path.join(generalSettings['Data_Folder'], currentDate)
        
    if not os.path.exists(folder):
        os.mkdir(folder)
        
    filename = os.path.join(folder, '{}.json'.format(time.strftime('%H-%M-%S', time.localtime())))
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
    d = {'Timestamp': timestamp,'GeneralSettings': generalSettings,  'Scheme': scheme, 'Comment': comment, 'additionalInformation': additionalInformation, 'Data': data}
    with open(filename, 'w', encoding ='utf8') as json_file:
        json.dump(d, json_file, allow_nan=True, indent=4)

    return filename

def loadData(path, filename):
    file = '{}.json'.format(os.path.join(path, filename))
    with open(file) as json_file:
        data = json.load(json_file)
    
    return data