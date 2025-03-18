from flask import Flask, request, jsonify, send_from_directory
from collections import OrderedDict
import json
import os
import re
from ServiceLayer import SAPBusinessOne
import threading
from datetime import datetime

app = Flask(__name__)
sap = SAPBusinessOne(config_file='config.json')

# Directorio para guardar los archivos generados
UPLOAD_FOLDER = './json_files'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def procesar_cabecera(data):
    return OrderedDict([
        ("order", data.get("order")),
        ("Numero_FacturasCompras", data.get("Numero_FacturasCompras")),
        ("bill_number", data.get("bill_number")),
        ("authorization_number", data.get("authorization_number")),
        ("date", data.get("date")),
        ("user", data.get("user")),
        ("partner", data.get("partner")),
        ("purchase_shopper", data.get("purchase_shopper")),
        ("delivery_shopper", data.get("delivery_shopper")),
        ("retailer_bills", data.get("retailer_bills")),
        ("vat_subtotal", data.get("vat_subtotal")),
        ("amount_total", data.get("amount_total")),
        ("retailer_name", data.get("retailer_name")),
        ("retailer_ruc", data.get("retailer_ruc")),
        ("retailer_id", data.get("retailer_id")),
        ("Ciudad_id", data.get("Ciudad_id")),
        ("Ciudad_desc", data.get("Ciudad_desc")),
        ("Sector_id", data.get("Sector_id")),
        ("Sector_desc", data.get("Sector_desc")),
        ("Tienda_id", data.get("Tienda_id")),
        ("Tienda_desc", data.get("Tienda_desc")),
        ("delivery_information", data.get("delivery_information"))
    ])

def procesar_lineas_y_descuentos(data):
    lineas = []
    descuentos = []

    for linenum, linea in enumerate(data.get("sale_lines", [])):
        nueva_linea = OrderedDict([
            (k, v) for k, v in linea.items() if k != "discounts"
        ])
        nueva_linea["linenum"] = linenum
        nueva_linea["order"]=data.get("order")
        nueva_linea["bill_number"]=data.get("bill_number")
        lineas.append(nueva_linea)

        descuentos.extend(
            OrderedDict([
                ("order", data.get("order")),
                ("linenum", linenum),
                ("discount_id", descuento.get("discount_id")),
                ("discount_name", descuento.get("discount_name")),
                ("discount_rate", descuento.get("discount_rate")),
                ("discount_group", descuento.get("discount_group")),
                ("amount", descuento.get("amount"))
            ])
            for descuento in linea.get("discounts", [])
        )
    
    return lineas, descuentos

def procesar_pagos(data):
    return [
        OrderedDict({**pago, "order": data.get("order"), "billnumber": data.get("bill_number")})
        for pago in data.get("payments", [])
    ]

def procesar_refund(data):
    refund_data = data.get("refund", {})
    return [
        OrderedDict({**refund_data, "tipticard_id": data.get("user", {}).get("tipticard_id"), "order": data.get("order")})
    ]

def insertar_cabecera_thread(cabecera, sap):
    sap.insertar_cabecera(cabecera)

def insertar_lineas_thread(lineas, sap):
    sap.insertar_lineas(lineas)

def insertar_pagos_thread(pagos,sap):
    sap.insertar_pagos(pagos)

"""@app.route('/procesar', methods=['POST'])
def procesar_json():
    try:
        data = request.get_json() 
        cabecera = procesar_cabecera(data)
        lineas, descuentos = procesar_lineas_y_descuentos(data)
        pagos = procesar_pagos(data)
        refund = procesar_refund(data)


        # Construir el JSON de respuesta
        response_data = OrderedDict([
            ("cabecera", cabecera),
            ("lineas", lineas),
            ("pagos", pagos),
            ("descuentos", descuentos),
            ("refund", refund),
        ])

          # Guardar el archivo JSON en el servidor
        json_filename = f"procesado_{data.get('order')}.json"
        json_file_path = os.path.join(UPLOAD_FOLDER, json_filename)
        with open(json_file_path, 'w', encoding='utf-8') as f:
            json.dump(response_data, f, ensure_ascii=False, indent=4)

         # Iniciar hilos para procesar cabecera y lineas en paralelo
        cabecera_thread = threading.Thread(target=insertar_cabecera_thread, args=(cabecera, sap))
        lineas_thread = threading.Thread(target=insertar_lineas_thread, args=(lineas, sap))
        pagos_thread = threading.Thread(target=insertar_pagos_thread, args=(pagos, sap))

        cabecera_thread.start()
        lineas_thread.start()
        pagos_thread.start()

        cabecera_thread.join()
        lineas_thread.join()
        pagos_thread.join()
        #sap.obtener_session()
        #sap.insertar_cabecera(cabecera)
        #sap.insertar_lineas(lineas)
        #sap.eliminar_lineas_en_rango(376,571)
        #socios=sap.obtener_socios_de_negocios()
        #sap.crear_socio(socios)

        response_data2 = OrderedDict([
            ("cabecera", cabecera),
        ])

        # Imprimir el JSON generado antes de devolverlo
       # print("JSON generado en el backend:", json.dumps(response_data2, indent=4))

        # Devolver la respuesta JSON y la ruta del archivo generado
        return jsonify(response_data), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400"""


def validar_fecha(date_str):
    try:
        # Intentar convertir la cadena al formato de fecha
        date_obj = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        return date_obj  # Si la conversión es exitosa, retornamos el objeto datetime
    except ValueError:
        return None  # Si la conversión falla, significa que la fecha no es válida
    
def validar_campos(cabecera):
    #print(cabecera)
    # Verificar si los campos obligatorios están presentes
    if not cabecera.get("order") :
        return {"error": {"code": -400, "message": "El campo 'order' es obligatorio."}}, 400
    
    if not cabecera.get("bill_number") or cabecera["bill_number"].strip() == "":
        return {"error": {"code": -400, "message": "El campo 'bill_number' es obligatorio."}}, 400
    
    if not cabecera.get("authorization_number") or cabecera["authorization_number"].strip() == "":
        return {"error": {"code": -400, "message": "El campo 'authorization_number' es obligatorio."}}, 400
    
        # Validar la fecha
    date_str = cabecera.get("date")
    if not date_str or not date_str.strip():
        return {"error": {"code": -400, "message": "El campo 'date' es obligatorio."}}, 400
    # Intentar convertir la fecha
    fecha = validar_fecha(date_str)
    if not fecha:
        return {"error": {"code": -400, "message": f"El formato de la fecha '{date_str}' no es válido. El formato debe ser 'YYYY-MM-DD HH:MM:SS'."}}, 400

    #validaciones PARTNER

    vat=cabecera["partner"].get("vat")
    if not vat or vat.strip() == "":
        return {"error": {"code": -400, "message": "El campo 'vat' es obligatorio."}}, 400
    
    name=cabecera["partner"].get("name")
    if not name or name.strip() == "":
        return {"error": {"code": -400, "message": "El campo 'name' es obligatorio."}}, 400

    # Verificar que el email tenga el formato correcto
    email = cabecera["partner"].get("email")
    if email:
        # Usamos una expresión regular para validar el formato del correo
        email_regex = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
        if not re.match(email_regex, email):
            return {"error": {"code": -400, "message": f"El formato del correo '{email}' no es válido."}}, 400
    else:
        return {"error": {"code": -400, "message": "El campo 'email' es obligatorio."}}, 400
    

    # Si todas las validaciones pasan, retornamos None
    return None
    
def validar_sale_lines(sale_lines):
    #print(sale_lines)  # Verificar la estructura real
    for line in sale_lines:
        # Convertir OrderedDict a dict si es necesario
        if isinstance(line, OrderedDict):
            line = dict(line)

        product_code = line.get("product_code", "").strip()  # Asegura que sea una cadena sin espacios
        print(f"Producto: '{product_code}'")  # Mostrar el valor real de product_code

        if not product_code:
            error_response = {"error": {"code": -400, "message": "El campo 'product_code' es obligatorio y no puede estar vacío o nulo."}}
            print("Respuesta de error:", error_response)  # Para verificar que se genera correctamente
            return error_response, 400  # Retornar correctamente

    return None  # Si no hay errores, retornar None

@app.route('/procesar', methods=['POST'])
def procesar_json():
    try:
        data = request.get_json() 
        cabecera = procesar_cabecera(data)
        lineas, descuentos = procesar_lineas_y_descuentos(data)
        pagos = procesar_pagos(data)
        refund = procesar_refund(data)

        validacion = validar_campos(data)  # Validamos los campos (en este caso 'order' y otros)
        if validacion:
            orden=cabecera['order']
            billnumber=cabecera['bill_number']
            datafin=dict(cabecera)
            print(validacion)
            sap.insertar_errores(orden,billnumber,validacion,datafin)
            return jsonify(validacion), 400
        
        validaciones_lineas=validar_sale_lines(lineas)
        if validaciones_lineas:
            orden=cabecera['order']
            billnumber=cabecera['bill_number']
            datafin=dict(cabecera)
            print(validaciones_lineas)
            sap.insertar_errores(orden,billnumber,validaciones_lineas,datafin)
            return jsonify(validaciones_lineas), 400

        # Intentar insertar la cabecera y verificar si fue exitosa
        cabecera_response = sap.insertar_cabecera(cabecera)
        """if cabecera_response is None:  # Si la cabecera no se insertó correctamente
            print(cabecera['order'])
            return jsonify({"error": "No se pudo registrar la cabecera, las líneas y los pagos no se procesarán."}), 400"""
        if isinstance(cabecera_response, str):
            orden=cabecera['order']
            billnumber=cabecera['bill_number']
            datafin=dict(cabecera)
            sap.insertar_errores(orden,billnumber,cabecera_response,datafin) 
            return jsonify({"error": cabecera_response}), 400

        
        # Iniciar los hilos para insertar líneas y pagos si la cabecera fue exitosa
        lineas_thread = threading.Thread(target=sap.insertar_lineas, args=(lineas,))
        pagos_thread = threading.Thread(target=sap.insertar_pagos, args=(pagos,))

        lineas_thread.start()
        pagos_thread.start()

        # Esperar a que los hilos terminen
        lineas_thread.join()
        pagos_thread.join()

        # Construir el JSON de respuesta
        response_data = OrderedDict([
            ("cabecera", cabecera),
            ("lineas", lineas),
            ("pagos", pagos),
            ("descuentos", descuentos),
            ("refund", refund),
        ])

        # Guardar el archivo JSON en el servidor
        json_filename = f"procesado_{data.get('order')}.json"
        json_file_path = os.path.join(UPLOAD_FOLDER, json_filename)
        with open(json_file_path, 'w', encoding='utf-8') as f:
            json.dump(response_data, f, ensure_ascii=False, indent=4)

        # Devolver la respuesta JSON y la ruta del archivo generado
        return jsonify(response_data), 200

    except Exception as e:
        return jsonify({"error fin": str(e)}), 400



if __name__ == '__main__':
    app.run(debug=True, port=9000)
