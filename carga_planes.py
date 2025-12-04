from datetime import datetime
from flask import jsonify, abort, request
from pymongo import MongoClient
import pandas as pd



# Conexión con MongoDB
def get_database():

    try:
        client = MongoClient(
            host=['127.0.0.1:27017'],
            username='admin',
            password='admin123'
        )
        db = client.LeyCaldera_DB
        return db
    except Exception as e:
        print(f"Error conectando a MongoDB: {e}")
        return None



# FUNCIÓN PARA REGISTRAR RUTAS EN LA APP PRINCIPAL

def registrar_rutas_planes(app):

    @app.route('/api/planes-inversion/cargar', methods=['POST'])
    def cargar_plan_inversion():

        if 'archivo' not in request.files:
            abort(400, description="No se envió archivo")

        archivo = request.files['archivo']
        tipo_beneficiario = request.form.get('tipo_beneficiario')
        codigo_beneficiario = request.form.get('codigo_beneficiario')
        anio = request.form.get('anio')

        if not all([tipo_beneficiario, codigo_beneficiario, anio]):
            abort(400, description="Faltan parámetros requeridos: tipo_beneficiario, codigo_beneficiario, anio")

        try:
            db = get_database()

            # Leer archivo Excel
            df = pd.read_excel(archivo, skiprows=13)


            df = df[['Detalle', 'Proveedor', 'Proforma', 'Cantidad', 'Pre Unitario', 'Sutotal']]

            # Renombrar columnas
            df.columns = ['detalle', 'proveedor', 'proforma', 'cantidad',
                          'precio_unitario', 'subtotal']



            # Limpiar datos - eliminar filas vacías
            df = df.dropna(subset=['detalle', 'proveedor'])

            # Convertir datos numéricos
            df['cantidad'] = pd.to_numeric(df['cantidad'], errors='coerce').fillna(0).astype(int)
            df['precio_unitario'] = pd.to_numeric(df['precio_unitario'], errors='coerce').fillna(0.0)
            df['subtotal'] = pd.to_numeric(df['subtotal'], errors='coerce').fillna(0.0)

            # Convertir DataFrame a lista de diccionarios
            detalle_items = df.to_dict(orient='records')

            # Calcular total solicitado
            total_solicitado = df['subtotal'].sum()

            # Crear documento para MongoDB
            plan = {
                "codigo_beneficiario": codigo_beneficiario,
                "tipo_beneficiario": tipo_beneficiario,
                "anio_plan": int(anio),
                "fecha_presentacion": datetime.now().strftime("%Y-%m-%d"),
                "total_solicitado": float(total_solicitado),
                "detalle_items": detalle_items,
                "estado": "presentado",
                "fecha_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            # Insertar en MongoDB
            result = db.planes_inversion.insert_one(plan)

            return jsonify({
                "mensaje": "Plan de inversión cargado exitosamente",
                "total_solicitado": float(total_solicitado),
                "items": len(detalle_items),
                "id": str(result.inserted_id)
            }), 201

        except Exception as e:
            print(f"Error al cargar plan de inversión: {e}")
            abort(500, description=f"Error al procesar archivo: {str(e)}")

    @app.route('/api/planes-inversion', methods=['GET'])
    def obtener_planes_inversion():

        try:
            db = get_database()
            anio = request.args.get('anio')
            tipo = request.args.get('tipo_beneficiario')

            # Construir filtro
            filtro = {}
            if anio:
                filtro['anio_plan'] = int(anio)
            if tipo:
                filtro['tipo_beneficiario'] = tipo

            planes = list(db.planes_inversion.find(filtro))

            for plan in planes:
                plan['_id'] = str(plan['_id'])

            return jsonify({"planes": planes, "total": len(planes)}), 200

        except Exception as e:
            print(f"Error: {e}")
            abort(500)

    @app.route('/api/planes-inversion/<string:codigo_beneficiario>', methods=['GET'])
    def obtener_plan_especifico(codigo_beneficiario):

        try:
            db = get_database()
            anio = request.args.get('anio')

            filtro = {"codigo_beneficiario": codigo_beneficiario}
            if anio:
                filtro['anio_plan'] = int(anio)

            plan = db.planes_inversion.find_one(filtro)

            if not plan:
                abort(404, description="Plan de inversión no encontrado")

            plan['_id'] = str(plan['_id'])
            return jsonify(plan), 200

        except Exception as e:
            print(f"Error: {e}")
            abort(500)