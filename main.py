from flask import Flask, request, jsonify, send_from_directory
from collections import OrderedDict
import json
import os
from ServiceLayer import SAPBusinessOne
import threading

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
        OrderedDict({**pago, "order": data.get("order")})
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
    for linea in lineas:
        sap.insertar_lineas(linea)


@app.route('/procesar', methods=['POST'])
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

        cabecera_thread.start()
        lineas_thread.start()

        cabecera_thread.join()
        lineas_thread.join()
        
        '''sap.obtener_session()
        sap.insertar_cabecera(cabecera)
        sap.insertar_lineas(lineas)
        #sap.eliminar_lineas_en_rango(278,375)
        socios=sap.obtener_socios_de_negocios()
        sap.crear_socio(socios)'''

        '''response_data2 = OrderedDict([
            ("cabecera", cabecera),
        ])'''

        # Imprimir el JSON generado antes de devolverlo
       # print("JSON generado en el backend:", json.dumps(response_data2, indent=4))

        # Devolver la respuesta JSON y la ruta del archivo generado
        return jsonify(response_data), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True, port=5000)
