from flask import Flask, json, Response, make_response, request, jsonify

# Simple Server that accepts any requests
app = Flask(__name__)

@app.route('/')
def home():
    return "Coming soon."

@app.route('/register', methods=['POST'])
def register():
    data = {"instance_id": "fw-1"}
    jsonData = json.dumps(data)
    resp = make_response(jsonData, 200)
    return resp

@app.route('/keep-alive', methods=['POST'])
def keepAlive():
    resp = jsonify({"route": 'keep-alive'})
    resp.status_code = 200
    return resp

@app.route('/alert', methods=['POST'])
def alert():
    resp = jsonify({"route": 'alert'})
    resp.status_code = 200
    return resp

@app.route('/delete', methods=['POST'])
def delete():
    return 'Hello'

if(__name__ == "__main__"):
    app.run(debug=True, host='0.0.0.0', port=5000)