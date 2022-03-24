"""
  Tests for classification endpoints
"""
import os
# disabling pylint rules that conflict with pytest fixtures
# pylint: disable=unused-argument,redefined-outer-name,unused-import
from testing.fastapi_fixtures import client_with_emulator
from common.testing.firestore_emulator import firestore_emulator, clean_firestore

from unittest.mock import Mock, patch
from unittest import mock
# assigning url
api_url = "http://localhost:8080/classification_service/v1/classification/classification_api"

os.environ["FIRESTORE_EMULATOR_HOST"] = "localhost:8080"
os.environ["GOOGLE_CLOUD_PROJECT"] = "fake-project"
SUCCESS_RESPONSE = {"status": "Success"}

# def call_to_classify_all_parameters():
#   response = request.post(f"{api_url}?case_id=%20123&uid=5fd0e97e-9dea-11ec-8e64-da7c2efe947f&gcs_url=gs%3A%2F%2Fdocument-upload-test%2F%20123%2F5fd0e97e-9dea-11ec-8e64-da7c2efe947f%2Ffuture-genral.pdf")
#   return response

# def call_to_classify_no_case_id():
#   response = request.post(f"{api_url}?case_id=&uid=5fd0e97e-9dea-11ec-8e64-da7c2efe947f&gcs_url=gs%3A%2F%2Fdocument-upload-test%2F%20123%2F5fd0e97e-9dea-11ec-8e64-da7c2efe947f%2Ffuture-genral.pdf")
#   return response


# def call_to_classify_no_uid():
#   response = request.post(f"{api_url}?case_id=%20123&uid=&gcs_url=gs%3A%2F%2Fdocument-upload-test%2F%20123%2F5fd0e97e-9dea-11ec-8e64-da7c2efe947f%2Ffuture-genral.pdf")
#   return response

# def call_to_classify_invalid_gcs_uri():
#   response = request.post(f"{api_url}?case_id=%20123&uid=&gcs_url=gs%3A%2F%2Fdocument-upload-test%2F%20123%2F5fd0e97e-9dea-11ec-8e64-da7c2efe947f%2Ffuture-genral.")
#   return response


def test_classify_all_parameters(client_with_emulator):
  """
    Test to check the classification endpoint with all parameters
  """
  res = {
      "case_id": "abc",
      "uid": "def",
      "predicted_class": "DL",
      'model_conf': 0.99,
    }
  mockresponse = Mock()
  mockresponse.status_code = 200
  with patch('routes.classification.predict_doc_type',return_value=res):
    with patch('routes.classification.update_classification_status',return_value = mockresponse):
      with patch('routes.classification.Logger'):
        response = client_with_emulator.post(f"{api_url}?case_id=abc&uid=def&gcs_url=gs://document-upload-test/abc/def/arkansas_dl_converted.pdf")
        assert response.status_code == 200


def test_classify_with_missing_parameters_caseid(client_with_emulator):
  """
    Test to check the classification endpoint with empty case_id
  """
  res = {
      "case_id": "abc",
      "uid": "def",
      "predicted_class": "DL",
      'model_conf': 0.99,
    }
  mockresponse = Mock()
  mockresponse.status_code = 200
  with patch('routes.classification.predict_doc_type',return_value=res):
    with patch('routes.classification.update_classification_status',return_value = mockresponse):
      with patch('routes.classification.Logger'):
        response = client_with_emulator.post(f"{api_url}?case_id=&uid=def&gcs_url=gs://document-upload-test/abc/def/arkansas_dl_converted.pdf")
        assert response.status_code == 400

def test_classify_with_missing_parameters_uid(client_with_emulator):
  """
    Test to check the classification endpoint with empty uid
  """
  res = {
      "case_id": "abc",
      "uid": "def",
      "predicted_class": "DL",
      'model_conf': 0.99,
    }
  mockresponse = Mock()
  mockresponse.status_code = 200
  with patch('routes.classification.predict_doc_type',return_value=res):
    with patch('routes.classification.update_classification_status',return_value = mockresponse):
      with patch('routes.classification.Logger'):
        response = client_with_emulator.post(f"{api_url}?case_id=abc&uid=&gcs_url=gs://document-upload-test/abc/def/arkansas_dl_converted.pdf")
        assert response.status_code == 400

  

def test_classify_with_invalid_gcs_uri(client_with_emulator):
  """
    Test to check the classification endpoint with invalid gcs uri
  """
  res = {
      "case_id": "abc",
      "uid": "def",
      "predicted_class": "DL",
      'model_conf': 0.99,
    }
  mockresponse = Mock()
  mockresponse.status_code = 200
  with patch('routes.classification.predict_doc_type',return_value=res):
    with patch('routes.classification.update_classification_status',return_value = mockresponse):
      with patch('routes.classification.Logger'):
        response = client_with_emulator.post(f"{api_url}?case_id=&uid=def&gcs_url=gs://document-upload-test/abc/def/arkansas_dl_converted.pdf")
        assert response.status_code == 400
