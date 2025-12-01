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
    db = client.LeyCaldera_DB
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


# Ruta de juntas postman
@app.route('/api/juntas', methods=['POST'])
# Registrar junta
def registrar_junta():
    if not request.json:
        abort(400)

    data = request.json

    try:
        db = get_database()
        codigo = generate_code("JUN")

        junta = {
            "codigo": codigo,
            "nombre": data['nombre'],
            "personeria_juridica": data['personeria_juridica'],
            "vencimiento_personeria": data['vencimiento_personeria'],
            "distrito": data['distrito'],
            "ubicacion": data['ubicacion'],
            "telefono": data['telefono'],
            "director": data['director'],
            "cuenta_bancaria": data.get('cuenta_bancaria', {}),
            "estudiantes_matriculados": data.get('estudiantes_matriculados', 0),
            "fecha_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "activo": True
        }

        result = db.juntas.insert_one(junta)

        return jsonify({
            "mensaje": "Junta registrada exitosamente",
            "codigo": codigo,
            "id": str(result.inserted_id)
        }), 201

    except Exception as e:
        print(f"Error: {e}")
        abort(500)

#Ruta registrar un hogar y metodo
@app.route('/api/hogares', methods=['POST'])
def registrar_hogar():

    if not request.json:
        abort(400)

    #Guarda los datos
    data = request.json

    try:
        db = get_database()
        # Genera un código único para el nuevo hogar.
        codigo = generate_code("HOG")

        hogar = {
            "codigo": codigo,
            "nombre": data['nombre'],
            "distrito": data['distrito'],
            "ubicacion": data['ubicacion'],
            "telefono": data['telefono'],
            "tipo_atencion": data['tipo_atencion'],
            "puntuacion": data['puntuacion'],
            "horario_atencion": data['horario_atencion'],
            "poblacion_anual": data.get('poblacion_anual', 0), #Si no envían poblacion_anual se pone 0 como valor
            "junta_directiva": {
                "presidente": data.get('presidente', {}),
                "tesorero": data.get('tesorero', {})
            },
            "fecha_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "activo": True
        }

        result = db.hogares.insert_one(hogar)

        return jsonify({
            "mensaje": "Hogar registrado exitosamente",
            "codigo": codigo
        }), 201

    except Exception as e:
        abort(500)

@app.route('/api/hogares', methods=['GET'])
def obtener_hogares():


    try:
        db = get_database()
        hogares = list(db.hogares.find({"activo": True}))

        #Convierte el ObjectId de MongoDB a string para poder retornarlo en JSON.
        for hogar in hogares:
            hogar['_id'] = str(hogar['_id'])

        return jsonify({"hogares": hogares}), 200

    except Exception as e:
        abort(500)

#  Ruta POST: Registrar institución
@app.route('/api/instituciones', methods=['POST'])
def registrar_institucion():

    if not request.json:
        abort(400)

    data = request.json

    try:
        db = get_database()
        codigo = generate_code("INS")

        institucion = {
            "codigo": codigo,
            "nombre": data['nombre'],
            "personeria_juridica": data.get('personeria_juridica'),
            "vencimiento_personeria": data.get('vencimiento_personeria'),
            "descripcion": data['descripcion'],
            "distrito": data['distrito'],
            "ubicacion": data['ubicacion'],
            "telefono": data['telefono'],
            "email": data['email'],
            "porcentaje_asignado": data['porcentaje_asignado'],
            "junta_directiva": {
                "presidente": data.get('presidente', {}),
                "tesorero": data.get('tesorero', {})
            },
            "cuenta_bancaria": data.get('cuenta_bancaria', {}),
            "fecha_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "activo": True
        }

        result = db.instituciones.insert_one(institucion)

        return jsonify({
            "mensaje": "Institución registrada exitosamente",
            "codigo": codigo
        }), 201

    except Exception as e:
        abort(500)

# Ruta GET: Listar instituciones activas
@app.route('/api/instituciones', methods=['GET'])
def obtener_instituciones():

    try:
        db = get_database()
        instituciones = list(db.instituciones.find({"activo": True}))

        for inst in instituciones:
            inst['_id'] = str(inst['_id'])

        return jsonify({"instituciones": instituciones}), 200
    except Exception as e:
     abort(500)



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)