# Generating certificates

## Prepare csr.conf

Important - change namespace and name of services

## Generate certificates

```
openssl genrsa -out server-key.pem 2048
openssl req -new -key server-key.pem -subj "/CN=argo-validation-controller.argo.svc.cluster.local" -out server.csr -config csr.conf
```

## Prepare CertificateSigningRequest

```
CSR=$(cat server.csr | base64 | tr -d '\n')
```

```
cat <<EOF | kubectl apply -f -
apiVersion: certificates.k8s.io/v1beta1
kind: CertificateSigningRequest
metadata:
  name: argo-validation-controller
spec:
  groups:
  - system:authenticated
  request: $CSR
  usages:
  - digital signature
  - key encipherment
  - server auth
EOF
```
or in a separate file with:
```
kubectl create -f << csr file >>
```

## Approve CSR

```
kubectl certificate approve argo-validation-controller
```

Get your approved certificate

```
serverCert=$(kubectl get csr argo-validation-controller -o jsonpath='{.status.certificate}')
```

Create file with approved cert

```
echo ${serverCert} | openssl base64 -d -A -out ${tmpdir}/server-cert.pem
```

## Prepare manifest.yaml

You need Kubernetes CA certificate for it

```
CA_BUNDLE=$(kubectl get configmap -n kube-system extension-apiserver-authentication -o=jsonpath='{.data.client-ca-file}' | base64 | tr -d '\n')
```

Paste contents of `$CA_BUNDLE` to manifest.yaml

```
kind: ValidatingWebhookConfiguration
metadata:
  name: scheduling-admission
webhooks:
  - name: argo-validation-controller.argo
    rules:
      - apiGroups:
          - "argoproj.io"
        apiVersions:
          - v1alpha1
        operations:
          - CREATE
        resources:
          - hyperparamworkflows
    failurePolicy: Ignore
    clientConfig:
      service:
        name: argo-validation-controller
        namespace: argo
        path: "/"
      caBundle: ${CA_BUNDLE}
```

## set up secrets

`kubectl -n argo create secret generic argo-validation-certs --from-file="server-cert.pem" --from-file="server-key.pem"`
