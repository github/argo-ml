import os
import json
from kubernetes import client, config, watch
import requests
from requests.auth import HTTPBasicAuth


group = "argoproj.io"
version = "v1alpha1"
plural = "workflows"


# config.load_incluster_config()

# local dev kube config
config.load_kube_config()


namespace = 'default'
api_client = client.ApiClient()
custom_api = client.CustomObjectsApi(api_client)
token = os.getenv("CHAT_TOKEN","X")
webhook_url = os.getenv("WEBHOOK_URL","http://localhost/")
default_channel = os.getenv("DEFAULT_CHANNEL",None)
argo_ui_url = os.getenv("ARGO_UI_URL","http://localhost/")
webhooks_enabled = os.getenv("WEBHOOKS_ENABLED",False)


watch = watch.Watch(return_type=object)


def notify_slack(message, channel):
    print(channel)
    if webhooks_enabled:
        print("Printing message to slack via webhooks")
        print(message)
        requests.post(webhook_url,
                json={"text": message})
    else:
        print(f"Printing message to channel{channel}")
        print(message)
        requests.post("{}{}".format(webhook_url,channel),
                json=message,
                auth=HTTPBasicAuth(token, ''))


def notify(message, workflow, notifs):
    message += "You can see workflow here {}/workflows/default/{}".format(argo_ui_url,workflow['metadata']['name'])
    users_to_notify = notifs.get("users", [])
    if users_to_notify:
        message += " CC:"
        for u in users_to_notify:
            message += " @" + u
    channel_to_notify = notifs.get("channel", default_channel)
    notify_slack(message, channel=channel_to_notify)


def notify_fail(workflow, notifs):
    message = "Workflow failed. :sad_panda: "
    notify(message, workflow, notifs)


def notify_success(workflow, notifs):
    message = "Workflow succeeded! :angel-parrot: "
    notify(message, workflow, notifs)


print("Starting watching for cronworkflow executions")
for event in watch.stream(custom_api.list_namespaced_custom_object, group, version, namespace, plural):
    if event["type"] == 'MODIFIED':
        notifs = event["raw_object"]["metadata"].get("annotations", {}).get("notify")
        print(notifs)
        if not notifs:
            continue
        notifs = json.loads(notifs)
        notify_phases = notifs.get("phases", [])
        if event["raw_object"]["status"]["phase"] == "Failed" and "Failed" in notify_phases:
            notify_fail(event["raw_object"], notifs)
        if event["raw_object"]["status"]["phase"] == "Succeeded" and "Succeeded" in notify_phases:
            notify_success(event["raw_object"], notifs)
