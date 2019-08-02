# Argo validation controller

This is only (so far) GoLang application in this repo. Reason for it breaking out of Python standard is being able to reuse Argo's own validation code. Currently this service validates `HyperparamWorkflow`, but goal is to extend it to every `Workflow` wrapper CRD we maintain.

This service provides HTTPS API that follows validation admission controller requirements in K8s. Kubernetes, after adding `ValidationWebhookConfiguration` (defined in `argo-validation-deployment.yaml`) will call this API and expect `AdmissionReview` serialized object in return. This review will either allow resource to be created or deny it and pass error to user.

## Deployment

This service requires HTTPS, so it requires certificates. K8s allows to sign TLS certs using internal CA, you can find full instruction for it in [certificate README](https://github.com/github/argo-ml/blob/master/argo-validation-controller/certificates/README.md).

After certificates are created and saved as `Secret`, build and push image from `Dockerfile` and run `kubectl apply -f argo-validation-deployment.yaml` to deploy service and configure Kubernetes to call it.