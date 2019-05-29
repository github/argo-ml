from flask import Flask, request, jsonify

from controller import grid_search, generate_workflow


app = Flask(__name__)


@app.route("/workflow", methods=["POST"])
def workflow():
    hyperparam = request.json
    if hyperparam['spec']['algorithm'] == 'grid':
        try:
            experiments = grid_search(hyperparam['spec']['hyperparams'])
        except Exception as e:
            return "Error while generating experiments: {}".format(e), 500
    else:
        return "Algorithm not supported: {}".format(hyperparam['spec']['algorithm']), 400
    return jsonify(generate_workflow(hyperparam, experiments))


if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True)