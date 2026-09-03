# app.py
from flask import Flask, jsonify, request
import time
import random
app = Flask(__name__)

import logging
MAX_DELAY=1
# Configurazione base del logging
logging.basicConfig(level=logging.DEBUG, filename="test.log")

@app.before_request
def log_request_info():
    app.logger.debug('Headers: %s', request.headers)
    app.logger.debug('Body: %s', request.get_data())

@app.route('/http11')
def http11_endpoint():
    time.sleep(random.randint(0,MAX_DELAY)/MAX_DELAY)
    protocol = request.environ.get('SERVER_PROTOCOL')
    return jsonify({
        "message": "Questo endpoint è stato raggiunto per testare HTTP/1.1",
        "protocol": protocol
    })

@app.route('/http2')
def http2_endpoint():
    time.sleep(random.randint(0,MAX_DELAY)/MAX_DELAY)
    protocol = request.environ.get('SERVER_PROTOCOL')
    return jsonify({
        "message": "Questo endpoint è stato raggiunto per testare HTTP/2 (in modalità cleartext)",
        "protocol_reported_by_flask": protocol
    })
    
    
@app.route('/http')
def http_endpoint():
    time.sleep(random.randint(0,10)/10)
    protocol = request.environ.get('SERVER_PROTOCOL')
    return jsonify({
        "message": "Rispondo",
        "protocol_reported_by_flask": protocol
    })