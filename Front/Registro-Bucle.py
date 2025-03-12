import time
from threading import Lock
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
        self.lock = Lock()  # Para sincronizar la modificación de recursos compartidos
        self.executor = ThreadPoolExecutor(max_workers=10)  # Iniciar el pool de hilos

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

    def obtener_Facturas(self):
        # Establecer conexión ODBC para obtener las facturas
        connection_string = f'DSN={self.DNS};UID={self.user};PWD={self.password};'
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()

        # Ejecutar la consulta para obtener las facturas
        consulta = f"SELECT * FROM {self.company_db}.{self.vista3}"
        cursor.execute(consulta)
        facturas = cursor.fetchall()
        conn.close()
        return facturas

    def registrar_socios(self):
        while True:
            socios = self.obtener_socios_de_negocios()
            for socio in socios:
                print(f"Registrando socio de negocios: {socio.CardName} ({socio.LicTradNum})")
                self.executor.submit(self.crear_socio, socio)
            time.sleep(10)  # Espera 10 segundos antes de revisar nuevamente

    def registrar_items(self):
        while True:
            items = self.obtener_items()
            for item in items:
                print(f"Registrando ítem: {item.ItemName} ({item.ItemCode})")
                self.executor.submit(self.crear_item, item)
            time.sleep(10)  # Espera 10 segundos antes de revisar nuevamente

    def registrar_facturas(self):
        while True:
            facturas = self.obtener_Facturas()
            for factura in facturas:
                print(f"Registrando factura: {factura.CardCode} ({factura.DocNum})")
                self.executor.submit(self.crear_factura, factura)
            time.sleep(10)  # Espera 10 segundos antes de revisar nuevamente

# Función principal para ejecutar el proceso continuamente
def main():
    sap = SAPBusinessOne(config_file='config.json')

    # Ejecutar cada uno de los procesos en paralelo
    from threading import Thread

    Thread(target=sap.registrar_socios, daemon=True).start()
    Thread(target=sap.registrar_items, daemon=True).start()
    Thread(target=sap.registrar_facturas, daemon=True).start()

    # Mantener el programa en ejecución
    while True:
        time.sleep(60)  # El programa sigue ejecutándose y revisando en segundo plano

if __name__ == "__main__":
    main()
