#Creating a pubsub resource for queue

#creating pubsub topic

resource "google_pubsub_topic" "queue" {
  name = "queue-topic"
}

#creating pubsub subscription

resource "google_pubsub_subscription" "queue-sub" {
  count = "${var.cloudrun_deploy ? 1 : 0}"

  name  = "queue-sub"
  topic = google_pubsub_topic.queue.name

  ack_deadline_seconds       = 600
  message_retention_duration = "86400s"

  expiration_policy {
    ttl = ""
  }

  push_config {
    push_endpoint = data.google_cloud_run_service.queue-run.status[0].url #calling the cloud run endpoint
    oidc_token {
      service_account_email = module.pubsub-service-account.email
    }
  }

}
