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
            if orden:
                self.actualizar_estado_factura_error(orden,secuencial)

    def actualizar_estado_factura(self, orden,secuencial):
        """Actualiza los campos U_Procesado en HBT_CABECERA y U_Tipti_Estado_Lineas en HBT_LINEAS"""
        try:
            orden = str(orden)
            secuencial = next(iter(secuencial))
            print(orden)
            print(secuencial)
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
            
            print(query_cabecera)
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

            print(query_lineas)
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
            print(orden)
            print(secuencial)
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
            
            print(query_cabecera)
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

            print(query_lineas)
            cursor.execute(query_lineas, (orden,secuencial))
            

            # Confirmar cambios en la base de datos
            conn.commit()
            print(f"Orden {orden} actualizada correctamente en @HBT_CABECERA y @HBT_LINEAS.")

            # Cerrar conexión
            cursor.close()
            conn.close()

        except Exception as e:
            print(f"Error al actualizar la orden {orden}: {str(e)}")

# Instancia de SAPBusinessOne
sap = SAPBusinessOne(config_file='config.json')

# Función para registrar socios de negocios en paralelo usando el pool de hilos
def registrar_socios():
    socios = sap.obtener_socios_de_negocios()
    with ThreadPoolExecutor(max_workers=10) as executor:  # Limita el número de hilos concurrentes
        for socio in socios:
            print(f"Registrando socio de negocios: {socio.CardName} ({socio.LicTradNum})")
            executor.submit(sap.crear_socio, socio)

# Función para registrar ítems en paralelo usando el pool de hilos
def registrar_items():
    items = sap.obtener_items()
    with ThreadPoolExecutor(max_workers=10) as executor:  # Limita el número de hilos concurrentes
        for item in items:
            print(f"Registrando ítem: {item.ItemName} ({item.ItemCode})")
            executor.submit(sap.crear_item, item)

# Función para registrar las facturas en paralelo
def registrar_facturas():
    sap = SAPBusinessOne(config_file='config.json')
    facturas = sap.obtener_Facturas()
    facturas_agrupadas = sap.agrupar_facturas(facturas)

    # Procesar las facturas agrupadas
    for clave, facturas_json in facturas_agrupadas.items():
        print(f"Procesando facturas para Orden: {clave[0]}, BillNumber: {clave[1]}")
        secuencial={clave[1]}
        for factura_json in facturas_json:
            # Llamar a la lógica para crear cada factura
            sap.crear_factura(factura_json,secuencial)
# Ejecutar todos los procesos de manera secuencial para evitar errores de dependencias
def main():
    # Registrar socios de negocios
    registrar_socios()

    # Registrar ítems
    registrar_items()

    # Registrar facturas
    registrar_facturas()
   

if __name__ == "__main__":
    main()
