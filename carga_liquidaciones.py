
#Modulo de carga de informe de liquidacion
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
        print(f"Error al conectar a MongoDB: {e}")
        return None



#funcion para registrar rutas

def registrar_rutas_liquidaciones(app):

    @app.route('/api/informes-liquidacion/cargar', methods=['POST'])
    def cargar_informe_liquidacion():

        if 'archivo' not in request.files:
            abort(400, description="No se envió archivo")

        archivo = request.files['archivo']
        codigo_beneficiario = request.form.get('codigo_beneficiario')
        anio = request.form.get('anio')

        if not all([codigo_beneficiario, anio]):
            abort(400, description="Faltan parámetros requeridos: codigo_beneficiario, anio")

        try:
            db = get_database()

            #Leer archivo Excel (saltando primeras 15 filas que son encabezado)
            df = pd.read_excel(archivo, skiprows=15)

            #El Excel tiene columnas extra, seleccionamos las importantes
            df.columns = ['detalle', 'col2', 'col3', 'col4', 'col5', 'col6',
                          'proveedor', 'factura', 'requerido', 'asignado', 'faltante']

            #Seleccionar solo columnas necesarias
            df = df[['detalle', 'proveedor', 'factura', 'requerido', 'asignado', 'faltante']]

            #Limpiar datos - eliminar filas vacías
            df = df.dropna(subset=['detalle', 'proveedor', 'factura'])

            #Convertir datos numéricos
            df['requerido'] = pd.to_numeric(df['requerido'], errors='coerce').fillna(0.0)
            df['asignado'] = pd.to_numeric(df['asignado'], errors='coerce').fillna(0.0)
            df['faltante'] = pd.to_numeric(df['faltante'], errors='coerce').fillna(0.0)

            #Convertir DataFrame a lista de diccionarios
            detalle_items = df.to_dict(orient='records')

            #Crear documento para MongoDB
            informe = {
                "codigo_beneficiario": codigo_beneficiario,
                "anio_liquidacion": int(anio),
                "fecha_presentacion": datetime.now().strftime("%Y-%m-%d"),
                "total_requerido": float(df['requerido'].sum()),
                "total_asignado": float(df['asignado'].sum()),
                "total_aplicado": float(df['asignado'].sum()),
                "total_sin_usar": float(df['faltante'].sum()),
                "detalle_items": detalle_items,
                "estado": "presentado",
                "fecha_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            #Insertar en MongoDB
            result = db.informes_liquidacion.insert_one(informe)

            return jsonify({
                "mensaje": "Informe de liquidación cargado exitosamente",
                "total_requerido": float(df['requerido'].sum()),
                "total_asignado": float(df['asignado'].sum()),
                "total_sin_usar": float(df['faltante'].sum()),
                "items": len(detalle_items),
                "id": str(result.inserted_id)
            }), 201

        except Exception as e:
            print(f"Error al cargar informe de liquidación: {e}")
            abort(500, description=f"Error al procesar archivo: {str(e)}")



    @app.route('/api/informes-liquidacion', methods=['GET'])
    def obtener_informes_liquidacion():

        try:
            db = get_database()
            anio = request.args.get('anio')


            filtro = {}
            if anio:
                filtro['anio_liquidacion'] = int(anio)

            informes = list(db.informes_liquidacion.find(filtro))

            for informe in informes:
                informe['_id'] = str(informe['_id'])

            return jsonify({"informes": informes, "total": len(informes)}), 200

        except Exception as e:
            print(f"Error: {e}")
            abort(500)

    @app.route('/api/informes-liquidacion/<string:codigo_beneficiario>', methods=['GET'])
    def obtener_informe_especifico(codigo_beneficiario):

        try:
            db = get_database()
            anio = request.args.get('anio')

            filtro = {"codigo_beneficiario": codigo_beneficiario}
            if anio:
                filtro['anio_liquidacion'] = int(anio)

            informe = db.informes_liquidacion.find_one(filtro)

            if not informe:
                abort(404, description="Informe de liquidación no encontrado")

            informe['_id'] = str(informe['_id'])
            return jsonify(informe), 200

        except Exception as e:
            print(f"Error: {e}")
        abort(500)
