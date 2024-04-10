import json
import logger as log
from google.cloud import pubsub_v1
import requests

logger = log.get_logger(__name__)

def publish_to_pubsub(topic_name : str, data : dict) -> bool:
    """Publishes a message to a Google Cloud Pub/Sub topic."""
    # Fetch Project ID from Metadata Server
    metadata_server_url = "http://metadata/computeMetadata/v1/project/project-id"
    headers = {"Metadata-Flavor": "Google"}
    project_id = requests.get(metadata_server_url, headers=headers).text
    # Publish the message to Pub/Sub
    try:
        publisher = pubsub_v1.PublisherClient()
        topic_path = publisher.topic_path(project_id, topic_name)
        data = json.dumps(data).encode("utf-8")
        future = publisher.publish(topic_path, data)
        logger.debug(f"Published message to topic: {topic_name} and project_id: {project_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to publish message: {str(e)}")
        return False