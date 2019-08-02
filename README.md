# Argo-ML

Controllers, wrappers and miscellaneous utils to make it easier for Argo to be used in ML scenarios. There are 3 major architectures in the repo.

## Controller

Controller, also known as operator, manages Kubernetes [Custom Resources](https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/custom-resources/), or CRs. Our controllers, written in Python, are built around main loop through Kubernetes events. Event will be emitted every time resource is added, updated or deleted.
Kubernetes Python client allows to watch for these events, therefore providing great way to write management code for regular or custom resources.

Example loop will look like that:

```
group = "mycustomapi"
version = "v1"
plural = "mycustomresource"

for event in watch.stream(custom_api.list_namespaced_custom_object, group, version, namespace, plural):
    if event['type'] == 'ADDED':
        do_something_when_resource_is_created(event['object'])
```


## Admission Controller

Although it's also called controller, it's not following pattern above. [Admission Controllers](https://kubernetes.io/docs/reference/access-authn-authz/admission-controllers/) are API endpoints that are triggered when user (or system) attempts to create particular resource. There are two types of admission controllers:

* Validating admission controller is great place to include resource validation. Whenever resource is created, Kube API will call this endpoint and expect either validation success message or error, throwing it back to user
* Mutating admission controller is allows us to add custom logic to modify any resource on creation. For example, we could add common secret to every Pod

## APIs

Just regular REST APIs


# Components

## Argo hyperparam workflow

This is controller that takes `HyperparamWorkflow` custom resource - resource similar to original Argo `Workflow`, adds new fields that defines hyperparameter search space. Controller then generates `Workflow` for with list of all hyperparam combinations as parameters.

## Argo validation controller

Argo workflows have specific syntax. You can validate it if you create `Workflow` with `argo` cli tool, but that won't be the case for our custom wrapper resources. Argo validation controller allows us to validate workflow syntax in these.

## Tensorboard spawner

Small API that takes workflow name as input, lists artifacts names `tensorboard` and spawns Tensorboard instance for them.

## Garbage collector

Small utility tool to delete old pods produced by workflows.
