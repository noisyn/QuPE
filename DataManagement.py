# Copyright (c) 2022-2023 Taner Esat <t.esat@fz-juelich.de>

import json
import os
import time


def saveData(generalSettings, scheme, comment, additionalInformation, data, experimentType='data'):
    """Saves measurement data as JSON file.

    Args:
        generalSettings (dict): Generel settings.
        scheme (dict): Pump-Probe or RF measurement scheme.
        comment (dict): Comments.
        additionalInformation (dict): Additional information.
        data (dict): Measurement data.
        experimentType (str, optional): 'TF': Transfer function data. 'CT': Crosstalk data. 'Data': Experimental data. Defaults to 'data'.

    Returns:
        str: Path and filename of the saved JSON file.
    """    
    currentDate = time.strftime('%Y-%m-%d', time.localtime())

    if experimentType == 'TF':
        folder = os.path.join(generalSettings['TF_Folder'], currentDate)
    elif experimentType == 'CT':
        folder = os.path.join(generalSettings['CT_Folder'], currentDate)
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
    """Loads a JSON data file.

    Args:
        path (str): Path of the file.
        filename (str): Filename without file extension.

    Returns:
        dict: Read-in data.
    """    
    file = '{}.json'.format(os.path.join(path, filename))
    with open(file) as json_file:
        data = json.load(json_file)
    
    return data