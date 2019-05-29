package main

import (
	"crypto/tls"
	"crypto/x509"
	"io/ioutil"
	"log"
	"net/http"
	validation "github.com/argoproj/argo/workflow/validate/validate"
	wfv1 "github.com/argoproj/argo/pkg/apis/workflow/v1alpha1"
)

func main() {
	caCert, err := ioutil.ReadFile("client.crt")
	if err != nil {
		log.Fatal(err)
	}
	caCertPool := x509.NewCertPool()
	caCertPool.AppendCertsFromPEM(caCert)
	cfg := &tls.Config{
		ClientAuth: tls.RequireAndVerifyClientCert,
		ClientCAs:  caCertPool,
	}
	srv := &http.Server{
		Addr:      ":8443",
		Handler:   &handler{},
		TLSConfig: cfg,
	}
	log.Print("Starting the service...")
	log.Fatal(srv.ListenAndServeTLS("cert.pem", "key.pem"))
}

type handler struct{}

func (h *handler) ServeHTTP(w http.ResponseWriter, req *http.Request) {
	
	b, err := ioutil.ReadAll(r.Body)
	defer r.Body.Close()
	if err != nil {
		http.Error(w, err.Error(), 500)
		return
	}

	var wf
	getResource(b, &wf)

	// get a yaml string here

	// pass a yaml string here
	output := validate(yamlStr)

	w.Header().Set("Content-Type", "application/json")
  	w.Write(output)
}

// function to ping the hparam api
func getResource(jsonData, &wf) {
	jsonValue, _ := json.Marshal(jsonData)
	response, err := http.Post("analytics-exploration-ead20c6.private-us-east-1.github.net:5000/workflow", "application/json", bytes.NewBuffer(jsonValue))
    if err != nil {
        log.Printf("The HTTP request failed with error %s\n", err)
    } else {
        data, _ := ioutil.ReadAll(response.Body)
        log.Println(string(data))
	}
	return
}

// function to validate the results using argoproj validation code
func validate(yamlStr string) error {
	wf := unmarshalWf(yamlStr)
	return ValidateWorkflow(wf, {} Validation)
}

func unmarshalWf(yamlStr string) *wfv1.Workflow {
	var wf wfv1.Workflow
	err := yaml.Unmarshal([]byte(yamlStr), &wf)
	if err != nil {
		panic(err)
	}
	return &wf
}

