from flask import Flask, jsonify, abort, make_response, request
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime
import random

app = Flask(__name__)
CORS(app)

# Conexión MongoDB
def get_database():
    client = MongoClient(
        host=['127.0.0.1:27017'],
        username='admin',
        password='admin123'
    )
    db = client.ley_caldera_db
    return db

# Función para generar un codigo unico a cada entidad
def generate_code(prefix):
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_num = random.randint(100, 999)
    return f"{prefix}-{timestamp}-{random_num}"

# Manejo de errores
@app.errorhandler(400)
def bad_request(error):
    return make_response(jsonify({'error': 'Solicitud incorrecta'}), 400)

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Recurso no encontrado'}), 404)

@app.errorhandler(500)
def internal_error(error):
    return make_response(jsonify({'error': 'Error interno del servidor'}), 500)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)