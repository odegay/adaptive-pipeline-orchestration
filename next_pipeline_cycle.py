import random
import json
import base64
import requests
from adpipwfwconst import MSG_TYPE
from adpipwfwconst import PIPELINE_TOPICS as TOPICS
from adpipsvcfuncs import publish_to_pubsub, fetch_gcp_secret
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Capture DEBUG, INFO, WARNING, ERROR, CRITICAL

api_url = fetch_gcp_secret("adaptive-pipeline-persistence-layer-url")
api_key = fetch_gcp_secret("adaptive-pipeline-API-token")

def continue_pipeline_required(pipeline_id) -> bool:    
    #TODO: Implement the logic to decide if the pipeline should continue with the next cycle
    #Randomly returning True or False based on the random generator
    return bool(random.getrandbits(1))    

# Function to complete the pipeline
def complete_pipeline(pipeline_id) -> bool:
    #TODO: Update the pipeline status to completed
    message_data = {
        "pipeline_id": pipeline_id,
        "MSG_TYPE": MSG_TYPE.ADAPTIVE_PIPELINE_END.value       
    }        
    
    if not publish_to_pubsub(TOPICS.WORKFLOW_TOPIC.value, message_data):
        return False
    logger.debug(f"Completed the pipeline with ID: {pipeline_id}")
    return True    

def create_new_pipeline() -> str:    
    if not api_url:
        logger.error("Failed to fetch the API URL")
        return None
    data = {
        "status": MSG_TYPE.ADAPTIVE_PIPELINE_START.value
    }
    headers = {
        "Authorization": api_key
    }
    try:
        response = requests.post(f"{api_url}/create", json=data, headers=headers)
        if response.status_code == 200:
            pipeline_id = response.json().get("id")
            logger.debug(f"Created a new pipeline with ID: {pipeline_id}")
            return pipeline_id
        else:
            logger.error(f"Failed to create a new pipeline. Response: {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return None

def send_message_start_config_msg(pipeline_id: str, topics_value: str) -> bool:
    message_data = {
        "pipeline_id": pipeline_id,
        "MSG_TYPE": MSG_TYPE.START_MODEL_CONFIGURATION.value
    }
    if not publish_to_pubsub(topics_value, message_data):
        logger.error(f"Failed to publish message to topic: {topics_value}")
        return False
    logger.debug(f"Published message to topic: {topics_value} for pipeline ID: {pipeline_id}")
    return True

def next_pipeline_cycle(event: dict, context: dict) -> bool:
    if 'data' in event:
        pubsub_message = base64.b64decode(event['data']).decode('utf-8')
        pubsub_message = json.loads(pubsub_message)
        msg_type = pubsub_message.get("MSG_TYPE")

        if msg_type == MSG_TYPE.ADAPTIVE_PIPELINE_START.value:
            logger.debug("Starting a new adaptive pipeline")            
            pipeline_id = create_new_pipeline()
            if not pipeline_id:
                return False                        
            if not send_message_start_config_msg(pipeline_id, TOPICS.CONFIG_TOPIC.value):
                return False
            else:
                return True            
        elif "pipeline_id" in pubsub_message:
            pipeline_id = pubsub_message['pipeline_id']
            if continue_pipeline_required(pipeline_id):
                logger.debug(f"Continuing the pipeline with ID: {pipeline_id}")
                if not send_message_start_config_msg(pipeline_id, TOPICS.CONFIG_TOPIC.value):
                    return False
                else:
                    #TODO: Update the pipeline status to in progress in the database
                    return True
            else:
                logger.debug(f"Pipeline with ID: {pipeline_id} has completed all the cycles")
                #TODO: Update the pipeline status to completed in the database
                return False
        else:
            logger.error("Pipeline ID is missing in the message")
            #TODO: Update the pipeline status to failed in the database and move the pipeline to the failed queue
            return False   
    else:
        logger.error("Data is missing in the event")
        #TODO: Update the pipeline status to failed in the database and move the pipeline to the failed queue
        return False 