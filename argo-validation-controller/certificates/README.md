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
```

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
  - name: analytics-exploration-ead20c6.private-us-east-1.github.net
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
      url: "https://analytics-exploration-ead20c6.private-us-east-1.github.net:12345"
      caBundle: LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0tCk1JSUN5RENDQWJDZ0F3SUJBZ0lCQURBTkJna3Foa2lHOXcwQkFRc0ZBREFWTVJNd0VRWURWUVFERXdwcmRXSmwKY201bGRHVnpNQjRYRFRFNU1ERXpNREUwTXpFek5Wb1hEVEk1TURFeU56RTBNekV6TlZvd0ZURVRNQkVHQTFVRQpBeE1LYTNWaVpYSnVaWFJsY3pDQ0FTSXdEUVlKS29aSWh2Y05BUUVCQlFBRGdnRVBBRENDQVFvQ2dnRUJBT0NqCi9Nd2s2ZkJzTk15VG82SWhoT1lJcENHT0swV3dmMXB5STc2MmdFbUoyUDFjcDU1S3liQ0E1OGQ4ZjBtay9PS0kKS3lHMEVxejhQd1VDUXZGc3NFeFowaFdoUjlEZ1cyc3hJeXk1a2tlSkRqOE13U1lhR0I0eGYxU3p0Z2UvdVpkMAorb3JvUWhIdEJuOWMrU3ByeW9yNW8zeHRWMDFnVS9VbFFnckVZYmxKcUxCUjdvSVU0b0gyOEJXb3ZQS01RM2FpCkcyOU5iTTNySW9TNmxCejFwRUc4TmNSbyt5ZVBuOEVZdHdNL1FFaS9oc3FBRVo3YTlSYzFhYVEzY243ci82K3gKM1BWUjBNZCt6UHc0SzZndis4WGpEU3luUm43R1ZQSDNwQWJUMkVqYUhzVnNRSis4YXJyRUgvRmtXYmFJOWhudAp0RGdjMWVRbDh2S2RaS0I4Q1dFQ0F3RUFBYU1qTUNFd0RnWURWUjBQQVFIL0JBUURBZ0trTUE4R0ExVWRFd0VCCi93UUZNQU1CQWY4d0RRWUpLb1pJaHZjTkFRRUxCUUFEZ2dFQkFHUWFWeE1JWkVmMlJHNXBaVjBNSjZob2IrNHAKNEJyR2hwbUhZbmdUWkUzSmRjZjVIaTgrV2Q2TFZHSjUxU1VuSTlSbklLcmJ6TjNIZjlSQVcrL1BwcEp0VEkxMQpvd2U4bzM2SkJQSmZDcDhLQllEdDVBWVdQTnhqL01td0IyZ0xGZnc3WjR3UjFoeTAyNGo0bmQwSkg0SU91TUcxCklDVlVqTXhuVTE3dmtkR0p5QnBPdjJYNnZQWnpSeURBS3k4aHJHM1E2OUt4TjdVK2J5akhuYWZCQWhubmplSkQKQUxqREJTUjF2S3hEcmFjQnhHOS9FaGZOZlRjZ3VXYUd2eFFUK0QyNjV2YUVOaFRQeEJDQnlicnhaK3BmcGVPRAo0d0Q2TlBXdFBVRWZzaHM5aXRITTFJNUNNdHU0cE85TEhmRTJpanI3OFlnRUZMazhBS0VidXhtVVVjdz0KLS0tLS1FTkQgQ0VSVElGSUNBVEUtLS0tLQo=
```