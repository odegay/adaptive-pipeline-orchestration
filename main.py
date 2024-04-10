import base64
import json
from adpipsvcfuncs import publish_to_pubsub
from adpipwfwconst import MSG_TYPE
from adpipwfwconst import PIPELINE_TOPICS as TOPICS
from next_pipeline_cycle import next_pipeline_cycle
import logging
logger = logging.getLogger(__name__)

# Function to handle new model configuration
def model_generation(event: dict, context: dict) -> bool:
    #TODO: Implement the logic for new model generation
    pipeline_id = ""
    if 'data' in event:
        pubsub_message = base64.b64decode(event['data']).decode('utf-8')
        pubsub_message = json.loads(pubsub_message)
        if 'pipeline_id' in pubsub_message:
            pipeline_id = pubsub_message['pipeline_id']
        else:
            logger.error("Pipeline ID is missing in the message")
            return False
    else:
        logger.error("Data is missing in the event")
        return False
    message_data = {
        "pipeline_id": pipeline_id,
        "MSG_TYPE": MSG_TYPE.REQUEST_LLM_NEW_MODEL_CONFIGURATION        
    } 
    if not publish_to_pubsub(TOPICS.CONFIG_TOPIC.value, message_data):
        return False
    else:            
        return True

# Function to handle pipeline step failure
def pipeline_step_failure(event: dict, context: dict) -> bool:
    #TODO: Implement the logic to handle pipeline step failures
    logger.debug("Placeholder for handling pipeline step failure")
    return False

# Function to prepare features
def prepare_features(event: dict, context: dict) -> bool:
    #TODO: Implement the logic to prepare features for the pipeline
    logger.debug("Placeholder for preparing features")
    return True

# Function to start prediction
def start_prediction(event: dict, context: dict) -> bool:
    #TODO: Implement the logic to start prediction
    logger.debug("Placeholder for starting prediction")
    return True

def route_pipeline(event: dict, context: dict) -> bool:
    # Decode the PubSub message    
    #logger.debug(f"Decoded Pub/Sub message: {pubsub_message}")  
    if 'data' in event:
        pubsub_message = base64.b64decode(event['data']).decode('utf-8')
        pubsub_message = json.loads(pubsub_message)
        if 'MSG_TYPE' in pubsub_message:
            if ((pubsub_message['MSG_TYPE'] == MSG_TYPE.ADAPTIVE_PIPELINE_START) or (pubsub_message['MSG_TYPE'] == MSG_TYPE.PREDICTION_SUCCESS)):
                next_pipeline_cycle(event, context)
            elif pubsub_message['MSG_TYPE'] == MSG_TYPE.NEW_MODEL_CONFIGURATION_SUCCESS:
                model_generation(event, context)
            elif pubsub_message['MSG_TYPE'] == MSG_TYPE.NEW_MODEL_CONFIGURATION_FAILURE:
                pipeline_step_failure(event, context)
            elif pubsub_message['MSG_TYPE'] == MSG_TYPE.NEW_MODEL_GENERATION_SUCCESS:
                prepare_features(event, context)                
            elif pubsub_message['MSG_TYPE'] == MSG_TYPE.NEW_MODEL_GENERATION_FAILURE:
                pipeline_step_failure(event, context)
            elif pubsub_message['MSG_TYPE'] == MSG_TYPE.FEATURES_PREPARATION_SUCCESS:
                start_prediction(event, context)
            elif pubsub_message['MSG_TYPE'] == MSG_TYPE.FEATURES_PREPARATION_FAILURE:
                pipeline_step_failure(event, context)                
            elif pubsub_message['MSG_TYPE'] == MSG_TYPE.PREDICTION_FAILURE:
                pipeline_step_failure(event, context)
            else:
                logger.error(f"Unknown message type: {pubsub_message['MSG_TYPE']}")
                return False
    else:
        return False

def adaptive_pipeline_orchestration(event, context):            
    if route_pipeline(event, context):
        return "Successfully routed the pipeline"
    else:
        return "Failed to route the pipeline"    