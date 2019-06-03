package main

import (
	"bytes"
	"crypto/tls"
	"encoding/json"
	"errors"
	"fmt"
	"io/ioutil"
	"log"
	"net/http"

	wfv1 "github.com/argoproj/argo/pkg/apis/workflow/v1alpha1"
	"github.com/argoproj/argo/workflow/validate"
	"k8s.io/api/admission/v1beta1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

func main() {
	sCert, _ := tls.LoadX509KeyPair("/certificates/server-cert.pem", "/certificates/server-key.pem")
	srv := &http.Server{
		Addr:    ":12345",
		Handler: &handler{},
	}
	srv.TLSConfig = &tls.Config{
		Certificates: []tls.Certificate{sCert},
	}
	log.Print("Starting the service...")
	log.Fatal(srv.ListenAndServeTLS("", ""))
}

type handler struct{}

func (h *handler) ServeHTTP(w http.ResponseWriter, req *http.Request) {

	b, err := ioutil.ReadAll(req.Body)
	defer req.Body.Close()
	if err != nil {
		http.Error(w, err.Error(), 500)
		return
	}
	
	validationError, allowed := handleAdmission(b)

	w.Header().Set("Content-Type", "application/json")
	reviewStatus := v1beta1.AdmissionResponse{}

	if allowed {
		reviewStatus.Allowed = true
	} else {
		reviewStatus.Allowed = false
		reviewStatus.Result = &metav1.Status{
			Message: fmt.Sprintf("%s", validationError),
		}

	}
	validationRequest := &v1beta1.AdmissionReview{}
	_ = json.Unmarshal(b, validationRequest)
	validationRequest.Response = &reviewStatus
	output, _ := json.Marshal(validationRequest)
	w.Write(output)
}

func handleAdmission(b []byte) (string, bool) {
	validationRequest := &v1beta1.AdmissionReview{}
	err := json.Unmarshal(b, validationRequest)
	if err != nil {
		return fmt.Sprintf("Error while unmarshalling AdmissionReview: %s", err), false
	}
	wf, err := getResource(validationRequest)

	if err != nil {
		return fmt.Sprintf("Error while generating workflow: %s", err), false
	}

	err = validateWF(wf)

	if err != nil {
		return fmt.Sprintf("Validation error: %s", err), false
	}
	return "", true
}

// function to ping the hparam api
func getResource(validationRequest *v1beta1.AdmissionReview) ([]byte, error) {
	hparam, err := json.Marshal(validationRequest.Request.Object)
	if err != nil {
		log.Printf("Error processing validation request: %s\n", err)
		r := []byte("")
		return r, err
	}
	response, err := http.Post("http://analytics-exploration-ead20c6.private-us-east-1.github.net:5000/workflow", "application/json", bytes.NewBuffer(hparam))
	if err != nil {
		r := []byte("")
		return r, err
	} else if response.StatusCode != 200 {
		resp, _ := ioutil.ReadAll(response.Body)
		err = errors.New(fmt.Sprintf("The HTTP request code is not 200: %s\n", resp))
		r := []byte("")
		return r, err
	} else {
		data, _ := ioutil.ReadAll(response.Body)
		return data, nil
	}
}

// function to validate the results using argoproj validation code
func validateWF(jsonStr []byte) error {
	wf := &wfv1.Workflow{}
	err := json.Unmarshal(jsonStr, wf)
	if err != nil {
		return err
	}
	return validate.ValidateWorkflow(wf, validate.ValidateOpts{})
}
