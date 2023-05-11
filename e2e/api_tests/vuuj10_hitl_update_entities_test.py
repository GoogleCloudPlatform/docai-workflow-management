"""
Copyright 2022 Google LLC

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

"""
  E2E tests for checking
  HITL updating extracted entity value with user provided values
"""

import requests
import datetime
from endpoint_proxy import get_baseurl
from common.models.document import Document
from common.config import STATUS_IN_PROGRESS, STATUS_SUCCESS, STATUS_ERROR


def add_records(entity, case_id, uid):
  """
  Function to insert records into collection
  ARGS:
  entity :List[Dict] - list of entities
  case_id : str - case_id of the document
  uid : str - uid of the document
  """
  timestamp = datetime.datetime.utcnow()

  d = Document()
  d.case_id = case_id
  d.uid = uid
  d.upload_timestamp = timestamp
  d.active = "active"
  d.system_status = [{
      "stage": "uploaded",
      "status": STATUS_SUCCESS,
      "timestamp": timestamp
  }]
  d.entities = entity
  d.save()
  doc_dict = d.to_dict()
  return doc_dict


def test_update_entities():
  """
  User journey to update the values of the extracted entities
  """
  #Inserting records
  case_id = "uj14_update_entity_1"
  uid = "uj14_update_entity_uid_1"
  entity = [{"entity": "name", "value": "JAMES ADAM", "corrected_value": None}]
  doc_dict = add_records(entity, case_id, uid)

  #Updating entities and making the api request with the parameters
  entity[0]["corrected_value"] = "James fernandez"
  doc_dict["entities"] = entity
  base_url = get_baseurl("hitl-service")
  res = requests.post(base_url + f"/hitl_service/v1/update_entity?"\
    f"uid={uid}",json=doc_dict)
  #Checking if the request was successful
  assert res.status_code == 200

  #Checking if the database is updated correctly
  d = Document()
  doc = d.find_by_uid(uid)
  assert entity == doc.entities
