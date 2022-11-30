/**
 * Copyright 2022 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     https://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
 */

resource "google_storage_bucket" "cloudbuild-logs" {
  name          = "${var.project_id}-cloudbuild-logs"
  location      = var.storage_multiregion
  storage_class = "NEARLINE"

  uniform_bucket_level_access = true
  labels = {
    goog-packaged-solution = "prior-authorization"
  }
  lifecycle_rule {
    condition {
      age = 356
    }
    action {
      type = "Delete"
    }
  }
}
