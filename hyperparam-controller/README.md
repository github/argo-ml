# Argo Hyperparameter tuning

Hyperparameter tuning controller manages custom resource `HyperParamWorkflow`. This is wrapper resource around `Workflow` that unrolls defined hyperparam search space according to algorithm chosen and creates list of runs. List then will be passed to workflow as parameter and can be used, for example, with `with_items` clause.

You can list hyperparameter runs with

```
kubectl get hparam
```

## Structure of HyperparamWorkflow

Example hparam workflow

```
apiVersion: argoproj.io/v1alpha1
kind: HyperParamWorkflow
metadata:
  name: example-hparam-sweep
spec:
  hyperparams:
    # This setup will create 12 models - LR between 0.1 and 0.5 x 3 types of models
    learning-rate:
      range:  # Ranges will start from min and go to max with step
        min: 0.1
        max: 0.5
        step: 0.1
    model:
      values:  # Values will iterate over flat list
        - RandomForest
        - SVM
        - LogisticRegression
  algorithm: grid

  entrypoint: hparam-example
  templates:
  - name: hparam-example
    parallelism: 3  # This will allow only 3 nodes to run at same time, good for resource conservation
    steps:
    - - name: train
        template: train
        arguments:
          parameters:
          - {name: learning-rate, value: "{{item.learning-rate}}"}
          - {name: model, value: "{{item.model}}"}
        withParam: "{{workflow.parameters.hyperparams}}"

  - name: train
    inputs:
      parameters:
      - name: learning-rate
      - name: model
    container:
      image: docker/whalesay:latest
      command: [sh, -c]
      args: ["cowsay $LR"]
      resources:
        requests:
          nvidia.com/gpu: 1 # requesting 1 GPU
        limits:
          nvidia.com/gpu: 1
      env:
        - name: LR
          value: "{{inputs.parameters.learning-rate}}"
```

This looks like regular Argo workflow with few additional fields:

`hyperparams` - this field defines list of hyperparameters we want to optimize. There are two ways to specify parameter search space:

    * `values` - each value in list will be hyperparameter
    * `range` - hyperparameters will be all values between `min` and `max` with `step`

`algorithm` - Algorithm used for generating hyperparams, currently we only support `grid` which means every combination