# Scheduling rules admission controller

This admission controller is meant to modify scheduling rules for Pods. Main role is to ensure that Pods are spread across cluster rather than fill single node.

Prepare cert bundle
```
openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365
```

Fill `caCert` field in scheduling-admission-controlle.yaml with outputs of

```
cat cert.pem | base64
```