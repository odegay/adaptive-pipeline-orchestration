import base64
import json
import datetime
from kubernetes import client, config
from google.cloud import container_v1
from adpipsvcfuncs import fetch_gcp_project_id, get_pipeline_id
import logging
import google.auth
from google.auth.transport.requests import Request

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

# Function to trigger model training kubernetes job - Python script wrapped in a docker container
def trigger_model_training(event: dict, context: dict) -> bool:
    try:
        cluster_name = "adaptive-pipeline-model-training-cluster"
        project_id = fetch_gcp_project_id()
        zone = "us-central1-a"    
        image_name = "model-training-job:latest"
        pipeline_id = get_pipeline_id(event)
        if pipeline_id == "":
            return False
        job_name = "model-training-job-" + pipeline_id + "-" + datetime.now().strftime("%Y%m%d%H%M%S")
        image = f"gcr.io/{project_id}/{image_name}"
        job_manifest = get_gke_job_manifest(job_name, image, pipeline_id)
            
        
        credentials, project = google.auth.default()
        container_client = container_v1.ClusterManagerClient(credentials=credentials)
        cluster = container_client.get_cluster(project_id=project_id, zone=zone, cluster_id=cluster_name)   

        # Get the Kubernetes API client
        kubernetes_client = get_kubernetes_client(cluster)
        
        # Create the job
        api_response = kubernetes_client.create_namespaced_job(
            body=job_manifest,
            namespace='default'
        )
        print(f"Job created. Status='{api_response.status}'")
        return True
    except Exception as e:
        logger.error(f"Error triggering model training job: {e}")
        return False


def get_kubernetes_client(cluster):
    
    try:
        # Get credentials for the cluster
        credentials, project = google.auth.default()
        credentials.refresh(Request())
        
        # Load kubeconfig from the cluster
        config.load_kube_config_from_dict({
            "apiVersion": "v1",
            "clusters": [{
                "cluster": {
                    "certificate-authority-data": cluster.master_auth.cluster_ca_certificate,
                    "server": f"https://{cluster.endpoint}"
                },
                "name": "kubernetes-cluster"
            }],
            "contexts": [{
                "context": {
                    "cluster": "kubernetes-cluster",
                    "user": "gke-user"
                },
                "name": "kubernetes-context"
            }],
            "current-context": "kubernetes-context",
            "kind": "Config",
            "preferences": {},
            "users": [{
                "name": "gke-user",
                "user": {
                    "auth-provider": {
                        "config": {
                            "access-token": credentials.token,
                            "cmd-args": "config config-helper --format=json",
                            "cmd-path": "gcloud",
                            "expiry-key": "{.credential.token_expiry}",
                            "token-key": "{.credential.access_token}"
                        },
                        "name": "gcp"
                    }
                }
            }]
        })
        
        # Return Kubernetes API client
        return client.BatchV1Api()
    except Exception as e:
        logger.error(f"Error getting Kubernetes client: {e}")
        return None

def get_gke_job_manifest(job_name: str, image: str, pipeline_id: str) -> dict:
    job_manifest = {
        "apiVersion": "batch/v1",
        "kind": "Job",
        "metadata": {
            "name": job_name
        },
        "spec": {
            "backoffLimit": 3,  # Add backoffLimit parameter
            "template": {
                "spec": {
                    "containers": [
                        {
                            "name": "model-training-job",
                            "image": image,
                            "env": [
                                {
                                    "name": "PIPELINE_ID",
                                    "value": pipeline_id
                                }
                            ]
                        }
                    ],
                    "restartPolicy": "Never"
                }
            }
        }
    }
    return job_manifest