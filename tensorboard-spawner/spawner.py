from flask import Flask
from flask import request
from flask import jsonify
from kubernetes import client, config
from kubernetes.client.rest import ApiException
import json
import yaml
from jinja2 import Template
import time


app = Flask(__name__)

config.load_incluster_config()
api_client = client.ApiClient()

custom_api = client.CustomObjectsApi(api_client)


def get_tensorboard_artifacts(wf):
    artifacts = []
    for name, node in wf["status"]["nodes"].items():
        if not "outputs" in node:
            continue
        afs = node["outputs"].get("artifacts")
        if not afs:
            continue
        for af in afs:
            if af["name"] != "tensorboard":
                continue
            artifacts.append(af)
    return artifacts


@app.route("/tb", methods=["GET"])
def workflow():
    group = "argoproj.io"
    version = "v1alpha1"
    plural = "workflows"
    namespace = "default"
    workflow = request.args["wf"]
    try:
        wf = custom_api.get_namespaced_custom_object(group, version, namespace, plural, workflow)
    except client.rest.ApiException as e:
        if e.status == 404:
            return "Workflow not found", 404
        raise
    tb_artifacts = get_tensorboard_artifacts(wf)
    logs = [a['s3']['key'] for a in tb_artifacts]

    with open('/app/tensorboard-spawner/tb-deployment.yaml') as f:
        tpl = Template(f.read())
        deploy = yaml.safe_load(
            tpl.render(workflow=workflow, logs=logs)
        )
    with open('/app/tensorboard-spawner/tb-service.yaml') as f:
        tpl = Template(f.read())
        svc = yaml.safe_load(
            tpl.render(workflow=workflow, logs=logs)
        )
    core_api = client.CoreV1Api()
    app_api = client.AppsV1Api()

    try:
        s = core_api.read_namespaced_service(namespace=namespace, name="tensorboard-{}".format(workflow))
    except ApiException as e:
        if e.status != 404:
            raise
    else:
        return jsonify(s.spec.ports[0].node_port)

    svc_resp = core_api.create_namespaced_service(namespace, svc)
    deploy_resp = app_api.create_namespaced_deployment(namespace, deploy)
    time.sleep(1)  # wait a second for nodeport to appear

    s = core_api.read_namespaced_service(namespace=namespace, name="tensorboard-{}".format(workflow))
    return jsonify(s.spec.ports[0].node_port)


if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True)