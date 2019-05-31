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
	sCert, _ := tls.LoadX509KeyPair("certificates/server-cert.pem", "certificates/server-key.pem")
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
	var hParamValidationError string
	var argoValidationError string
	allowed := true
	wf, err := getResource(b)

	if err != nil {
		log.Printf("Workflow error")
		allowed = false
		hParamValidationError = fmt.Sprintf("Error while generating workflow %s", err)
	}
	log.Printf("Workflow error2")

	err = validateWF(wf)

	if err != nil {
		argoValidationError = fmt.Sprintf("Workflow validation error %s", err)
		allowed = false
	}

	w.Header().Set("Content-Type", "application/json")
	reviewStatus := v1beta1.AdmissionResponse{}

	if allowed {
		reviewStatus.Allowed = true
	} else {
		reviewStatus.Allowed = false
		reviewStatus.Result = &metav1.Status{
			Message: hParamValidationError + argoValidationError,
		}

	}
	output, _ := json.Marshal(reviewStatus)
	log.Printf("%s", output)
	w.Write(output)
}

// function to ping the hparam api
func getResource(jsonData []byte) ([]byte, error) {
	validationRequest := &v1beta1.AdmissionReview{}
	err := json.Unmarshal(jsonData, validationRequest)
	if err != nil {
		log.Printf("Error processing validation request: %s\n", err)
		r := []byte("")
		return r, err
	}
	hparam, err := json.Marshal(validationRequest.Request.Object)
	if err != nil {
		log.Printf("Error processing validation request: %s\n", err)
		r := []byte("")
		return r, err
	}
	response, err := http.Post("http://analytics-exploration-ead20c6.private-us-east-1.github.net:5000/workflow", "application/json", bytes.NewBuffer(hparam))
	if err != nil {
		log.Printf("The HTTP request failed with error %s\n", err)
		r := []byte("")
		return r, err
	} else if response.StatusCode != 200 {
		resp, _ := ioutil.ReadAll(response.Body)
		err = errors.New(fmt.Sprintf("The HTTP request code is not 200: %s\n", resp))
		log.Printf("The HTTP request code is not 200: %s\n", resp)
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
