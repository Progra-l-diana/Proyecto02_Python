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

        #Conexion con mongo
        db = get_database()
        #Genera un codigo unico a la junta
        codigo = generate_code("JUN")

        #diccionario de Python con todos los datos
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

        #Se guarda la junta en la bd
        result = db.juntas.insert_one(junta)

        #Devuelve un JSON a Postman con los datos de la nueva junta e informa que se creó correctamente.
        return jsonify({ #Transforma el diccionario a un JSON
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


#Ruta de parametros
@app.route('/api/parametros', methods=['POST'])

def registrar_parametro():

    if not request.json:
        abort(400)

    data = request.json
    try:
        db = get_database()

        parametro = {
            "anio": data['anio'],
            "monto_incop": data['monto_incop'],
            "porcentajes": {
                "juntas": 50,
                "hogares": 15,
                "instituciones": 35
            },
            "fecha_limite_plan_inversion": data.get('fecha_limite_plan'),
            "fecha_limite_informe_liquidacion": data.get('fecha_limite_liquidacion'),
            "fecha_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        result = db.parametros.insert_one(parametro)

        return jsonify({
            "mensaje": "Parámetros registrados exitosamente",
            "id": str(result.inserted_id)
        }), 201

    except Exception as e:
        print(f"Error: {e}")
        abort(500)


@app.route('/api/parametros/<int:anio>', methods=['GET'])
def obtener_parametros(anio):

    try:
        db = get_database()
        parametro = db.parametros.find_one({"anio": anio})

        if not parametro:
            abort(404)

        parametro['_id'] = str(parametro['_id'])
        return jsonify(parametro), 200
    except Exception as e:
        print(f"Error: {e}")
        abort(500)

#Ruta distribucion de fondos
@app.route('/api/distribucion/calcular', methods=['POST'])
def calcular_distribucion():

    if not request.json:
        abort(400)

    data = request.json
    anio = data.get('anio')

    if not anio:
        abort(400, description="Se requiere el año")

    try:
        db = get_database()

        parametros = db.parametros.find_one({"anio": anio})
        if not parametros:
            abort(404, description="No hay parámetros para ese año")

        monto_total = parametros['monto_incop']

        monto_juntas = monto_total * 0.50
        monto_hogares = monto_total * 0.15
        monto_instituciones = monto_total * 0.35

        #Calculo para juntas
        planes_juntas = list(db.planes_inversion.find({
            "tipo_beneficiario": "junta",
            "anio_plan": anio,
            "estado": "presentado"
        }))

        total_estudiantes = 0
        for plan in planes_juntas:
            junta = db.juntas.find_one({"codigo": plan['codigo_beneficiario']})
            if junta:
                plan['estudiantes'] = junta.get('estudiantes_matriculados', 0)
                total_estudiantes += plan['estudiantes']

        promedio_por_estudiante = monto_juntas / total_estudiantes if total_estudiantes > 0 else 0

        detalle_juntas = []
        for plan in planes_juntas:
            monto_asignado = promedio_por_estudiante * plan.get('estudiantes', 0)
            detalle_juntas.append({
                "codigo": plan['codigo_beneficiario'],
                "solicitado": plan['total_solicitado'],
                "asignado": round(monto_asignado, 2)
            })

        #Calculo para hogares
        planes_hogares = list(db.planes_inversion.find({
            "tipo_beneficiario": "hogar",
            "anio_plan": anio,
            "estado": "presentado"
        }))

        total_puntos = 0
        total_personas = 0
        for plan in planes_hogares:
            hogar = db.hogares.find_one({"codigo": plan['codigo_beneficiario']})
            if hogar:
                plan['puntos'] = hogar.get('puntuacion', 0)
                plan['personas'] = hogar.get('poblacion_anual', 0)
                total_puntos += plan['puntos']
                total_personas += plan['personas']

        num_hogares = len(planes_hogares)
        monto_por_puntos = monto_hogares * 0.03
        monto_por_personas = monto_hogares * 0.70
        monto_por_disponibilidad = monto_hogares * 0.02
        monto_igual = monto_hogares * 0.25 / num_hogares if num_hogares > 0 else 0

        detalle_hogares = []
        for plan in planes_hogares:
            asig_puntos = (plan['puntos'] / total_puntos) * monto_por_puntos if total_puntos > 0 else 0
            asig_personas = (plan['personas'] / total_personas) * monto_por_personas if total_personas > 0 else 0
            asig_disponibilidad = monto_por_disponibilidad / num_hogares if num_hogares > 0 else 0

            monto_total_hogar = asig_puntos + asig_personas + asig_disponibilidad + monto_igual

            detalle_hogares.append({
                "codigo": plan['codigo_beneficiario'],
                "solicitado": plan['total_solicitado'],
                "asignado": round(monto_total_hogar, 2)
            })

        #Calculo para instituciones
        instituciones_activas = list(db.instituciones.find({"activo": True}))

        detalle_instituciones = []
        for inst in instituciones_activas:
            porcentaje = inst['porcentaje_asignado'] / 100
            monto_asignado = monto_instituciones * porcentaje

            detalle_instituciones.append({
                "codigo": inst['codigo'],
                "nombre": inst['nombre'],
                "porcentaje": inst['porcentaje_asignado'],
                "asignado": round(monto_asignado, 2)
            })

        distribucion = {
            "anio": anio,
            "monto_total": monto_total,
            "fecha_calculo": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "juntas": {
                "monto_total": monto_juntas,
                "detalle": detalle_juntas
            },
            "hogares": {
                "monto_total": monto_hogares,
                "detalle": detalle_hogares
            },
            "instituciones": {
                "monto_total": monto_instituciones,
                "detalle": detalle_instituciones
            }
        }

        db.distribuciones.insert_one(distribucion)
        return jsonify(distribucion), 200

    except Exception as e:
        print(f"Error: {e}")
        abort(500, description=str(e))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)