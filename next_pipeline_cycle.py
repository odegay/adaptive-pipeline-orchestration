import random
import uuid
import json
import base64
from adpipwfwconst import MSG_TYPE
from adpipwfwconst import PIPELINE_TOPICS as TOPICS
from service_functions import publish_to_pubsub
import logging
logger = logging.get_logger(__name__)

def continue_pipeline_required(pipeline_id) -> bool:    
    #TODO: Implement the logic to decide if the pipeline should continue with the next cycle
    #Randomly returning True or False based on the random generator
    return bool(random.getrandbits(1))    

# Function to complete the pipeline
def complete_pipeline(pipeline_id) -> bool:
    #TODO: Update the pipeline status to completed
    message_data = {
        "pipeline_id": pipeline_id,
        "MSG_TYPE": MSG_TYPE.ADAPTIVE_PIPELINE_END        
    }        
    
    if not publish_to_pubsub(TOPICS.WORKFLOW_TOPIC.value, message_data):
        return False
    logger.debug(f"Completed the pipeline with ID: {pipeline_id}")
    return True    

def create_and_send_message_start_config_msg(pipeline_id: str, topics_value: str) -> bool:
    message_data = {
        "pipeline_id": pipeline_id,
        "MSG_TYPE": MSG_TYPE.START_MODEL_CONFIGURATION
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

        if msg_type == MSG_TYPE.ADAPTIVE_PIPELINE_START:
            logger.debug("Starting a new adaptive pipeline")
            pipeline_id = str(uuid.uuid4())
            if not create_and_send_message_start_config_msg(pipeline_id, TOPICS.CONFIG_TOPIC.value):
                return False
            else:
                return True            
        elif "pipeline_id" in pubsub_message:
            pipeline_id = pubsub_message['pipeline_id']
            if continue_pipeline_required(pipeline_id):
                logger.debug(f"Continuing the pipeline with ID: {pipeline_id}")
                if not create_and_send_message_start_config_msg(pipeline_id, TOPICS.CONFIG_TOPIC.value):
                    return False
                else:
                    return True
            else:
                logger.debug(f"Pipeline with ID: {pipeline_id} has completed all the cycles")
                return False
        else:
            logger.error("Pipeline ID is missing in the message")
            return False   
    else:
        logger.error("Data is missing in the event")
        return False 