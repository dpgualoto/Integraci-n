import pyodbc
import requests
import json
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict
import pandas as pd 
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from decimal import Decimal
import time
from collections import deque
import threading
# Definir una cola de tareas
facturas_queue = deque()

# Definir un conjunto para controlar los socios de negocios e ítems creados
socios_creados = set()
items_creados = set()

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
        self.password = self.config['Configuracion']['password']
        self.user = self.config['Configuracion']['user']
        self.vista = self.config['Configuracion']['vista']
        self.vista2 = self.config['Configuracion']['vista2']
        self.vista3 = self.config['Configuracion']['vista3']
        self.vista4 = self.config['Configuracion']['vista4']
        self.session_id = None

    def obtener_session(self):
        if self.session_id:
            return True
        try:
            response = requests.post(
                f"{self.service_layer_url}Login",
                json={
                    "UserName": self.user_sap,
                    "Password": self.password_sap,
                    "CompanyDB": self.company_db
                },
                verify=False
            )
            if response.status_code == 200:
                self.session_id = response.cookies["B1SESSION"]
                return True
            else:
                print(f"Error al obtener sesión: {response.text}")
                return False
        except Exception as e:
            print(f"Error al intentar obtener la sesión: {e}")
            return False

    def obtener_socios_de_negocios(self):
        # Establecer conexión ODBC usando el DNS configurado
        connection_string = f'DSN={self.DNS};UID={self.user};PWD={self.password};'
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        
        # Ejecutar la consulta a la vista
        consulta = f"SELECT * FROM {self.company_db}.{self.vista}"
        cursor.execute(consulta)
        socios = cursor.fetchall() 
        
        conn.close()
        return socios

    def crear_socio(self, socio):
        if not self.session_id:
            if not self.obtener_session():
                return None

        partner_data = {
            "CardCode": socio.LicTradNum,
            "CardName": socio.CardName,
            "FederalTaxID": socio.LicTradNum,
            "CardType": "C", 
            "Phone1": socio.Phone1,
            "City": socio.Ciudad,
            "GroupCode": socio.GroupCode
        }

        url = f"{self.service_layer_url}BusinessPartners"
        headers = {
            "Content-Type": "application/json",
            "Cookie": f"B1SESSION={self.session_id}; ROUTEID=.node0"
        }

        try:
            # Realizar la solicitud POST para crear el socio de negocios
            response = requests.post(url, json=partner_data, headers=headers, verify=False, timeout=30)
            if response.status_code == 201:
                print(f"Socio de negocios creado con éxito, ID: {response.json()['CardCode']}")
            else:
                print(f"Error al crear el socio de negocios. Código de error: {response.status_code}")
                print(f"Detalles del error: {response.text}")
        except Exception as e:
            print(f"Error al realizar la solicitud: {e}")

    def obtener_items(self):
        # Establecer conexión ODBC para obtener los ítems
        connection_string = f'DSN={self.DNS};UID={self.user};PWD={self.password};'
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()

        # Ejecutar la consulta para obtener los ítems
        consulta = f"SELECT * FROM {self.company_db}.{self.vista2}"  # Ajusta según la tabla de ítems que tengas
        cursor.execute(consulta)
        items = cursor.fetchall()
        
        conn.close()
        return items

    def crear_item(self, item):
        if not self.session_id:
            if not self.obtener_session():
                return None

        item_data = {
            "ItemCode": item.ItemCode,
            "ItemName": item.ItemName,
            "BarCode": item.ItemCode2,
            "ItemsGroupCode":111,
            #"Price": item.Price,
            "PurchaseItem": "tYES",
            "SalesItem": "tYES",
            "InventoryItem": "tNO",
            "U_Tipti_Cod_Secun": item.ItemCode
        }

        url = f"{self.service_layer_url}Items"
        headers = {
            "Content-Type": "application/json",
            "Cookie": f"B1SESSION={self.session_id}; ROUTEID=.node0"
        }

        try:
            # Realizar la solicitud POST para crear el ítem
            response = requests.post(url, json=item_data, headers=headers, verify=False, timeout=30)
            if response.status_code == 201:
                print(f"Ítem creado con éxito, Código: {response.json()['ItemCode']}")
            else:
                print(f"Error al crear el ítem. Código de error: {response.status_code}")
                print(f"Detalles del error: {response.text}")
        except Exception as e:
            print(f"Error al realizar la solicitud: {e}")

    def obtener_Facturas(self):
        connection_string = f'DSN={self.DNS};UID={self.user};PWD={self.password};'
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()

        consulta = f"SELECT * FROM {self.company_db}.{self.vista3}"
        cursor.execute(consulta)
        facturas = cursor.fetchall()
        conn.close()
        return facturas

    def procesar_factura(self, factura, facturas):
        orden = factura.Orden  # El campo de orden
        billnumber = factura.NumAtCard  # El campo de billnumber
        # Convertir DocDate si es un objeto datetime
        if isinstance(factura.DocDate, datetime):
            DocDate = factura.DocDate.isoformat()  # Convierte a formato ISO 8601 (cadena)
        else:
            DocDate = factura.DocDate

        # Filtrar las líneas de la factura que pertenecen a la misma orden (para evitar duplicados)
        lineas_factura = [
            {
                "ItemCode": f.ItemCode,
                "Quantity": f.Cantidad,
                "TaxCode": f.Tax,
                "LineTotal": f.LineTotal,
                "UoMEntry": 1
                #"UoMCode": "Und"
            }
            for f in facturas if f.Orden == orden and f.NumAtCard == billnumber  # Filtra las líneas de la misma orden
        ]

        # Crear el JSON de la factura, asegurándose de no duplicar
        factura_json = {
            "CardCode": factura.CardCode,
            "DocObjectCode": "13",  # Documento de tipo factura
            "DocType": "dDocument_Items",  # Factura de ítems
            "Series": "76",  # Ajusta según la serie que quieras usar
            "U_Tipti_Orden": orden,               
            "DocDate": DocDate,  # Ajusta según el índice de la fecha
            "NumAtCard": factura.NumAtCard,  # Ajusta según el índice del número de tarjeta
            "SalesPersonCode": -1,  # Vendedor (ajustar según sea necesario)
            "PaymentGroupCode": 1,  # Grupo de pago
            "Comments": "",  # Comentarios
            "JrnlMemo": "",  # Memorando de la factura
            "U_HBT_PTO_EST": factura.Serie,  # Ajusta según el índice de 'Establecimiento'
            "U_HBT_SER_EST": factura.Establecimiento,  # Ajusta según el índice de 'Serie'
            "U_HBT_AUT_FAC": factura.Secuencial,  # Ajusta según el índice de 'Autorizacion'
            "DocumentLines": lineas_factura
        }

        return (orden, billnumber), factura_json
    
    def agrupar_facturas(self, facturas):
        facturas_agrupadas = defaultdict(list)
        processed_orders = set()  # Para asegurarse de que las facturas no se procesen varias veces

        with ThreadPoolExecutor(max_workers=10) as executor:
            # Enviar cada factura a la función `procesar_factura` en los hilos
            futuros = {executor.submit(self.procesar_factura, factura, facturas): factura for factura in facturas}

            for futuro in as_completed(futuros):
                clave, factura_json = futuro.result()

                # Asegurarse de no procesar la misma orden más de una vez
                if clave not in processed_orders:
                    processed_orders.add(clave)  # Marcar esta orden como procesada
                    facturas_agrupadas[clave].append(factura_json)

        return facturas_agrupadas

    def crear_factura(self, factura_json,secuencial):
        if not self.session_id:
            if not self.obtener_session():
                return None
        
        print(json.dumps(factura_json, indent=4)) 
        
        url = f"{self.service_layer_url}Invoices"
        headers = {
            "Content-Type": "application/json",
            "Cookie": f"B1SESSION={self.session_id}; ROUTEID=.node0"
        }
        
        response = requests.post(url, headers=headers, data=json.dumps(factura_json), verify=False)
        
        if response.status_code == 201:
            print(f"Factura procesada: {factura_json['CardCode']}")
            
            # Extraer el número de orden para actualizar las tablas
            orden = factura_json.get("U_Tipti_Orden")  
            if orden:
                self.actualizar_estado_factura(orden,secuencial)
        else:
            print(f"Error procesando factura: {response.text}")
            # Extraer el número de orden para actualizar las tablas
            orden = factura_json.get("U_Tipti_Orden")  
            NumAtCard= factura_json.get("NumAtCard")
            data=json.dumps(factura_json)
            if orden:
                self.actualizar_estado_factura_error(orden,secuencial)
            insertar_errores(self,orden,NumAtCard,response.text,data)
            

    def actualizar_estado_factura(self, orden,secuencial):
        """Actualiza los campos U_Procesado en HBT_CABECERA y U_Tipti_Estado_Lineas en HBT_LINEAS"""
        try:
            orden = str(orden)
            secuencial = next(iter(secuencial))
            #print(orden)
            #print(secuencial)
            connection_string = f'DSN={self.DNS};UID={self.user};PWD={self.password};'
            conn = pyodbc.connect(connection_string)
            cursor = conn.cursor()

           # Actualizar la tabla @HBT_CABECERA
            query_cabecera = """
                UPDATE "{0}"."@HBT_CABECERA"
                SET "U_Procesado" = 'S'
                WHERE "U_Tipti_Orden" = ?
                and "U_Tipti_BillNumber" = ?
            """.format(self.company_db)
            
            #print(query_cabecera)
            cursor.execute(query_cabecera, (orden,secuencial))
           
            # Verificar cuántas filas fueron afectadas
            """rows_affected = cursor.rowcount
            if rows_affected > 0:
                print(f"Consulta ejecutada correctamente. Se actualizaron {rows_affected} registros.")
            else:
                print("La consulta no afectó ningún registro.")"""


            # Actualizar la tabla @HBT_LINEAS
            query_lineas = """
                UPDATE "{0}"."@HBT_LINEAS"
                SET "U_Tipti_Estado_Lineas" = 'S'
                WHERE "U_Tipti_Order" = ?
                and "U_Tipti_Secuencial"= ?
            """.format(self.company_db)

            #print(query_lineas)
            cursor.execute(query_lineas, (orden,secuencial))
            

            # Confirmar cambios en la base de datos
            conn.commit()
            print(f"Orden {orden} actualizada correctamente en @HBT_CABECERA y @HBT_LINEAS.")

            # Cerrar conexión
            cursor.close()
            conn.close()

        except Exception as e:
            print(f"Error al actualizar la orden {orden}: {str(e)}")
    
    def actualizar_estado_factura_error(self, orden,secuencial):
        """Actualiza los campos U_Procesado en HBT_CABECERA y U_Tipti_Estado_Lineas en HBT_LINEAS"""
        try:
            orden = str(orden)
            secuencial = next(iter(secuencial))
            #print(orden)
            #print(secuencial)
            connection_string = f'DSN={self.DNS};UID={self.user};PWD={self.password};'
            conn = pyodbc.connect(connection_string)
            cursor = conn.cursor()

           # Actualizar la tabla @HBT_CABECERA
            query_cabecera = """
                UPDATE "{0}"."@HBT_CABECERA"
                SET "U_Procesado" = 'E'
                WHERE "U_Tipti_Orden" = ?
                and "U_Tipti_BillNumber" = ?
            """.format(self.company_db)
            
           #print(query_cabecera)
            cursor.execute(query_cabecera, (orden,secuencial))
           
            # Verificar cuántas filas fueron afectadas
            """rows_affected = cursor.rowcount
            if rows_affected > 0:
                print(f"Consulta ejecutada correctamente. Se actualizaron {rows_affected} registros.")
            else:
                print("La consulta no afectó ningún registro.")"""


            # Actualizar la tabla @HBT_LINEAS
            query_lineas = """
                UPDATE "{0}"."@HBT_LINEAS"
                SET "U_Tipti_Estado_Lineas" = 'E'
                WHERE "U_Tipti_Order" = ?
                and "U_Tipti_Secuencial"= ?
            """.format(self.company_db)

            #print(query_lineas)
            cursor.execute(query_lineas, (orden,secuencial))
            

            # Confirmar cambios en la base de datos
            conn.commit()
            print(f"Orden {orden} actualizada correctamente en @HBT_CABECERA y @HBT_LINEAS.")

            # Cerrar conexión
            cursor.close()
            conn.close()

        except Exception as e:
            print(f"Error al actualizar la orden {orden}: {str(e)}")

    def obtener_Pagos(self):
        # Establecer conexión ODBC para obtener los ítems
        connection_string = f'DSN={self.DNS};UID={self.user};PWD={self.password};'
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()

        # Ejecutar la consulta para obtener los ítems
        consulta = f"SELECT * FROM {self.company_db}.{self.vista4}"  # Ajusta según la tabla de ítems que tengas
        cursor.execute(consulta)
        pagos = cursor.fetchall()
        
        conn.close()
        return pagos
    
    def crear_Pago(self, pagos,id,orden,billnumber):
        if not self.session_id:
            if not self.obtener_session():
                return None

        pago_data = {
            "CardCode": pagos.CardCode,
            "PaymentInvoices": [
                {
                    "DocEntry": pagos.DocEntry,  
                    "SumApplied": float(pagos.U_Tipti_Amount)
                }
            ],
            "PaymentCreditCards": [
                {
                    "CreditCard": pagos.CodigoTC,
                    "CreditCardNumber": pagos.CardNum,
                    "CardValidUntil": pagos.FechaTC,
                    "VoucherNum": "1429",
                    "CreditSum": float(pagos.U_Tipti_Amount)
                }
            ],
            "Remarks":pagos.Remark
        }
        #print(pago_data)
        #print(json.dumps(pago_data, indent=4))
        url = f"{self.service_layer_url}IncomingPayments"
        headers = {
            "Content-Type": "application/json",
            "Cookie": f"B1SESSION={self.session_id}; ROUTEID=.node0"
        }

        try:
            # Realizar la solicitud POST para crear el ítem
            response = requests.post(url, json=pago_data, headers=headers, verify=False, timeout=30)
            if response.status_code == 201:
                print(f"Pago creado con éxito, Código: {response.json()['DocNum']}")
                self.actualizar_estado_pago(id,orden,billnumber)

            else:
                print(f"Error al crear el ítem. Código de error: {response.status_code}")
                print(f"Detalles del error: {response.text}")
                self.actualizar_estado_pago_error(id,orden,billnumber)
        except Exception as e:
            print(f"Error al realizar la solicitud: {e}")
    
    def actualizar_estado_pago(self,id,orden,secuencial):
        """Actualiza los campos U_Procesado en Pagos"""
        try:
            orden = str(orden)
            #secuencial = next(iter(secuencial))
            #print("Orden estado"+ orden)
            #print("Secuencial"+ secuencial)
            #print("Id:"+ id)
            connection_string = f'DSN={self.DNS};UID={self.user};PWD={self.password};'
            conn = pyodbc.connect(connection_string)
            cursor = conn.cursor()

           # Actualizar la tabla @HBT_CABECERA
            query_pagos = """
                UPDATE "{0}"."@TIPTI_PAGOS"
                SET "U_Tipti_Estado_Pagos"= 'S'
                WHERE "U_Tipti_Orden" = ?
                AND "U_Tipti_BillNumber" = ?
                AND "U_Tipti_ID_interno" = ?
            """.format(self.company_db)
            
            #print(query_pagos)
            cursor.execute(query_pagos, (orden,secuencial,id))
            # Confirmar cambios en la base de datos
            conn.commit()
            print(f"Pago {id} actualizada correctamente")
            # Cerrar conexión
            cursor.close()
            conn.close()

        except Exception as e:
            print(f"Error al actualizar el pago {id}: {str(e)}")

    def actualizar_estado_pago_error(self,id,orden,secuencial):
        """Actualiza los campos U_Procesado en HBT_CABECERA y U_Tipti_Estado_Lineas en HBT_LINEAS"""
        try:
            orden = str(orden)
            #secuencial = next(iter(secuencial))
            #print(orden)
            #print(secuencial)
            connection_string = f'DSN={self.DNS};UID={self.user};PWD={self.password};'
            conn = pyodbc.connect(connection_string)
            cursor = conn.cursor()

           # Actualizar la tabla @HBT_CABECERA
            query_pagos = """
                UPDATE "{0}"."@TIPTI_PAGOS"
                SET "U_Tipti_Estado_Pagos" = 'E'
                WHERE "U_Tipti_Orden" = ?
                AND "U_Tipti_BillNumber" = ?
                AND "U_Tipti_ID_interno" = ?
            """.format(self.company_db)
            
            #print(query_pagos)
            cursor.execute(query_pagos, (orden,secuencial,id))
            # Confirmar cambios en la base de datos
            conn.commit()
            print(f"Pago {id} actualizada correctamente")
            # Cerrar conexión
            cursor.close()
            conn.close()

        except Exception as e:
            print(f"Error al actualizar el pago {id}: {str(e)}")

    # Función para convertir Decimal a float
    def decimal_default(obj):
        if isinstance(obj, Decimal):
            return float(obj)
        raise TypeError("Type not serializable")
    
# Instancia de SAPBusinessOne
sap = SAPBusinessOne(config_file='config.json')


# Función para registrar ítems en paralelo usando el pool de hilos
def registrar_pagos():
    Pagos = sap.obtener_Pagos()
    with ThreadPoolExecutor(max_workers=10) as executor:  # Limita el número de hilos concurrentes
        for pago in Pagos:
            print(f"Registrando pago: {pago.U_Tipti_ID_interno} ({pago.U_Tipti_Orden})")
            id=pago.U_Tipti_ID_interno
            orden=pago.U_Tipti_Orden
            billnumber=pago.U_Tipti_BillNumber
            executor.submit(sap.crear_Pago, pago,id,orden,billnumber)

def insertar_errores(self, order,billnumber,respuesta,json):
    # Verificar si la sesión está activa antes de la operación
        if not self.session_id:
            print("No se ha obtenido una sesión válida.")
            if not self.obtener_session():  # Si no hay sesión, intenta obtenerla
                print("No se pudo obtener la sesión.")
                return None

        url = f"{self.service_layer_url}U_TIPTI_ERRORES_FC"  # URL para los pagos (ajústalo según tu API)
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



from concurrent.futures import ThreadPoolExecutor, as_completed

# Función para registrar socios de negocios en paralelo usando el pool de hilos
def registrar_socios():
    socios = sap.obtener_socios_de_negocios()
    with ThreadPoolExecutor(max_workers=10) as executor:  # Limita el número de hilos concurrentes
        futures = []
        for socio in socios:
            print(f"Registrando socio de negocios: {socio.CardName} ({socio.LicTradNum})")
            future = executor.submit(sap.crear_socio, socio)
            futures.append((future, socio.LicTradNum))  # Guardar la referencia al futuro y el socio
        # Esperamos a que todos los socios se registren
        for future, lic_trad_num in futures:
            future.result()  # Esperar a que cada socio sea creado
            socios_creados.add(lic_trad_num)  # Marcar el socio como creado

# Función para registrar ítems en paralelo usando el pool de hilos
def registrar_items():
    items = sap.obtener_items()
    with ThreadPoolExecutor(max_workers=10) as executor:  # Limita el número de hilos concurrentes
        futures = []
        for item in items:
            print(f"Registrando ítem: {item.ItemName} ({item.ItemCode})")
            future = executor.submit(sap.crear_item, item)
            futures.append((future, item.ItemCode))  # Guardar la referencia al futuro y el item
        # Esperamos a que todos los ítems se registren
        for future, item_code in futures:
            future.result()  # Esperar a que cada ítem sea creado
            items_creados.add(item_code)  # Marcar el ítem como creado

# Función para registrar facturas con control de ejecución usando un deque
def registrar_facturas():
    # Obtener las facturas
    facturas = sap.obtener_Facturas()

    if facturas:
        print(f"Procesando {len(facturas)} nuevas facturas.")
        facturas_agrupadas = sap.agrupar_facturas(facturas)
        
        # Agregar las facturas agrupadas a la cola
        for clave, facturas_json in facturas_agrupadas.items():
            facturas_queue.append((clave, facturas_json))  # Añadir a la cola de tareas

        # Procesar las facturas en cola
        while facturas_queue:
            clave, facturas_json = facturas_queue.popleft()  # Obtener la siguiente factura de la cola
            print(f"Procesando facturas para Orden: {clave[0]}, BillNumber: {clave[1]}")
            secuencial = {clave[1]}

            # Verificar que todos los socios de negocios e ítems estén creados
            for factura_json in facturas_json:
                socio_card_code = factura_json["CardCode"]
                item_code = factura_json["DocumentLines"][0]["ItemCode"]

                # Verificar que el socio de negocios y el ítem existan
                if socio_card_code not in socios_creados or item_code not in items_creados:
                    # Esperar a que el socio de negocios y el ítem estén creados
                    print(f"Esperando a que el socio de negocios {socio_card_code} y el ítem {item_code} sean creados.")
                    continue  # Volver a intentar la factura más tarde

                # Procesar la factura si ya están creados los dependientes
                threading.Thread(target=sap.crear_factura, args=(factura_json, secuencial)).start()

        return True  # Se procesaron facturas
    else:
        return False  # No se procesaron facturas




def main():
    while True:
        # Registrar socios de negocios de manera concurrente
        print("Iniciando el registro de socios de negocios...")
        registrar_socios()  # Ya utiliza ThreadPoolExecutor

        # Registrar ítems de manera concurrente
        print("Iniciando el registro de ítems...")
        registrar_items()  # Ya utiliza ThreadPoolExecutor

        # Esperar que los registros de socios e ítems se completen antes de continuar
        print("Esperando a que los socios e ítems sean registrados...")
        time.sleep(10)  # Puede ajustar este tiempo de espera según sea necesario

        # Intentar registrar facturas, esperando que socios e ítems ya estén procesados
        print("Intentando registrar facturas...")
        facturas_procesadas = registrar_facturas()
        
        # Si no se registraron facturas, esperar un poco y seguir
        if not facturas_procesadas:
            print("Esperando 3 minutos antes de procesar nuevas facturas...")
            time.sleep(180)  # Espera 3 minutos antes de volver a intentar registrar facturas

        # Registrar pagos
        print("Iniciando el registro de pagos...")
        registrar_pagos()

        # Esperar un tiempo (por ejemplo, 3 minutos) antes de continuar con el próximo ciclo
        print("Esperando 3 minutos antes de procesar nuevamente...")
        time.sleep(180)  # 180 segundos = 3 minutos
   

if __name__ == "__main__":
    main()
