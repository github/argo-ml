import json
from flask import Flask, request, jsonify, Response


app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def mutate_pod():
    res = {
        "response": {
            "allowed": False,
            "status": {
                "status": "Failure",
                "message": "Test failure",
                "reason": "Test failure",
                "code": 402
            }
        }
    }
    return jsonify(res)



if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=12345, ssl_context=('cert.pem', 'key.pem'))