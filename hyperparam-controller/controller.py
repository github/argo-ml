from pprint import pprint
import itertools
import json, yaml
from kubernetes import client, config
from kubernetes import watch as kwatch
from kubernetes.config.config_exception import ConfigException
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

try:
    config.load_incluster_config()
except ConfigException:
    logger.debug("loading local kube config")
    config.load_kube_config()

def generate_param_combinations(params):
    keys, values = zip(*params.items())
    experiments = [dict(zip(keys, v)) for v in itertools.product(*values)]
    return experiments


def unroll_hparams(hparams):
    parameters = {}

    for param in hparams:
        parameters[param] = []
        if 'range' in hparams[param]:
            rang = hparams[param]['range']
            i = rang['min']
            while abs(i) <= abs(rang['max']):
                parameters[param].append(i)
                i += rang['step']
        if 'values' in hparams[param]:
            parameters[param].extend(hparams[param]['values'])

    return parameters


def grid_search(hparams):
    unrolled = unroll_hparams(hparams)
    return generate_param_combinations(unrolled)


def generate_workflow(wf, experiments):
    wf['kind'] = "Workflow"
    del wf['spec']['algorithm']
    del wf['spec']['hyperparams']

    for i in ['selfLink', 'uid', 'creationTimestamp', 'generation', 'resourceVersion']:
        if i in wf['metadata']:
            del wf['metadata'][i]

    wf['spec']['arguments'] = wf['spec'].get('arguments', {})
    wf['spec']['arguments']['parameters'] = wf['spec']['arguments'].get('parameters', [])

    wf['spec']['arguments']['parameters'].append(
        {
            'name': 'hyperparams',
            'value': json.dumps(experiments)
        }
    )
    pprint(wf['metadata'])
    return wf

def main():
    group = "argoproj.io"
    version = "v1alpha1"
    plural = "hyperparamworkflows"


    namespace = 'default'
    api_client = client.ApiClient()
    custom_api = client.CustomObjectsApi(api_client)


    watch = kwatch.Watch(return_type=object)

    logger.info("Starting loop")
    for event in watch.stream(custom_api.list_cluster_custom_object, group, version, plural):
        logger.debug(event)
        if event['type'] == 'ADDED':
            namespace = event['metadata']['namespace']
            hparams = event['raw_object']['spec']['hyperparams']
            if event['raw_object']['spec']['algorithm'] == 'grid':
                experiments = grid_search(hparams)
                wf = generate_workflow(event['raw_object'], experiments)
                try:
                    resp = custom_api.create_namespaced_custom_object(group, version, namespace, "workflows", wf, pretty=True)
                except client.rest.ApiException:
                    continue
                logger.info(yaml.dump(wf))
        if event['type'] == 'DELETED':
            namespace = event['metadata']['namespace']
            # TODO: This would be better managed with resource owners
            name = event['raw_object']['metadata']['name']
            custom_api.delete_namespaced_custom_object(group, version, namespace, "workflows", name=name, body=client.V1DeleteOptions())


if __name__ == "__main__":
    main()