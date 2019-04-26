from pprint import pprint
import itertools
import json, yaml
from kubernetes import client, config, watch


group = "argoproj.io"
version = "v1alpha1"
plural = "hyperparamworkflows"


config.load_incluster_config()


namespace = 'default'
api_client = client.ApiClient()
custom_api = client.CustomObjectsApi(api_client)


watch = watch.Watch(return_type=object)


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



print("Starting loop")
for event in watch.stream(custom_api.list_namespaced_custom_object, group, version, namespace, plural):
    if event['type'] == 'ADDED':
        hparams = event['raw_object']['spec']['hyperparams']
        if event['raw_object']['spec']['algorithm'] == 'grid':
            experiments = grid_search(hparams)
            wf = generate_workflow(event['raw_object'], experiments)
            resp = custom_api.create_namespaced_custom_object(group, version, namespace, "workflows", wf, pretty=True)
            print(yaml.dump(wf))