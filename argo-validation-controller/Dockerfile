FROM golang:1.11.5

RUN mkdir -p /go/src/github.com/github/argo-ml
COPY . /go/src/github.com/github/argo-ml
RUN go get github.com/github/argo-ml
RUN go build src/github.com/github/argo-ml/argo-validation-controller.go

CMD ["./argo-validation-controller"]
