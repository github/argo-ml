package main

import (
	"bytes"
	"crypto/tls"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"log"
	"net/http"

	"k8s.io/api/admission/v1beta1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"

	// validation "github.com/argoproj/argo/workflow/validate"
	wfv1 "github.com/argoproj/argo/pkg/apis/workflow/v1alpha1"
	"github.com/kelseyhightower/envconfig"
)

// Config for replicating bash script
type Config struct {
	ListenOn string `default:"0.0.0.0:8443"`
	TlSCert  string `default:"/etc/webhook/certs/cert.pem"`
	TlSKey   string `default:"/etc/webhook/certs/key.pem"`
}

func getValidatorNoSSL(ListenOn string) *http.Server {
	server := &http.Server{
		Addr:    ListenOn,
		Handler: &handler{},
	}

	return server
}

func main() {
	config := &Config{}
	envconfig.Process("", config)

	sCert, err := tls.LoadX509KeyPair(config.TlSCert, config.TlSKey)
	server := getValidatorNoSSL(config.ListenOn)
	server.TLSConfig = &tls.Config{
		Certificates: []tls.Certificate{sCert},
	}
	if err != nil {
		log.Printf("server failed to start due to %s\n", (err))
	}
	server.ListenAndServeTLS("", "")
}

type handler struct{}

func (h *handler) ServeHTTP(w http.ResponseWriter, req *http.Request) {

	b, err := ioutil.ReadAll(req.Body)
	defer req.Body.Close()
	if err != nil {
		http.Error(w, err.Error(), 500)
		return
	}
	var allowed bool
	var validationError string

	wf, err := getResource(b)
	if err != nil {
		allowed = false
		validationError = fmt.Sprintf("Error while generating workflow %s", err)
	}
	fmt.Sprintf("workflow %s", wf)

	// get a json string here

	// pass a json string here
	if err != nil {
		validationError = fmt.Sprintf("Validation error %s", err)
		allowed = false
	}

	w.Header().Set("Content-Type", "application/json")
	reviewStatus := v1beta1.AdmissionResponse{}

	if allowed {
		reviewStatus.Allowed = true
	} else {
		reviewStatus.Allowed = false
		reviewStatus.Result = &metav1.Status{
			Message: validationError,
		}

	}
	output, _ := json.Marshal(reviewStatus)
	w.Write(output)
}

// function to ping the hparam api
func getResource(jsonData []byte) ([]byte, error) {
	jsonValue, _ := json.Marshal(jsonData)
	response, err := http.Post("analytics-exploration-ead20c6.private-us-east-1.github.net:5000/workflow", "application/json", bytes.NewBuffer(jsonValue))
	if err != nil {
		log.Printf("The HTTP request failed with error %s\n", err)
		r := []byte("")
		return r, err
	} else {
		data, _ := ioutil.ReadAll(response.Body)
		return data, nil
	}
}

// function to validate the results using argoproj validation code
func validate(jsonStr string) *wfv1.Workflow {
	wf := unmarshalWf(jsonStr)
	return wf
}

func unmarshalWf(jsonStr string) *wfv1.Workflow {
	var wf wfv1.Workflow
	err := json.Unmarshal([]byte(jsonStr), &wf)
	if err != nil {
		panic(err)
	}
	return &wf
}
