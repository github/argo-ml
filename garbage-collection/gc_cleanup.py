# argo garbage collection

import os
import argparse
import json, yaml
from datetime import datetime, tzinfo, timedelta
import logging


from kubernetes import client, config, watch
from kubernetes.client.rest import ApiException
from pprint import pprint


config.load_incluster_config()


api_client = client.ApiClient()
custom_api = client.CustomObjectsApi(api_client)
v1_api = client.CoreV1Api(api_client)


def get_pods(workflow,namespace):
    # check if pods exist in workflow and collect them
    nodes = list(workflow['status']['nodes'].keys())
    pods = []
    for node in nodes:
        try:
            api_response = v1_api.read_namespaced_pod_status(node, namespace)
            pods.append(node)
        except ApiException as e:
            # print("Exception when calling CoreV1Api->read_namespaced_pod: %s\n" % e)
            pass
    return pods


def delete_pods(pod,namespace,body):
    try:
        api_response = v1_api.delete_namespaced_pod(pod, namespace, body=body, propagation_policy='Background')
    except ApiException as e:
        print("Exception when calling CoreV1Api->delete_namespaced_pod: %s\n" % e)
    print("{} deleted".format(pod))
    return api_response

def clean_up(args):
    # body object for kubernetes api
    body = client.V1DeleteOptions()
    # get all workflows
    try:
        workflows = custom_api.list_namespaced_custom_object(args.group, args.version, args.namespace, args.plural)
    except ApiException as e:
        logging.info("Exception when calling CustomObjectsApi->list_namespaced_custom_object: %s\n" % e)

    # track workflows expired, workflows not expired and pods deleted for logging
    workflows_expired = []
    workflows_not_expired = []
    pods_deleted = []
    for workflow in workflows['items']:
        key = workflow['metadata']['name']

        try:
            finished_at = datetime.strptime(workflow['status']['finishedAt'], '%Y-%m-%dT%H:%M:%SZ')
        except TypeError:
            logging.info('could not read workflow {}'.format(key))
        time_since_completion = (datetime.utcnow() - finished_at).total_seconds()/60/60
        # Get specific metadata based on workflow type
        if args.adhoc:
            exists = False
            for word in args.starts_with + args.label_selector:
                if key.startswith(word):
                    #skip
                    exists = True
                elif word in workflow['metadata']['labels']:
                    #skip
                    exists = True
            if not exists and int(time_since_completion) > int(args.max_age_hrs):
                workflows_expired.append(key)
                # print("deleting workflow pod {} that completed {} hrs ago".format(key,time_since_completion))
                pods = get_pods(workflow,args.namespace)
                for pod in pods:
                    if not args.dry_run:
                        delete_pods(pod,args.namespace,body)
                    else:
                        logging.info("dry_run flag set, would have deleted {}".format(pod))
            else:
                workflows_not_expired.append(key)
        else:
            exists = False
            for word in args.starts_with + args.label_selector:
                if key.startswith(word):
                    #skip
                    exists = True
                elif word in workflow['metadata']['labels']:
                    #skip
                    exists = True
            if exists and int(time_since_completion) > int(args.max_age_hrs):
                workflows_expired.append(key)
                # print("deleting workflow pod {} that completed {} hrs ago".format(key,time_since_completion))
                pods = get_pods(workflow, args.namespace)
                for pod in pods:
                    if not args.dry_run:
                        delete_pods(pod,args.namespace,body)
                    else:
                        logging.info("dry_run flag set, would have deleted {}".format(pod))
            else:
                workflows_not_expired.append(key)
    logging.info("expired workflows: {}".format(workflows_expired))


def main():
  logging.basicConfig(level=logging.INFO)
  logging.getLogger().setLevel(logging.INFO)

# initiate the parser
parser = argparse.ArgumentParser(description = 'a garbage collection utility for cleaning up argo workflows')

# add in a namespace argument
parser.add_argument("-n", "--namespace", default="default", type=str, help=("The custom resource's namespace."))

# add in a group argument
parser.add_argument("-grp", "--group", default="argoproj.io", type=str, help=("The custom resource's group name."))

# add in a version argument
parser.add_argument("-version", default="v1alpha1", type=str, help=("The custom resource's version."))

# add in a plurals argument
parser.add_argument("-p", "--plural", default="workflows", type=str, help=("The custom resource's plural name to filter by."))

# add in a plurals argument
parser.add_argument("--starts_with", nargs='+', type=str, help=("A list of specific names filtering for workflows that start with"))

# add in a plurals argument
parser.add_argument("--label_selector", nargs='+', type=str, help=("A list of labels to filter by."))

# adhoc flag for handling all adhoc workflows
parser.add_argument("--adhoc", action='store_true', help=("This flag will cause the workflows filtered by the label_selector and starts_with to be ignored if set"))

# add in a default min date argument
parser.add_argument("--max_age_hrs", default=168, type=int, help=("enter the maximum age to keep workflows for in hours"))

parser.add_argument("--dry_run", action='store_true', help=("Triggers a dry run delete"))

args = parser.parse_args()
logging.info(args)
clean_up(args)

if __name__ == "__main__":
    main()
