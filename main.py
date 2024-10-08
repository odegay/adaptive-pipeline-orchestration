import base64
import json
from adpipsvcfuncs import publish_to_pubsub
from adpipwfwconst import MSG_TYPE
from adpipwfwconst import PIPELINE_TOPICS as TOPICS
#from adpipwfwconst import MODEL_TRAINING_JOB_IMAGE_NAME
from next_pipeline_cycle import next_pipeline_cycle
import logging

root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)  # Capture DEBUG, INFO, WARNING, ERROR, CRITICAL
if not root_logger.handlers:
    # Create console handler and set its log level to DEBUG
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    # Create formatter and add it to the handler
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    # Add the handler to the root logger
    root_logger.addHandler(ch)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Capture DEBUG, INFO, WARNING, ERROR, CRITICAL

# Function to handle new model configuration
def model_generation(event: dict, context: dict) -> bool:
    #TODO: Implement the logic for new model generation
    pipeline_id = get_pipeline_id(event)
    if pipeline_id == "":
        return False
        
    message_data = {
        "pipeline_id": pipeline_id,
        "status": MSG_TYPE.REQUEST_LLM_NEW_MODEL_CONFIGURATION.value      
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
        # Log the entire message and its type
        logger.debug(f"Decoded Pub/Sub message: {pubsub_message}")
        logger.debug(f"Type of MSG_TYPE in message: {type(pubsub_message['status'])}")

        if 'status' in pubsub_message:
            logger.debug(f"Type of MSG_TYPE.ADAPTIVE_PIPELINE_START.value: {type(MSG_TYPE.ADAPTIVE_PIPELINE_START.value)}")

            if ((pubsub_message['status'] == MSG_TYPE.ADAPTIVE_PIPELINE_START.value) or (pubsub_message['status'] == MSG_TYPE.PREDICTION_SUCCESS.value)):
                next_pipeline_cycle(event, context)
            elif pubsub_message['status'] == MSG_TYPE.NEW_MODEL_CONFIGURATION_SUCCESS.value:
                #model_generation(event, context)
                logger.debug(f"Skipping message type: {pubsub_message['status']} as it will be handled by the ADAPTIVE-PIPELINE-MODEL function")
            elif pubsub_message['status'] == MSG_TYPE.NEW_MODEL_CONFIGURATION_FAILURE.value:
                pipeline_step_failure(event, context)
            elif pubsub_message['status'] == MSG_TYPE.NEW_MODEL_GENERATION_SUCCESS.value:
                prepare_features(event, context)                
            elif pubsub_message['status'] == MSG_TYPE.NEW_MODEL_GENERATION_FAILURE.value:
                pipeline_step_failure(event, context)
            elif pubsub_message['status'] == MSG_TYPE.FEATURES_PREPARATION_SUCCESS.value:
                start_prediction(event, context)
            elif pubsub_message['status'] == MSG_TYPE.FEATURES_PREPARATION_FAILURE.value:
                pipeline_step_failure(event, context)                
            elif pubsub_message['status'] == MSG_TYPE.PREDICTION_FAILURE.value:
                pipeline_step_failure(event, context)
            else:
                logger.error(f"Unknown message type: {pubsub_message['status']}")
                return False
    else:
        return False

def adaptive_pipeline_orchestration(event, context):            
    if route_pipeline(event, context):
        return "Successfully routed the pipeline"
    else:
        return "Failed to route the pipeline"    