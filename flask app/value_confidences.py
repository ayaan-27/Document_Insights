# -*- coding: utf-8 -*-
"""
Spyder Editor
"""


# prashanth Arun  16/09/2021


import json
import pandas as pd

def get_json_data(raw_json):
    """
    Returns a Python dictionary of the JSON content

    Parameters
    ----------
    raw_data : string (multi-line)
        The JSON data to be extracted

    Returns
    -------
    json_data: dict
        The JSON data loaded as a Python dictionary

    """
    
    try:
        json_data = json.loads(raw_json)
    except:
        raw_json = raw_json.replace("\'", "\"")
        json_data = json.loads(raw_json)
        
    return json_data



def get_word_data(word_list, word_id):
    """
    Returns the text associated with the given ID.
    
    Parameters
    ----------
    word_list: list
        The list of blocks (each of type dict) of type WORD
        
    word_id: string
        The ID of the word to be matched
        
    Returns
    -------
    corr_values: dict
        A dictionary containing the word and its associated confidence
    """
    
    corr_values = {"Word": "", "Confidence": 0.0}
    
    for word in word_list:
        if word_id == word["Id"]:
            corr_values["Word"] = word["Text"]
            corr_values["Confidence"] = float(word["Confidence"]) if word["Confidence"] != '' else 0.0
            
    return corr_values



def weighted_average(word_list, confidence_list):
    """
    Returns the weighted average of the confidences of the words, based on the number of 
    letters in each word. Requires that len(word_list) == len(confidence_list).
    
    Parameters
    ----------
    word_list: list
        The list of words for which to calculate the average confidences
        
    confidence_list: list
        The list of corresponding confidence values for each word
        
    Returns
    -------
    avg: float
        The weighted average of the confidences
    """
    
    assert len(word_list) == len(confidence_list)
    
    weighted_confidence = 0.0
    num_letters = 0
    
    for i in range(len(word_list)):
        weighted_confidence += len(word_list[i]) * confidence_list[i]
        num_letters += len(word_list[i])
        
    if num_letters == 0:
        return 0
    else:
        avg = weighted_confidence / num_letters
        return avg
    


def extract_field_and_confidences(response):
    
    """
    Extracts the words in a key-value set, along with the confidences of the values.
    The final value confidence is displayed as the weighted average of the value words' confidences.
    
    Parameters
    ----------
    response: string
        The JSON response from Textract
        
    Returns
    -------
    data_df: pandas DataFrame
        The table of KEY words, VALUE words, and VALUE confidences
    """
    
    #json_data = get_json_data(response)
    json_data = response
    
    # Getting the lists of WORD and KEY_VALUE_SET text blocks
    words = [x for x in json_data["Blocks"] if x["BlockType"] == "WORD"]
    key_value_pairs = [x for x in json_data["Blocks"] if x["BlockType"] == "KEY_VALUE_SET"]
    
    i = 0
    val_list = []
    
    while i < len(key_value_pairs):
        
        # Typically, KEY entities are indexed with even numbers
        # Also, from observation, KEY entities always have a "Relationships" field
        
        key = key_value_pairs[i]
        value = key_value_pairs[i + 1]
        
        i += 2
        
        # Getting the words that correspond to the key of the KVP
        key_words = [get_word_data(words, word_id)["Word"] for word_id in key["Relationships"][1]["Ids"]]
        value_words = []
        value_confidences = []
        
        # Value words are tricky sometimes...they may not have a "Relationships" field
        try:
            value_data = [get_word_data(words, word_id) for word_id in value["Relationships"][0]["Ids"]]
            value_words = [element["Word"] for element in value_data]
            value_confidences = [element["Confidence"] for element in value_data]
        except KeyError:
            pass
        
        # Enclosing the required data in a dictionary
        word_dict = {"Key": " ".join(key_words),
                    "Value": " ".join(value_words),
                    "Value Confidence": weighted_average(value_words, value_confidences)}
        
        val_list.append(word_dict)
        
    data_df = pd.DataFrame(val_list)
    
    return data_df