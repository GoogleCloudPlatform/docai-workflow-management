"""
This script has all the common and re-usable functions required for extraction framework

"""

import os
import re
import json
import pandas as pd
from google.cloud import storage


def pattern_based_entities(parser_data, pattern):
    """
    Function return matched text as per pattern
    Parameters
    ----------
    parser_data: text in which pattern is applied
    pattern : pattern

    Returns: Extracted text by using pattern
    -------

    """

    text = parser_data["text"]

    pattern = re.compile(r"{}".format(pattern), flags=re.DOTALL)

    # match as per pattern
    matched_text = re.search(pattern, text)

    if matched_text:
        op = matched_text.group(1)
    else:
        op = None
    return op


def default_entities_extraction(parser_entities, default_entities):
    """
    This function extracted default entities

    Parameters
    ----------
    parser_entities: Specialized parser entities
    default_entities: Default entites that need to extract from parser entities

    Returns : Default entites dict
    -------

    """

    parser_entities_dict = {}

    # retrieve parser given entities
    for each_entity in parser_entities:
        key, val, confidence = each_entity.get("type", ""), each_entity.get("mentionText", ""), round(
            each_entity.get("confidence", 0), 2)

        parser_entities_dict[key] = [val, confidence]

    entity_dict = {}

    # create default entities
    for key in default_entities.keys():
        if key in parser_entities_dict.keys():
            entity_dict[default_entities[key][0]] = {"entity": default_entities[key][0],
                                                     "value": parser_entities_dict[key][0],
                                                     "extraction_confidence": parser_entities_dict[key][1],
                                                     "manual_extraction": False}
        else:
            entity_dict[default_entities[key][0]] = {"entity": default_entities[key][0], "value": None,
                                                     "extraction_confidence": None,
                                                     "manual_extraction": False}

    return entity_dict


def name_entity_creation(entity_dict, name_list):
    """
    This function is to create name from Fname and Gname. Can be re-used if it helps
    Parameters
    ----------
    entity_dict: extracted entities dict
    name_list: list of varibles required to create name

    Returns : derived name entitity dict
    -------

    """
    name = ""
    confidence = 0

    # loop through all the name variables used for name creation
    for each_name in name_list:
        parser_extracted_name = entity_dict[each_name]["value"]
        if parser_extracted_name:
            name += parser_extracted_name
            confidence += entity_dict[each_name]["extraction_confidence"]

    if name.strip():
        name = name.strip()
        confidence = round(confidence / len(name_list), 2)
    else:
        name = None
        confidence = None

    name_dict = {"entity": "Name", "value": name,
                 "extraction_confidence": confidence,
                 "manual_extraction": False}

    return name_dict


def derived_entities_extraction(parser_data, derived_entities):
    """

    This function extract/create derived entities based on config derived entity section

    Parameters
    ----------
    parser_data: text in which pattern is applied
    derived_entities: derived entities dict and pattern

    Returns: derived entities dict
    -------

    """

    derived_entities_extracted_dict = {}

    # loop through derived entities
    for key, val in derived_entities.items():
        pattern = val["rule"]
        pattern_op = pattern_based_entities(parser_data, pattern)

        derived_entities_extracted_dict[key] = {"entity": key, "value": pattern_op,
                                                "extraction_confidence": None,
                                                "manual_extraction": True}

    return derived_entities_extracted_dict


def entities_extraction(parser_data, required_entities, doc_type):
    """
    This function reads information of default and derived entities

    Parameters
    ----------
    parser_data: specialzed parser result
    required_entities: required extracted entities
    doc_type: Document type

    Returns: Required entities dict
    -------

    """

    # Read the entities from the processor

    parser_entities = parser_data["entities"]
    default_entities = required_entities["default_entities"]
    derived_entities = required_entities.get("derived_entities")

    # Extract default entities
    entity_dict = default_entities_extraction(parser_entities, default_entities)

    # if any derived entities then extract them
    if derived_entities:
        # this function can be used for all docs, if derived entities are extracted by using regex pattern
        derived_entities_extracted_dict = derived_entities_extraction(parser_data, derived_entities)
        entity_dict.update(derived_entities_extracted_dict)

    return entity_dict


def standard_entity_mapping(parser_extracted_entity_json):
    # convert extracted json to pandas dataframe
    df_json = pd.DataFrame.from_dict(parser_extracted_entity_json)
    # read entity standardization csv
    entities_standardization_csv = pd.read_csv('Entity Standardization.csv')
    entities_standardization_csv.dropna(how='all', inplace=True)
    # Create a dictionary from the look up dataframe/excel which has the key col and the value col
    dict_lookup = dict(
        zip(entities_standardization_csv['entity'], entities_standardization_csv['standard_entity_name']))
    # Get( all the entity (key column) from the json as a list
    key_list = list(df_json['entity'])

    # Iterate over the key list and check if the key is in the dictionary
    if all(i in dict_lookup for i in key_list):
        # Replace the value by creating a list by looking up the value and assign to json entity
        df_json['entity'] = [dict_lookup[item] for item in key_list]
        # convert datatype from object to int for column 'extraction_confidence'
        df_json['extraction_confidence'] = pd.to_numeric(df_json['extraction_confidence'], errors='coerce')

        # check if there is any repeated entity (many to one)
        if any(df_json.duplicated('entity')):

            # check if there is any None value in json (value field)
            if any(df_json['value'].apply(lambda x: x == None)):
                df_none = df_json[df_json['value'].isna()]
                df_json.drop(df_none.index, inplace=True)
                # concatenation of same entities values
                df_conc = df_json.groupby('entity')['value'].apply(' '.join).reset_index()
                # average of extraction_confidence of same/repeated entities
                df_av = df_json.groupby(['entity', 'manual_extraction'])[
                    'extraction_confidence'].mean().reset_index().round(2)
                df_final = pd.merge(df_conc, df_av, on="entity", how="inner")
                df_final = df_final.append(df_none, ignore_index=True)

                def is_digit(s):
                    """Return True if all characters in the string are digits or space characters."""
                    return s.replace(' ', '').isdigit()  # remove spaces

                for i in range(len(df_final)):
                    # check if the value is digit and have more than one space between digits for "DOB" format entities
                    if (is_digit(df_final.loc[i, "value"]) == True) & (df_final.loc[i, "value"].count(" ") > 1):
                        # replace ' ' with '/' for "DOB" format entities
                        add_delimiter_date = df_final.loc[i, 'value'].replace(' ', '/')
                        df_final.loc[i, 'value'] = add_delimiter_date
                        entities_extraction_dict = df_final.reset_index().to_dict(orient='records')
                        extracted_entities_final_json = [{k: v for k, v in d.items() if k != 'index'} for d in
                                                         entities_extraction_dict]
                        return extracted_entities_final_json
                    else:
                        entities_extraction_dict = df_final.reset_index().to_dict(orient='records')
                        extracted_entities_final_json = [{k: v for k, v in d.items() if k != 'index'} for d in
                                                         entities_extraction_dict]
                        return extracted_entities_final_json

            else:
                # concatenation of same entities values
                df_conc = df_json.groupby('entity')['value'].apply(' '.join).reset_index()
                # average of extraction_confidence of same/repeated entities
                df_av = df_json.groupby(['entity', 'manual_extraction'])[
                    'extraction_confidence'].mean().reset_index().round(2)
                df_final = pd.merge(df_conc, df_av, on="entity", how="inner")

                def is_digit(s):
                    """Return True if all characters in the string are digits or space characters."""
                    return s.replace(' ', '').isdigit()  # remove spaces

                for i in range(len(df_final)):
                    # check if the value is digit and have more than one space between digits for "DOB" format entities
                    if (is_digit(df_final.loc[i, "value"]) == True) & (df_final.loc[i, "value"].count(" ") > 1):
                        # replace ' ' with '/' for "DOB" format entities
                        add_delimiter_date = df_final.loc[i, 'value'].replace(' ', '/')
                        df_final.loc[i, 'value'] = add_delimiter_date
                        entities_extraction_dict = df_final.reset_index().to_dict(orient='records')
                        extracted_entities_final_json = [{k: v for k, v in d.items() if k != 'index'} for d in
                                                         entities_extraction_dict]
                        return extracted_entities_final_json
                    else:
                        entities_extraction_dict = df_final.reset_index().to_dict(orient='records')
                        extracted_entities_final_json = [{k: v for k, v in d.items() if k != 'index'} for d in
                                                         entities_extraction_dict]
                        return extracted_entities_final_json

        else:
            entities_extraction_dict = df_json.reset_index().to_dict(orient='records')
            extracted_entities_final_json = [{k: v for k, v in d.items() if k != 'index'} for d in
                                             entities_extraction_dict]
            return extracted_entities_final_json

   


def form_parser_entities_mapping(form_parser_entity_list, mapping_dict, form_parser_text):
    """
    Form parser entity mapping function

    Parameters
    ----------
    form_parser_entity_list: Extracted form parser entities before mapping
    mapping_dict: Mapping dictionary have info of default, derived entities along with desired keys

    Returns: required entities - list of dicts having entity, value, confidence and manual_extraction information
    -------

    """

    # extract entities information from config files
    default_entities = mapping_dict.get("default_entities")

    derived_entities = mapping_dict.get("derived_entities")

    df = pd.DataFrame(form_parser_entity_list)
    print(df['value_coordinates'])

    required_entities_list = []

    # loop through one by one deafult entities mentioned in the config file
    # for duplicate entities
    for each_ocr_key, each_ocr_val in default_entities.items():
        idx_list = df.index[df['key'] == each_ocr_key].tolist()
        

        # loop for matched records of mapping dictionary
        for idx, each_val in enumerate(each_ocr_val):
           
            if idx_list:
                try:
                    
                    # creating response
                    temp_dict = {"entity": each_val, "value": df['value'][idx_list[idx]],
                                 "extraction_confidence": df['value_confidence'][idx_list[idx]],
                                 "manual_extraction": False,
                                  "value_coordinates":df['value_coordinates'][idx_list[idx]],
                                 "key_coordinates":df['key_coordinates'][idx_list[idx]],
                                 "page_no":df['page_no'][idx_list[idx]],
                                  "page_width":df['page_width'][idx_list[idx]],
                                 "page_height":df['page_height'][idx_list[idx]]
                                   }
                except Exception as e:
                    print('Key not found in parser output')
                 
                    temp_dict = {"entity": each_val, "value": None,
                                 "extraction_confidence": None,
                                 "manual_extraction": False,
                                  "value_coordinates":None,
                                 "key_coordinates":None,
                                 "page_no":None,
                                  "page_width":None,
                                 "page_height":None
                                }

                required_entities_list.append(temp_dict)
            else:
                # filling null value if parser didn't extract
                temp_dict = {"entity": each_val, "value": None,
                             "extraction_confidence": None,
                             "manual_extraction": False,
                              "value_coordinates":None,
                              "key_coordinates":None,
                              "page_no":None,
                              "page_width":None,
                              "page_height":None
                            }
                required_entities_list.append(temp_dict)

    if derived_entities:
        # this function can be used for all docs, if derived entities are extracted by using regex pattern
        parser_data = {}
        parser_data["text"] = form_parser_text
        derived_entities_op_dict = derived_entities_extraction(parser_data, derived_entities)
        required_entities_list.extend(list(derived_entities_op_dict.values()))

    return required_entities_list


def download_pdf_gcs(bucket_name=None, gcs_uri=None, file_to_download=None, output_filename=None) -> str:
    """
    Function takes a path of an object/file stored in GCS bucket and downloads
    the file in the current working directory

    Args:
        bucket_name (str): bucket name from where file to be downloaded
        gcs_uri (str): GCS object/file path
        output_filename (str): desired filename
        file_to_download (str): gcs file path excluding bucket name.
            Ex: if file is stored in X bucket under the folder Y with filename ABC.txt
            then file_to_download = Y/ABC.txt
    Return:
        pdf_path (str): pdf file path that is downloaded from the bucket and stored in local
    """

    if bucket_name is None:
        bucket_name = gcs_uri.split('/')[2]

    # if file to download is not provided it can be extracted from the GCS URI
    if file_to_download is None and gcs_uri is not None:
        file_to_download = '/'.join(gcs_uri.split('/')[3:])

    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(file_to_download)

    # save file, if output path provided
    if output_filename:
        with open(output_filename, "wb") as file_obj:
            blob.download_to_file(file_obj)

    return blob


def clean_form_parser_keys(text):
    """
    Cleaning form parser keys

    Parameters
    ----------
    text: original text before noise removal - removed spaces, newlines

    Returns: text after noise removal
    -------

    """

    # removing special characters from beginning and end of a string
    if len(text):
        text = text.strip()
        text = text.replace("\n", ' ')
        text = re.sub(r"^\W+", "", text)
        last_word = text[-1]
        text = re.sub(r"\W+$", "", text)
        if last_word in [")", "]"]:
            text += last_word

    return text


def del_gcs_folder(bucket, folder):
    """
    This function is to delete folder from gcs bucket, this is used to delete temp folder from bucket

    Parameters
    ----------
    bucket: Bucket name
    folder: Folder name inside bucket

    Returns : None
    -------

    """

    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket)
    blobs = bucket.list_blobs(prefix=folder)
    for blob in blobs:
        blob.delete()

    print("Delete successful")


def extract_form_fields(doc_element: dict, document: dict):
    """

    # Extract form fields from form parser raw json

    Parameters
    ----------
    doc_element: Entitiy
    document: Extracted OCR Text

    Returns: Entity name and Confidence
    -------

    """

    response = ""
    # If a text segment spans several lines, it will
    # be stored in different text segments.
    for segment in doc_element.text_anchor.text_segments:
        start_index = (
            int(segment.start_index)
            if segment in doc_element.text_anchor.text_segments
            else 0
        )
        end_index = int(segment.end_index)
        response += document.text[start_index:end_index]
    confidence = doc_element.confidence
    coordinate=doc_element.bounding_poly.normalized_vertices
    return response, confidence,coordinate
    


def extraction_accuracy_calc(total_entities_list):
    """

    This function is to calculate document extraction accuracy
    Parameters
    ----------
    total_entities_list: Total extracted list of dict

    Returns : Extraction score
    -------

    """

    # get fields extraction accuracy
    entity_accuracy_list = [each_entity.get("extraction_confidence") if each_entity.get("extraction_confidence") else 0
                            for each_entity in
                            total_entities_list if not each_entity.get("manual_extraction")]

    extraction_accuracy = round(sum(entity_accuracy_list) / len(entity_accuracy_list), 3)

    return extraction_accuracy


if __name__ == "__main__":

    # these variables are used to run in local environment

    parser_json = "/home/jupyter/parsers_output"
    #extracted_entities = "/home/jupyter/parsers_output"

    required_entities = {
        "default_entities": ["Family Name", "Given Names", "Document Id", "Expiration Date", "Date Of Birth",
                             "Issue Date",
                             "Address"],
        "derived_entities": {"Name": {"rule": ["Given Names", "Family Name"]}, "Sex": {"rule": "pattern"}}
    }

    required_entities = {
        "default_entities": ["invoice_id", "invoice_date", "due_date", "receiver_name", "service_address",
                             "total_tax_amount",
                             "supplier_account_number"]
    }

    json_files = os.listdir(parser_json)

    for each_json in json_files:
        with open(os.path.join(parser_json, each_json), 'r') as j:
            data = json.loads(j.read())
           # print(each_json)

            entity_dict = entities_extraction(data, required_entities)

            # save extracted entities json
            #with open("{}.json".format(os.path.join(extracted_entities, each_json.split('.')[0])), "w") as outfile:
             #   json.dump(entity_dict, outfile, indent=4)

    download_pdf_gcs(
        gcs_uri='gs://async_form_parser/input/arizona-driver-form-13.pdf'
    )

    total_entities_list = [
        {
            "entity": "Social Security Number",
            "value": None,
            "extraction_confidence": 1,
            "manual_extraction": False
        },
        {
            "entity": "Date",
            "value": None,
            "extraction_confidence": None,
            "manual_extraction": False
        }
    ]

    #extraction_accuracy_calc(total_entities_list)