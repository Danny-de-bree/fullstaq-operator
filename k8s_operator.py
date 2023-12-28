import kopf
from kubernetes import client, config, watch
from config import Config
import requests
from kubernetes.client import CoreV1Api
from kubernetes.client.models.v1_pod import V1Pod
from kubernetes.client.models.v1_container_status import V1ContainerStatus

# Set up logging
logger = Config.setup_logging()

cluster = Config.cluster()

def kubeconfig() -> client.CoreV1Api:
    """This is for using the kubeconfig to auth with the k8s api
    with the first try it will try to use the in-cluster config (so for in cluster use)
    If it cannot find an incluster because it is running locally, it will use your local config"""
    try:
        # Try to load the in-cluster configuration
        config.load_incluster_config()
        logger.info("Loaded in-cluster configuration.")
    except config.ConfigException:
        # If that fails, fall back to kubeconfig file
        config.load_kube_config(context=cluster)
        logger.info(f"Loaded kubeconfig file with context {cluster}.")

        # Check the active context
        _, active_context = config.list_kube_config_contexts()
        if active_context:
            logger.info(f"The active context is {active_context['name']}.")
        else:
            logger.info("No active context.")

    # Now you can use the client
    api = client.CoreV1Api()
    return api

def watch_namespace_pods(v1: CoreV1Api, namespace: str) -> None:
    """Watch pods in a specified namespace"""
    logger.info(f"Watching namespace {namespace} on cluster {v1.api_client.configuration.host}")
    w = watch.Watch()
    for event in w.stream(v1.list_namespaced_pod, namespace=namespace, timeout_seconds=10):
        process_pod_event(event)


def watch_labeled_pods(v1: CoreV1Api, label_selector: str) -> None:
    """Watch pods with a specific label across all namespaces"""
    logger.info(f"Watching all pods on cluster {v1.api_client.configuration.host} with label {label_selector}")
    w = watch.Watch()
    for event in w.stream(v1.list_pod_for_all_namespaces, label_selector=label_selector, timeout_seconds=10):
        process_pod_event(event)


def watch_all_pods(v1: CoreV1Api) -> None:
    """Watch all pods in all namespaces"""
    logger.info(f"Watching all pods on cluster {v1.api_client.configuration.host}")
    w = watch.Watch()
    for event in w.stream(v1.list_pod_for_all_namespaces, timeout_seconds=10):
        process_pod_event(event)


def process_pod_event(event: dict) -> None:
    """Process pod events and take necessary actions"""
    if event['type'] not in ('ADDED', 'MODIFIED'):
        return

    pod = event['object']
    logger.info(f"Event: {event['type']} {pod.kind} {pod.metadata.name} {pod.status.phase}")

    if pod.status.phase in ("Failed", "Unknown"):
        handle_failed_pod(pod)

    for container_status in pod.status.container_statuses:
        if container_status.state.waiting:
            handle_failed_container(container_status, pod)

def handle_failed_pod(pod: V1Pod) -> None:
    """Handle pods in a failed state"""
    logger.info("Pod is not running")
    logger.info("Sending webhook to teams")
    data = {"text": f"Hello! The {pod.kind} {pod.metadata.name} is in the {pod.status.phase} phase. But remember Feyenoord 1#"}
    requests.post(Config.teams_url, json=data)

def handle_failed_container(container_status: V1ContainerStatus, pod: V1Pod) -> None:
    """Handle containers in a waiting state"""
    error_states = ["ImagePullBackOff", "ErrImagePull", "CrashLoopBackOff"]
    if container_status.state.waiting.reason in error_states:
        logger.info(f"Container {container_status.name} is in a faulty state")
        logger.info("Sending webhook to teams")
        data = {"text": f"Hello! The container {container_status.name} in {pod.kind} {pod.metadata.name} is in the {container_status.state.waiting.reason} state. But remember Feyenoord 1#"}
        requests.post(Config.teams_url, json=data)

def watch_pods_by_config(v1: CoreV1Api) -> None:
    """Watch pods based on configuration"""
    if Config.namespace:
        watch_namespace_pods(v1, Config.namespace)
    elif Config.label:
        watch_labeled_pods(v1, Config.label)
    else:
        watch_all_pods(v1)

@kopf.on.startup()
def on_startup(**kwargs):
    """On startup, watch pods"""
    logger.info("Starting up")
    v1 = kubeconfig()
    watch_pods_by_config(v1)
    
@kopf.on.timer('pods',interval=Config.interval)
def on_timer(**kwargs):
    """On timer, watch pods"""
    logger.info("Starting up")
    v1 = kubeconfig()
    watch_pods_by_config(v1)
    
def main():
    kopf.run()
    
if __name__ == '__main__':
    main()