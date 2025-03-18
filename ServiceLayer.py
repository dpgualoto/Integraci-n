import requests
import json
from urllib3.exceptions import InsecureRequestWarning
import pyodbc
from datetime import datetime
# Desactivar la advertencia InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
import re
class SAPBusinessOne:
    def __init__(self, config_file='config.json'):
        # Cargar configuración desde el archivo JSON
        with open(config_file, 'r') as f:
            self.config = json.load(f)
        
        # Datos de configuración
        self.service_layer_url = f"https://{self.config['Configuracion']['host']}:50000/b1s/v1/"
        self.user_sap = self.config['Configuracion']['userSAP']
        self.password_sap = self.config['Configuracion']['passSAP']
        self.company_db = self.config['Configuracion']['database_name']
        self.DNS = self.config['Configuracion']['dns']
        self.password=self.config['Configuracion']['password']
        self.user = self.config['Configuracion']['user']
        self.vista = self.config['Configuracion']['vista']
        self.vista2 = self.config['Configuracion']['vista2']
        self.database_name = self.config['Configuracion']['database_name']
        self.session_id = None
    
    def obtener_session(self):
        if self.session_id:  # Si la sesión ya está activa, no es necesario volver a obtenerla
            print("Sesión ya activa.")
            return True  # Si la sesión ya existe, no hace falta autenticar nuevamente
        # Autenticación al Service Layer
        try:
            response = requests.post(
                f"{self.service_layer_url}Login",
                json={
                    "UserName": self.user_sap,
                    "Password": self.password_sap,
                    "CompanyDB": self.company_db
                },
                verify=False  # Asegúrate de ajustar si tu certificado SSL no es verificado
            )

            if response.status_code == 200:
                self.session_id = response.cookies["B1SESSION"]
                print("Sesión obtenida correctamente.")
                return self
            else:
                print(f"Error al obtener sesión: {response.text}")
                return False
        except Exception as e:
            print(f"Error al intentar obtener la sesión: {e}")
            return False

    def insertar_cabecera(self, cabecera):
        # Verificar si la sesión está activa antes de la operación
        if not self.session_id:
            print("No se ha obtenido una sesión válida.")
            if not self.obtener_session():  # Si no hay sesión, intenta obtenerla
                print("No se pudo obtener la sesión.")
                return None
        
        url = f"{self.service_layer_url}U_HBT_CABECERA"
        # Obtener la fecha y hora actual
        fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Prepara los datos de la cabecera
        cabecera_data = {
            "Code": str(cabecera.get("order"))+cabecera.get("bill_number"),
            "Name": f"Orden {cabecera.get('order')}",
            "U_Tipti_Orden": cabecera.get("order"),
            "U_Tipti_NumeroFC": cabecera.get("Numero_FacturasCompras"),
            "U_Tipti_BillNumber": cabecera.get("bill_number"),
            "U_Tipti_Authorization_Number": cabecera.get("authorization_number"),
            "U_Tipti_Date": cabecera.get("date"),
            "U_Tipti_user_ref": cabecera["user"].get("ref"),
            "U_Tipti_User_Name": cabecera["user"].get("name"),
            "U_Tipti_Tipticard_id": cabecera["user"].get("tipticard_id"),
            "U_Email_user": cabecera["user"].get("email"),
            "U_Tipti_Partner_Name": cabecera["partner"].get("name"),
            "U_Tipti_Vat_Partner": cabecera["partner"].get("vat"),
            "U_Tipti_vat_type": cabecera["partner"].get("vat_type"),
            "U_Tipti_Street": cabecera["partner"].get("street"),
            "U_Tipti_Phone_Partner": cabecera["partner"].get("phone"),
            "U_Tipti_City_Partner": cabecera["partner"].get("city"),
            "U_Tipti_Grupo_Partner": cabecera["partner"].get("Grupo"),
            "U_Tipti_Subcategoria_Partner": cabecera["partner"].get("Subcategoria"),
            # Verificar que purchase_shopper no sea None
            "U_Tipti_purchase_shopper_id": cabecera["purchase_shopper"].get("id") if cabecera["purchase_shopper"] else None,
            "U_Tipti_purchase_shopper_name": cabecera["purchase_shopper"].get("name") if cabecera["purchase_shopper"] else None,
            "U_Tipti_purchase_shopper_ruc": cabecera["purchase_shopper"].get("ruc") if cabecera["purchase_shopper"] else None,
            "U_Tipti_purchase_shopper_canal": cabecera["purchase_shopper"].get("canal") if cabecera["purchase_shopper"] else None,
            # Verificar que delivery_shopper no sea None
            "U_Tipti_delivery_shopper_id": cabecera["delivery_shopper"].get("id") if cabecera["delivery_shopper"] else None,
            "U_Tipti_delivery_shopper_name": cabecera["delivery_shopper"].get("name") if cabecera["delivery_shopper"] else None,
            "U_Tipti_delivery_shopper_ruc": cabecera["delivery_shopper"].get("ruc") if cabecera["delivery_shopper"] else None,
            "U_Tipt_delivery_shopper_canali": cabecera["delivery_shopper"].get("canal") if cabecera["delivery_shopper"] else None,
            "U_Tipti_retailer_bills": ",".join(cabecera.get("retailer_bills", [])) if isinstance(cabecera.get("retailer_bills"), list) else "",
            "U_Tipti_vat_subtotal": cabecera.get("vat_subtotal"),
            "U_Tipti_amount_total": cabecera.get("amount_total"),
            "U_Tipti_retailer_name": cabecera.get("retailer_name"),
            "U_Tipti_retailer_ruc": cabecera.get("retailer_ruc"),
            "U_Tipti_retailer_id": cabecera.get("retailer_id"),
            "U_Ciudad_id": cabecera.get("Ciudad_id"),
            "U_Tipti_Ciudad_desc": cabecera.get("Ciudad_desc"),
            "U_Titpti_Sector_id": cabecera.get("Sector_id"),
            "U_Tipti_Sector_desc": cabecera.get("Sector_desc"),
            "U_Tipti_Tienda_id": cabecera.get("Tienda_id"),
            "U_Tipti_Tienda_desc": cabecera.get("Tienda_desc"),
            # Verificar que delivery_information no sea None
            "U_Tipti_delivery_city_id": cabecera["delivery_information"].get("city_id") if cabecera["delivery_information"] else None,
            "U_Tipti_delivery_city": cabecera["delivery_information"].get("city") if cabecera["delivery_information"] else None,
            "U_Tipti_delivery_sector_id": cabecera["delivery_information"].get("sector_id") if cabecera["delivery_information"] else None,
            "U_Tipti_delivery_sector": cabecera["delivery_information"].get("sector") if cabecera["delivery_information"] else None,
            "U_Tipti_delivery_address": cabecera["delivery_information"].get("address") if cabecera["delivery_information"] else None,
            "U_Procesado": "P",  # Puedes ajustar según sea necesario
            "U_Tipti_Estado_Cabecera": ""  # Puedes ajustar según sea necesario
            ,"U_Tipti_Fecha_Reg": fecha_actual
        }

        headers = {
            "Content-Type": "application/json",
            "Cookie": f"B1SESSION={self.session_id}; ROUTEID=.node0"  # Configuración de las cookies correctamente
        }

        print(self.session_id)

        try:
            # Intentar la inserción de la cabecera
            response = requests.post(url, json=cabecera_data, headers=headers, verify=False, timeout=30)

            if response.status_code == 201:
                print(f"Registro insertado con éxito, ID: {response.json()['Code']}")
                return response.json()
            else:
                #print(f"Error al insertar el registro: {response.text}")
                return response.text
            #None
        except requests.exceptions.Timeout:
            print("La solicitud ha superado el tiempo de espera.")
            return None
        except Exception as e:
            print(f"Error al realizar la solicitud: {e}")
            return None 

    def insertar_lineas(self, lineas):
        # Verificar si la sesión está activa antes de la operación
        if not self.session_id:
            print("No se ha obtenido una sesión válida.")
            if not self.obtener_session():  # Si no hay sesión, intenta obtenerla
                print("No se pudo obtener la sesión.")
                return None

        url = f"{self.service_layer_url}U_HBT_LINEAS"  # Cambiar la URL si es diferente
        # Obtener la fecha y hora actual
        fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        headers = {
            "Content-Type": "application/json",
            "Cookie": f"B1SESSION={self.session_id}; ROUTEID=.node0"  # Configuración de las cookies correctamente
        }

        print(self.session_id)

        for linea in lineas:
            # Preparar los datos de la línea
            linea_data = {
                #"Code": str(linea.get("order")) +'-'+str(linea.get("linenum", 0)),
                "Name": f"Orden {linea.get('order')}-{linea.get("linenum", 0)}",
                "U_Tipti_Order": linea.get("order"),
                "U_Tipti_Linenum": linea.get("linenum", 0),
                "U_Titpti_Quantity": linea.get("quantity"),
                "U_Tipti_product_code": linea.get("product_code"),
                "U_Tipti_product_code_secundario": linea.get("product_code_secundario"),
                "U_Tipti_product_name": linea.get("product_name"),
                "U_Tipti_product_description": linea.get("product_description"),
                "U_tipti_revenue_source": linea.get("revenue_source"),
                "U_Tipti_Category1": linea.get("category1"),
                "U_Tipti_category2": linea.get("category2"),
                "U_Tipti_category3": linea.get("category3"),
                "U_Tipti_category4": linea.get("category4"),
                "U_Tipti_Sequence": linea.get("sequence"),
                "U_Tipti_tax": linea.get("tax"),
                "U_Tipti_price_unit": linea.get("price_unit"),
                "U_Tipti_price_unit_without_tax": linea.get("price_unit_without_tax"),
                "U_Tipti_LineTotal": linea.get("line_total"),
                "U_Tipti_margin": linea.get("margin"),
                "U_Tipti_validate_inventory": linea.get("validate_inventory"),
                "U_Tipti_Estado_Lineas": "P",
                "U_Tipti_Secuencial": linea.get("bill_number"),
                "U_Tipti_Fecha_Reg": fecha_actual
            }

            # Imprimir la trama (el JSON a enviar)
            #print("Trama a enviar:", json.dumps(linea_data, indent=4))  # Usamos json.dumps para una mejor presentación

            try:
                # Intentar la inserción de la línea
                response = requests.post(url, json=linea_data, headers=headers, verify=False, timeout=30)

                if response.status_code == 201:
                    print(f"Registro de línea insertado con éxito, ID: {response.json()['Code']}")
                else:
                    print(f"Error al insertar el registro de línea: {response.text}")
            except requests.exceptions.Timeout:
                print("La solicitud ha superado el tiempo de espera.")
            except Exception as e:
                print(f"Error al realizar la solicitud: {e}")

    def insertar_pagos(self, pagos):
    # Verificar si la sesión está activa antes de la operación
        if not self.session_id:
            print("No se ha obtenido una sesión válida.")
            if not self.obtener_session():  # Si no hay sesión, intenta obtenerla
                print("No se pudo obtener la sesión.")
                return None

        url = f"{self.service_layer_url}U_TIPTI_PAGOS"  # URL para los pagos (ajústalo según tu API)
        # Obtener la fecha y hora actual
        fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Preparar los datos de los pagos
        for pago in pagos:
            pago_data = {
                "Name": f"Pago {pago.get('order')}-{pago.get('id_interno')}",  # Usar el número de la factura como referencia
                "U_Tipti_ID_interno": pago.get("id_interno"),
                "U_Tipti_Method": pago.get("method"),
                "U_Tipti_Amount": pago.get("amount"),
                "U_Tipti_Date": pago.get("date"),
                "U_Tipti_id_externo": pago.get("id_externo"),
                "U_Tipti_Autorizacion": pago.get("authorization_code"),
                "U_Tipti_Orden": pago.get("order"),
                "U_Tipti_BillNumber": pago.get("billnumber"),
                "U_Tipti_Estado_Pagos":'P',
                "U_Tipti_Fecha_Reg": fecha_actual

            }

            headers = {
                "Content-Type": "application/json",
                "Cookie": f"B1SESSION={self.session_id}; ROUTEID=.node0"  # Configuración de las cookies correctamente
            }

            print(self.session_id)

            try:
                # Intentar la inserción del pago
                response = requests.post(url, json=pago_data, headers=headers, verify=False, timeout=30)

                if response.status_code == 201:
                    print(f"Pago registrado con éxito, ID: {response.json()['Code']}")
                else:
                    print(f"Error al insertar el pago: {response.text}")
            except requests.exceptions.Timeout:
                print("La solicitud ha superado el tiempo de espera.")
            except Exception as e:
                print(f"Error al realizar la solicitud: {e}")

    def insertar_errores(self, order,billnumber,respuesta,json):
    # Verificar si la sesión está activa antes de la operación
        if not self.session_id:
            print("No se ha obtenido una sesión válida.")
            if not self.obtener_session():  # Si no hay sesión, intenta obtenerla
                print("No se pudo obtener la sesión.")
                return None

        url = f"{self.service_layer_url}U_TIPTI_ERRORES"  # URL para los pagos (ajústalo según tu API)
        # Obtener la fecha y hora actual
        fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Preparar los datos de los pagos
        MAX_LENGTH=254
        
        error_data = {
                "Name":str(order) + str(billnumber),  # Usar el número de la factura como referencia
                "U_Tipti_Orden":order,	
                "U_Tipti_BillNumber":billnumber,	
                "U_Tipti_Error":str(respuesta[:MAX_LENGTH]),
                "U_Tipti_Json":json[:MAX_LENGTH] if isinstance(json, str) else str(json)[:MAX_LENGTH],	
                "U_Tipti_fecha":fecha_actual
            }

        headers = {
                "Content-Type": "application/json",
                "Cookie": f"B1SESSION={self.session_id}; ROUTEID=.node0"  # Configuración de las cookies correctamente
            }

        print(self.session_id)

        try:
                # Intentar la inserción del pago
                response = requests.post(url, json=error_data, headers=headers, verify=False, timeout=30)

                if response.status_code == 201:
                    print(f"Error registrado con éxito, ID: {response.json()['Code']}")
                else:
                    print(f"Error al insertar el error: {response.text}")
        except requests.exceptions.Timeout:
                print("La solicitud ha superado el tiempo de espera.")
        except Exception as e:
                print(f"Error al realizar la solicitud: {e}")

    """def insertar_cabecera(self, cabecera):
        # Validar campos antes de insertar
        print(f"Valor de 'order': {cabecera.get('order')}")
        validacion = validar_campos(cabecera)
        if validacion:
            return validacion  # Retorna el error 400 con el mensaje de validación

        # Continuamos con la inserción si todo es correcto
        if not self.session_id:
            print("No se ha obtenido una sesión válida.")
            if not self.obtener_session():  # Si no hay sesión, intenta obtenerla
                print("No se pudo obtener la sesión.")
                return None

        url = f"{self.service_layer_url}U_HBT_CABECERA"
        fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cabecera_data = {
            "Code": str(cabecera.get("order"))+cabecera.get("bill_number"),
            "Name": f"Orden {cabecera.get('order')}",
            "U_Tipti_Orden": cabecera.get("order"),
            "U_Tipti_NumeroFC": cabecera.get("Numero_FacturasCompras"),
            "U_Tipti_BillNumber": cabecera.get("bill_number"),
            "U_Tipti_Authorization_Number": cabecera.get("authorization_number"),
            "U_Tipti_Date": cabecera.get("date"),
            "U_Tipti_user_ref": cabecera["user"].get("ref"),
            "U_Tipti_User_Name": cabecera["user"].get("name"),
            "U_Tipti_Tipticard_id": cabecera["user"].get("tipticard_id"),
            "U_Email_user": cabecera["user"].get("email"),
            "U_Tipti_Partner_Name": cabecera["partner"].get("name"),
            "U_Tipti_Vat_Partner": cabecera["partner"].get("vat"),
            "U_Tipti_vat_type": cabecera["partner"].get("vat_type"),
            "U_Tipti_Street": cabecera["partner"].get("street"),
            "U_Tipti_Phone_Partner": cabecera["partner"].get("phone"),
            "U_Tipti_City_Partner": cabecera["partner"].get("city"),
            "U_Tipti_Grupo_Partner": cabecera["partner"].get("Grupo"),
            "U_Tipti_Subcategoria_Partner": cabecera["partner"].get("Subcategoria"),
            # Verificar que purchase_shopper no sea None
            "U_Tipti_purchase_shopper_id": cabecera["purchase_shopper"].get("id") if cabecera["purchase_shopper"] else None,
            "U_Tipti_purchase_shopper_name": cabecera["purchase_shopper"].get("name") if cabecera["purchase_shopper"] else None,
            "U_Tipti_purchase_shopper_ruc": cabecera["purchase_shopper"].get("ruc") if cabecera["purchase_shopper"] else None,
            "U_Tipti_purchase_shopper_canal": cabecera["purchase_shopper"].get("canal") if cabecera["purchase_shopper"] else None,
            # Verificar que delivery_shopper no sea None
            "U_Tipti_delivery_shopper_id": cabecera["delivery_shopper"].get("id") if cabecera["delivery_shopper"] else None,
            "U_Tipti_delivery_shopper_name": cabecera["delivery_shopper"].get("name") if cabecera["delivery_shopper"] else None,
            "U_Tipti_delivery_shopper_ruc": cabecera["delivery_shopper"].get("ruc") if cabecera["delivery_shopper"] else None,
            "U_Tipt_delivery_shopper_canali": cabecera["delivery_shopper"].get("canal") if cabecera["delivery_shopper"] else None,
            "U_Tipti_retailer_bills": ",".join(cabecera.get("retailer_bills", [])) if isinstance(cabecera.get("retailer_bills"), list) else "",
            "U_Tipti_vat_subtotal": cabecera.get("vat_subtotal"),
            "U_Tipti_amount_total": cabecera.get("amount_total"),
            "U_Tipti_retailer_name": cabecera.get("retailer_name"),
            "U_Tipti_retailer_ruc": cabecera.get("retailer_ruc"),
            "U_Tipti_retailer_id": cabecera.get("retailer_id"),
            "U_Ciudad_id": cabecera.get("Ciudad_id"),
            "U_Tipti_Ciudad_desc": cabecera.get("Ciudad_desc"),
            "U_Titpti_Sector_id": cabecera.get("Sector_id"),
            "U_Tipti_Sector_desc": cabecera.get("Sector_desc"),
            "U_Tipti_Tienda_id": cabecera.get("Tienda_id"),
            "U_Tipti_Tienda_desc": cabecera.get("Tienda_desc"),
            # Verificar que delivery_information no sea None
            "U_Tipti_delivery_city_id": cabecera["delivery_information"].get("city_id") if cabecera["delivery_information"] else None,
            "U_Tipti_delivery_city": cabecera["delivery_information"].get("city") if cabecera["delivery_information"] else None,
            "U_Tipti_delivery_sector_id": cabecera["delivery_information"].get("sector_id") if cabecera["delivery_information"] else None,
            "U_Tipti_delivery_sector": cabecera["delivery_information"].get("sector") if cabecera["delivery_information"] else None,
            "U_Tipti_delivery_address": cabecera["delivery_information"].get("address") if cabecera["delivery_information"] else None,
            "U_Procesado": "P",  # Puedes ajustar según sea necesario
            "U_Tipti_Estado_Cabecera": ""  # Puedes ajustar según sea necesario
            ,"U_Tipti_Fecha_Reg": fecha_actual
        }

        headers = {
            "Content-Type": "application/json",
            "Cookie": f"B1SESSION={self.session_id}; ROUTEID=.node0"
        }

        try:
            # Intentar la inserción de la cabecera
            response = requests.post(url, json=cabecera_data, headers=headers, verify=False, timeout=30)

            if response.status_code == 201:
                print(f"Registro insertado con éxito, ID: {response.json()['Code']}")
                return response.json()
            else:
                print(f"Error al insertar el registro: {response.text}")
                return None
        except requests.exceptions.Timeout:
            print("La solicitud ha superado el tiempo de espera.")
            return None
        except Exception as e:
            print(f"Error al realizar la solicitud: {e}")
            return None"""

    
def validar_campos(cabecera):
    # Verificar si los campos obligatorios están presentes
    if not cabecera.get("order") or cabecera["order"].strip() == "":
        return {"error": {"code": -400, "message": "El campo 'order' es obligatorio."}}, 400
    if not cabecera.get("bill_number"):
        return {"error": {"code": -400, "message": "El campo 'bill_number' es obligatorio."}}, 400

    # Verificar que el email tenga el formato correcto
    email = cabecera["user"].get("email")
    if email:
        # Usamos una expresión regular para validar el formato del correo
        email_regex = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
        if not re.match(email_regex, email):
            return {"error": {"code": -400, "message": f"El formato del correo '{email}' no es válido."}}, 400
    else:
        return {"error": {"code": -400, "message": "El campo 'email' es obligatorio."}}, 400

    # Si todas las validaciones pasan, retornamos None
    return None
    
    
def eliminar_lineas_en_rango(self, start_code, end_code):
        # Verificar si la sesión está activa antes de la operación
        if not self.session_id:
            print("No se ha obtenido una sesión válida.")
            if not self.obtener_session():  # Si no hay sesión, intenta obtenerla
                print("No se pudo obtener la sesión.")
                return None

        for code in range(start_code, end_code + 1):
            url = f"https://13.92.0.225:50000/b1s/v1/U_HBT_LINEAS({code})"  # Usamos el code del registro a eliminar

            headers = {
                "Content-Type": "application/json",
                "Cookie": f"B1SESSION={self.session_id}; ROUTEID=.node0"  # Configuración de las cookies correctamente
            }

            try:
                # Realizar la solicitud DELETE
                response = requests.delete(url, headers=headers, verify=False, timeout=30)

                if response.status_code == 204:
                    print(f"Registro con Code {code} eliminado con éxito.")
                else:
                    print(url)
                    print(f"Error al eliminar el registro con Code {code}: {response.text}")
            except requests.exceptions.Timeout:
                print(f"La solicitud para eliminar el registro con Code {code} ha superado el tiempo de espera.")
            except Exception as e:
                print(f"Error al realizar la solicitud para Code {code}: {e}")
    

        # Verificar si la sesión está activa antes de la operación
        if not self.session_id:
            print("No se ha obtenido una sesión válida.")
            if not self.obtener_session():  # Si no hay sesión, intenta obtenerla
                print("No se pudo obtener la sesión.")
                return None

        for item in items:
            # Asegurarse de que los datos del socio de negocios sean correctos
            item_data = {
                "ItemCode": item.LicTradNum,
                "ItemName": item.CardName,
                "ItemsGroupCode": item.LicTradNum,
                "SalesItem": "tYES",
                "U_Tipti_Cod_Secun":""
                #"SubCategoria": socio.SubCategoria  
            }
            #print("Datos del socio de negocios a crear:", partner_data)

            url = f"{self.service_layer_url}Items"
            headers = {
                "Content-Type": "application/json",
                "Cookie": f"B1SESSION={self.session_id}; ROUTEID=.node0"
            }

            try:
                # Realizar la solicitud POST para crear el socio de negocios
                response = requests.post(url, json=item_data, headers=headers, verify=False, timeout=30)

                # Imprimir más detalles de la respuesta
                #print("Código de respuesta:", response.status_code)
                #print("Encabezados de la respuesta:", response.headers)
                #print("Respuesta del servidor:", response.text)

                if response.status_code == 201:
                    print(f"Item creado con éxito, ID: {response.json()['ItemCode']}")
                else:
                    print(f"Error al crear el item. Código de error: {response.status_code}")
                    print(f"Detalles del error: {response.text}")
            except Exception as e:
                print(f"Error al realizar la solicitud: {e}")