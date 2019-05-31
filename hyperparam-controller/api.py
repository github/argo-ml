from flask import Flask, request, jsonify
from pprint import pprint
from controller import grid_search, generate_workflow


app = Flask(__name__)


@app.route("/workflow", methods=["POST"])
def workflow():
    hyperparam = request.json
    pprint(hyperparam)
    if hyperparam['spec']['algorithm'] == 'grid':
        experiments = grid_search(hyperparam['spec']['hyperparams'])
    else:
        return "Algorithm not supported: {}".format(hyperparam['spec']['algorithm']), 400
    return jsonify(generate_workflow(hyperparam, experiments))



if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True)