#from pipes import quote
import subprocess
from clases.conexiones import Conexiones
import json
import tkinter as tk
from tkinter import filedialog
import subprocess
import pandas as pd
from tkinter import messagebox
from decimal import Decimal, InvalidOperation
from datetime import datetime, timedelta, date
import requests
import chardet
from tkinter import ttk
import threading
import logging
import os
from collections import defaultdict
import time
from itertools import groupby
from operator import itemgetter
requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)

session_id = None
marcas_tarjeta = []

log_dir = 'logs'
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

log_filename = os.path.join(log_dir, 'log.log')
logging.basicConfig(filename=log_filename, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
#log_filenameSL = 'log_SAP/log.log'
#logging.basicConfig(filename=log_filenameSL, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

registrosNoProcesados = []

def abrir_explorador():
    # Ruta de la carpeta que deseas abrir en el explorador de archivos
    ruta_carpeta = "logs\Pendiente"
    # Construir el comando para abrir el explorador de archivos
    comando = "explorer {}".format(ruta_carpeta)  # En Windows
    # Ejecutar el comando
    subprocess.run(comando, shell=True)
    




###################
#CLASES
###################

# GUARDAR EL EXCEL QUE SE VA A LEER CON LOS CAMPOS CORRESPONDIENTES     
class RegistroExcel:
    def __init__(self, Fecha, Referencia, ReferenciaBancaria, TC_MARCA, ValorBruto, Comision, IvaCompras, IVA, FUENTE, RefRetencion, Pago, Banco, Ruc, NombreSN, TipoComprobante, Establecimiento, PtoEmision, Referencia1, AutorizacionFac, Comentario):
        self.Fecha = Fecha
        self.Referencia = Referencia
        self.ReferenciaBancaria = ReferenciaBancaria
        self.TC_MARCA = TC_MARCA
        self.ValorBruto = ValorBruto
        self.Comision = Comision
        self.IvaCompras = IvaCompras
        self.IVA = IVA
        self.FUENTE = FUENTE
        self.RefRetencion = RefRetencion
        self.Pago = Pago
        self.Banco = Banco
        self.Ruc = Ruc
        self.NombreSN = NombreSN
        self.TipoComprobante = TipoComprobante
        self.Establecimiento = Establecimiento
        self.PtoEmision = PtoEmision
        self.Referencia1 = Referencia1
        self.AutorizacionFac = AutorizacionFac
        self.Comentario = Comentario
       
        
    def to_dict(self):
        return {
            'Fecha': self.Fecha,
            'Referencia': self.Referencia,
            'ReferenciaBancaria': self.ReferenciaBancaria,
            'TC_MARCA': self.TC_MARCA,
            'ValorBruto': self.ValorBruto,
            'Comision': self.Comision,
            'IvaCompras': self.IvaCompras,
            'IVA': self.IVA,
            'FUENTE': self.FUENTE,
            'RefRetencion': self.RefRetencion,
            'Pago': self.Pago,
            'Banco': self.Banco,
            'Ruc': self.Ruc,
            'NombreSN': self.NombreSN,
            'TipoComprobante': self.TipoComprobante,
            'Establecimiento': self.Establecimiento,
            'PtoEmision': self.PtoEmision,
            'Referencia1': self.Referencia1,
            'AutorizacionFac': self.AutorizacionFac,
            'Comentario': self.Comentario
        }



class RegistroExcel1:
    def __init__(self, Fecha, Referencia, ReferenciaBancaria, TC_MARCA, ValorBruto, Comision, IVA, FUENTE, Pago, Banco):
        self.Fecha = Fecha
        self.Referencia = Referencia
        self.ReferenciaBancaria = ReferenciaBancaria
        self.TC_MARCA = TC_MARCA
        self.ValorBruto = ValorBruto
        self.Comision = Comision
        self.IVA = IVA
        self.FUENTE = FUENTE
        self.Pago = Pago
        self.Banco = Banco
        
    def to_dict(self):
        return {
            'Fecha': self.Fecha,
            'Referencia': self.Referencia,
            'ReferenciaBancaria': self.ReferenciaBancaria,
            'TC_MARCA': self.TC_MARCA,
            'ValorBruto': self.ValorBruto,
            'Comision': self.Comision,
            'IVA': self.IVA,
            'FUENTE': self.FUENTE,
            'Pago': self.Pago,
            'Banco': self.Banco
        }
# Abrir ventana para seleccionar archivo Excel
def abrir_archivo():
    global archivo
    archivo = filedialog.askopenfilename(filetypes=[("Archivos Excel", "*.xlsx;*.xls")])
 

# Configuraciones desde el archivo config.json
def cargar_configuracion():
    try:
        with open('config.json', 'r') as archivo_config:
            configuracion = json.load(archivo_config)
        return configuracion
    except FileNotFoundError:
        print("El archivo de configuración 'config.json' no se encontró.")
        return None
    

def es_comprobante_pago_valido(valor):
    valor_cadena = str(valor)
    
    if pd.isna(valor) or valor_cadena.lower() == 'nan' or valor is None or valor_cadena.strip() == '':
        return False
    valor_cadena = valor_cadena.split('.')[0]
    return valor_cadena

def cerrar_session_SL():
    
    config = cargar_configuracion()

    if config:
        db_host = config["Configuracion"]["host"]
        db_port = config["Configuracion"]["port"]
        db_user = config["Configuracion"]["user"]
        db_password = config["Configuracion"]["password"]
        db_name = config["Configuracion"]["database_name"]
        db_userSAP = config["Configuracion"]["userSAP"]
        db_passwordSAP = config["Configuracion"]["passSAP"]
        

    # URL del servicio web
    url = "https://"+db_host+":50000/b1s/v1/Logout"
    try:
        # Realizar la solicitud POST deshabilitando la verificación SSL
        response = requests.post(url, verify=False)
        
    except Exception as e:
        #messagebox.showerror("Error", "Error al realizar la conexión: " + str(e))
        logging.exception("Error: ")

def convert_date(date):
    if isinstance(date, str):
        return pd.to_datetime(date, format='%d/%m/%Y').strftime('%Y-%m-%d')
    elif isinstance(date, datetime):
        return date.strftime('%Y-%m-%d')
    else:
        return date
    
def validar_formato_PR(progreso):
    global registrosNoProcesados
    registrosNoProcesados = []
    
    if 'archivo' not in globals():
        messagebox.showerror("Error", "Por favor, selecciona un archivo Excel primero.")
        return
    config = cargar_configuracion()
    sesion_Id = validar_conexionSL()
    #print(config)
    if sesion_Id is not None:  
        cerrar_session_SL()
        try:
            if config:
                # Acceder a las configuraciones
                db_host = config["Configuracion"]["host"]
                db_port = config["Configuracion"]["port"]
                db_user = config["Configuracion"]["user"]
                db_password = config["Configuracion"]["password"]
                db_name = config["Configuracion"]["database_name"]
                db_DNS = config["Configuracion"]["dns"]
                HOJA1 = config["Configuracion"]["HOJA1"]
                Comentario2 = config["Configuracion"]["ComentarioDeposito"]        
                CuentaComision = config["Configuracion"]["CuentaComision"]
                CuentaImpuestoIVA = config["Configuracion"]["CuentaImpuestoIVA"]
                CuentaImpuestoFUENTE = config["Configuracion"]["CuentaImpuestoFUENTE"]
                CuentaIvaCompras = config["Configuracion"]["CuentaIvaCompras"]
                CuentaComisionTC = config["Configuracion"]["CuentaComisionTC"]
                ItemCode= config["Configuracion"]["ItemCode"]
                IndicadorImpuesto=config["Configuracion"]["IndicadorImpuesto"]
                Series = config["Configuracion"]["Series"] 
                SeriesRB = config["Configuracion"]["SeriesRB"] 
                CodigoRetencion = config["Configuracion"]["CodigoRetencion"] 
                TC = config["Configuracion"]["Tarjetas"]
                Plantilla_Fecha = config["Configuracion"]["Plantilla_Fecha"]
                Plantilla_Referencia = config["Configuracion"]["Plantilla_Referencia"]
                Plantilla_ReferenciaBancaria = config["Configuracion"]["Plantilla_ReferenciaBancaria"]
                Plantilla_TC_MARCA = config["Configuracion"]["Plantilla_TC/MARCA"]
                Plantilla_ValorBruto = config["Configuracion"]["Plantilla_ValorBruto"]
                Plantilla_Comision = config["Configuracion"]["Plantilla_Comision"]
                Plantilla_IvaCompras = config["Configuracion"]["Plantilla_IvaCompras"]
                Plantilla_IVA = config["Configuracion"]["Plantilla_IVA"]
                Plantilla_FUENTE = config["Configuracion"]["Plantilla_FUENTE"]  
                Platilla_RefRetencion = config["Configuracion"]["Platilla_RefRetencion"]
                Plantilla_Pago = config["Configuracion"]["Plantilla_Pago"]
                Plantilla_Banco = config["Configuracion"]["Plantilla_Banco"]
                Plantilla_Ruc = config["Configuracion"]["Plantilla_Ruc"]  # Ruc
                Plantilla_NombreSN = config["Configuracion"]["Plantilla_NombreSN"]  # Nombre del socio de negocio
                Plantilla_TipoComprobante = config["Configuracion"]["Plantilla_TipoComprobante"]  # Tipo de comprobante
                Plantilla_Establecimiento = config["Configuracion"]["Plantilla_Establecimiento"]  # Establecimiento
                Plantilla_PtoEmision = config["Configuracion"]["Plantilla_PtoEmision"]  # Punto de emisión
                Plantilla_Referencia1 = config["Configuracion"]["Plantilla_Referencia1"] # Referencia1
                Plantilla_AutorizacionFac = config["Configuracion"]["Plantilla_AutorizacionFac"]  # Autorización de factura
                Plantilla_Comentario = config["Configuracion"]["Plantilla_Comentario"]  # Comentario

                BancoGeneralRuminahui = config["Configuracion"]["RucBancoGeneralRuminahui"]
                BancoBolivariano = config["Configuracion"]["RucBancoBolivariano"]
                BancoPichincha = config["Configuracion"]["RucBancoPichincha"]
                BancoDelAustro = config["Configuracion"]["RucBancoDelAustro"]
                BancoGuayaquil = config["Configuracion"]["RucBancoGuayaquil"]
                BancoInternacional = config["Configuracion"]["RucBancoInternacional"]
                BancoCentralDelEcuador = config["Configuracion"]["RucBancoCentralDelEcuador"]
                Produbanco = config["Configuracion"]["RucProdubanco"]
                BancoDinersClub = config["Configuracion"]["RucBancoDinersClub"]
                BancoDelPacifico = config["Configuracion"]["RucBancoDelPacifico"]



                
        except Exception as e:
            print("¡Error!", e)
        #Conexión a la base de datos (cadena de conexión)
        connection_string = f"DSN={db_DNS};UID={db_user};PWD={db_password}"
        
        depositos_pendientes = 0
        depositos_creados = 0
        depositos_fallidos = 0
        
        asiento_pendientes = 0
        asiento_creados = 0
        asiento_fallidos = 0
        
        try:
            
            columns_mapping = {
                "Fecha": Plantilla_Fecha,
                "Referencia": Plantilla_Referencia,
                "Referencia Bancaria": Plantilla_ReferenciaBancaria,
                "TC/MARCA": Plantilla_TC_MARCA,
                "Valor Bruto": Plantilla_ValorBruto,
                "Comision": Plantilla_Comision,
                "IvaCompras": Plantilla_IvaCompras,
                "IVA": Plantilla_IVA,
                "Fuente": Plantilla_FUENTE,
                "RefRetencion": Platilla_RefRetencion,
                "Pago": Plantilla_Pago,
                "Banco": Plantilla_Banco,
                "Ruc": Plantilla_Ruc,  # RUC
                "Nombre del socio de negocio": Plantilla_NombreSN,  # Nombre del socio de negocio
                "Tipo de comprobante": Plantilla_TipoComprobante,  # Tipo de comprobante
                "Establecimiento": Plantilla_Establecimiento,  # Establecimiento
                "Punto de emisión": Plantilla_PtoEmision,  # Punto de emisión
                "Referencia1": Plantilla_Referencia1,  # Referencia1
                "Autorización de factura": Plantilla_AutorizacionFac,  # Autorización de factura
                "Comentario": Plantilla_Comentario  # Comentario
            }

            

            
            df = pd.read_excel(archivo, sheet_name=HOJA1, usecols=list(columns_mapping.values())) 
            df.columns = list(columns_mapping.keys()) 
            df['Valor Bruto'] = pd.to_numeric(df['Valor Bruto'], errors='coerce').fillna(0)
            df['IVA'] = pd.to_numeric(df['IVA'], errors='coerce').fillna(0)
            df['Fuente'] = pd.to_numeric(df['Fuente'], errors='coerce').fillna(0)
            df['Comision'] = pd.to_numeric(df['Comision'], errors='coerce').fillna(0)
            df['Pago'] = pd.to_numeric(df['Pago'], errors='coerce').fillna(0)
            df['Fecha'] = df['Fecha'].apply(convert_date)
            #print(df.head())
            registros = [
                RegistroExcel(
                    Fecha=row['Fecha'],
                    Referencia=row['Referencia'],
                    ReferenciaBancaria=row['Referencia Bancaria'],
                    TC_MARCA=row['TC/MARCA'],
                    ValorBruto=row['Valor Bruto'],
                    Comision=row['Comision'],
                    IvaCompras=row['IvaCompras'],
                    IVA=row['IVA'],
                    FUENTE=row['Fuente'],
                    RefRetencion=row['RefRetencion'],
                    Pago=row['Pago'],
                    Banco=row['Banco'],
                    Ruc=row['Ruc'],  # Nuevo campo RUC
                    NombreSN=row['Nombre del socio de negocio'],  # Nuevo campo Nombre del socio de negocio
                    TipoComprobante=row['Tipo de comprobante'],  # Nuevo campo Tipo de comprobante
                    Establecimiento=row['Establecimiento'],  # Nuevo campo Establecimiento
                    PtoEmision=row['Punto de emisión'],  # Nuevo campo Punto de emisión
                    Referencia1=row['Referencia1'],  # Nuevo campo Referencia1
                    AutorizacionFac=row['Autorización de factura'],  # Nuevo campo Autorización de factura
                    Comentario=row['Comentario']  # Nuevo campo Comentario
                ) for _, row in df.iterrows() 
            ]
            
        


            """for i, registro in enumerate(registros, 1):
                    print(f"Registro {i}:")
                    print(f"  Fecha: {registro.Fecha}")
                    print(f"  Referencia: {registro.Referencia}")
                    print(f"  Referencia Bancaria: {registro.ReferenciaBancaria}")
                    print(f"  TC/MARCA: {registro.TC_MARCA}")
                    print(f"  Valor Bruto: {registro.ValorBruto}")
                    print(f"  Comision: {registro.Comision}")
                    print(f"  IvaCompras: {registro.IvaCompras}")
                    print(f"  IVA: {registro.IVA}")
                    print(f"  Fuente: {registro.FUENTE}")
                    print(f"  RefRetencion: {registro.RefRetencion}")
                    print(f"  Pago: {registro.Pago}")
                    print(f"  Banco: {registro.Banco}")
                    print(f"  Ruc: {registro.Ruc}")  # Nuevo campo Ruc
                    print(f"  Nombre del socio de negocio: {registro.NombreSN}")  # Nuevo campo NombreSN
                    print(f"  Tipo de comprobante: {registro.TipoComprobante}")  # Nuevo campo Tipo de comprobante
                    print(f"  Establecimiento: {registro.Establecimiento}")  # Nuevo campo Establecimiento
                    print(f"  Punto de emisión: {registro.PtoEmision}")  # Nuevo campo Punto de emisión
                    print(f"  Referencia1: {registro.Referencia1}")  # Nuevo campo Referencia1
                    print(f"  Autorización de factura: {registro.AutorizacionFac}")  # Nuevo campo AutorizacionFac
                    print(f"  Comentario: {registro.Comentario}")  # Nuevo campo Comentario
                    print()  # Espacio para separar los registros"""
            
            for i, registro in enumerate(registros, 1):
                    print(f"  Referencia1: {registro.Referencia1}")  # Nuevo campo Referencia1
                    #print(f"El tipo de dato es: {type(registro.Referencia1)} y el valor es: {registro.Referencia1}")
                    print()  # Espacio para separar los registros

            registro_dict = {registro.Referencia: registro.to_dict() for registro in registros}
            json_registros = json.dumps(registro_dict, indent=4)
            #print("registro dict")
            #print(json_registros)
          
            registro_dict_ordenado = sorted(registro_dict.values(), key=itemgetter('ReferenciaBancaria'))
            json_registros2= json.dumps(registro_dict_ordenado, indent=4)
            #print(json_registros2)

            # Convertir la lista a un DataFrame de pandas
            df = pd.DataFrame(registro_dict_ordenado)
            # Agrupar por 'ReferenciaBancaria'
            grouped = df.groupby('ReferenciaBancaria')

            max=0
            for ref, group in grouped:
             max+=1
            
            sesion_Id = validar_conexionSL()
            progreso['maximum'] = max
            total_registros_procesados=0
            # Iterar sobre los grupos e imprimir cada grupo
            for ref1, group in grouped:
                ref = int(ref1) if pd.notna(ref) else 0 
                print(f"Referencia Bancaria: {ref}")
                referencias = group['Referencia'].tolist()

                # Inicializa los acumuladores fuera del bucle interno
                docnums_en_resultados = set()
                docnums_en_resultados2 = set()
                docnums_en_resultados3 = set()

                # Acumulador para resultados dentro del grupo
                resultados_grupo = []

                # Iterar sobre cada registro en el grupo
                for _, row in group.iterrows():
                    # Obtener solo el campo 'Referencia'
                    referencia = row['Referencia']
                    
                    # Llamar a la función enviando solo la referencia y acumular los resultados en el grupo
                    resultados = obtener_depositos_1a1(referencia, sesion_Id)
                    resultados_grupo.extend(resultados)  # Acumular todos los resultados en la lista del grupo
                    
                    print(f"Resultados de obtener_depositos_1a1: {resultados}")
                    
                    # Actualizar los conjuntos con los resultados obtenidos
                    docnums_en_resultados.update({str(resultado['VoucherNum']) for resultado in resultados})
                    docnums_en_resultados2.update({str(resultado['U_HBT_N_AUT']) for resultado in resultados})
                    docnums_en_resultados3.update({str(resultado['DocNum']) for resultado in resultados})

                # Obtenemos los registros que no se procesan y mandarlos al log
                pagos_no_en_resultados = [
                    reg for _, reg in group.iterrows()
                    if (str(reg.Referencia) not in docnums_en_resultados) and
                    (str(reg.Referencia) not in docnums_en_resultados2) and
                    (str(reg.Referencia) not in docnums_en_resultados3)
                ]

                # Verificar si existen registros sin depósitos pendientes
                if len(pagos_no_en_resultados) > 0:
                    print(f"No se procesarán registros de la Referencia Bancaria: {ref}, debido a que hay registros sin depósito pendiente.")
                    
                    # Crear la subcarpeta si no existe
                    subcarpeta = "logs/Pendiente"
                    if not os.path.exists(subcarpeta):
                        os.makedirs(subcarpeta)
                    
                    # Generar el nombre del archivo con la fecha y hora actual
                    fecha_hora_actual = datetime.now().strftime('%Y%m%d_%H%M%S')
                    nombre_archivo = f'NoProcesados_{ref}_{fecha_hora_actual}.xlsx'
                    ruta_excel = os.path.join(subcarpeta, nombre_archivo)
                    
                    # Convertir los registros no procesados a una lista de diccionarios
                    pagos_no_en_resultados_dicts = [reg.to_dict() for reg in pagos_no_en_resultados]
                    
                    # Crear el DataFrame 'df_final' a partir de la lista de diccionarios
                    df_final = pd.DataFrame(pagos_no_en_resultados_dicts)
                    df_final["Observación"] = "No existe pago recibido o ya fue depositado"
                    df_final.rename(columns={'Referencia': 'Autorización'}, inplace=True)
                    
                    # Guardar el DataFrame en un archivo Excel
                    df_final.to_excel(ruta_excel, index=False)
                    print(f"Archivo Excel generado en: {ruta_excel}")
                    mensaje = f"Revisar logs: Existen pagos sin procesar Referencia Bancaria: {ref}"
                    mostrar_mensaje_temporal(mensaje)
                
                else:
                    
                    # Se crea una lista de todos los pagos que pertenecen a esa tarjeta de crédito
                    combinados = []

                    # Transformación explícita de las claves del diccionario a cadenas 
                    registro_dict = {str(k): v for k, v in registro_dict.items()}
                    
                    # Iterar sobre los resultados acumulados en el grupo
                    for resultado in resultados_grupo:
                        conf_num = resultado.get('VoucherNum')
                        num_auto = resultado.get('U_HBT_N_AUT')
                        doc_num = resultado.get('DocNum')

                        # Verificar y combinar usando las referencias
                        referenciaA = str(num_auto) if num_auto is not None else None
                        referenciaB = str(conf_num) if conf_num is not None else None
                        referenciaC = str(doc_num) if doc_num is not None else None

                        # Crear una lista de todas las referencias posibles para buscar en el registro_dict
                        referencias_a_buscar = [referenciaB, referenciaA, referenciaC]

                        # Inicializamos 'combinado' como None
                        combinado = None

                        # Iterar sobre las referencias para encontrar coincidencias en registro_dict
                        for referencia in referencias_a_buscar:
                            if referencia and referencia in registro_dict:
                                #print(f"Combinar con referencia: {referencia}")
                                if combinado:
                                    # Combinar el resultado actual con los registros previos en 'combinado'
                                    combinado.update(registro_dict[referencia])
                                else:
                                    # Inicializar combinado si aún no tiene un valor
                                    combinado = {**resultado, **registro_dict[referencia]}

                        # Si se encontró una combinación válida, agregarla a la lista combinados
                        if combinado:
                            print(f"Agregando combinado: {combinado}")
                            combinados.append(combinado)

                    # Imprimir los combinados
                    """print("Combinados finales:")
                    for CreditAcct in combinados:
                        print(CreditAcct['ReferenciaBancaria'])"""



                    fecha_actual = datetime.now()
                    fecha_formateada = fecha_actual.strftime('%Y-%m-%d')

                    if combinados:
                            depositos_pendientes += 1
                            asiento_pendientes += 1 
                            primer_registro = combinados[0]
                            credit_acct = primer_registro['CreditAcct'] 

                            # Crear asiento de reclasificación
                            data = pd.DataFrame(combinados)
                            # Acceder al valor máximo de la columna 'Banco'
                            max_banco = int(data['Banco'].max())  # Acceder directamente a la columna 'Banco' Ruc
                            max_credit = data['CreditAcct'].max()
                            max_fecha = data['Fecha'].astype(str).max()
                            max_comentario=data['Comentario'].astype(str).max()
                            max_ReferenciaBancaria = data['ReferenciaBancaria'].astype(str).max()
                            # Asegurarte de que 'Referencia1' siempre tenga 9 dígitos
                            data.loc[data['Referencia1'].notnull(), 'Referencia1'] = data['Referencia1'].astype(str).str.zfill(9)

                            #data['Referencia1'] = data['Referencia1'].astype(str).str.zfill(9)

                            ref_max_str=data['Referencia1'].max()
                            #print(ref_max_str)
                            # Verificar si el valor máximo es válido antes de convertir a entero
                            if ref_max_str != 'nan':  # Si no es NaN
                                ref3 = ref_max_str  # Primero convierto a float, luego a int
                            else:
                                ref3 = 0 
                            
                            suma_valor_iva_compras = round(data['IvaCompras'].sum(), 2)
                            RefRetencion = data['RefRetencion'].astype(str).max()
                            
                            
                            # Sumarizar los valores de 'Total', 'Comision', 'Valor Retencion IVA', y 'Valor Retencion Fuente'
                            suma_total = round(data['ValorBruto'].sum(), 2)
                            total= round(data['ValorBruto'], 2)
                            suma_comision = round(data['Comision'].sum(), 2)
                            suma_valor_retencion_iva = round(data['IVA'].sum(), 2)
                            suma_valor_retencion_fuente = round(data['FUENTE'].sum(), 2)
                         
                            
                            # Lista de columnas específicas que deseas verificar
                            columnas_a_verificar = ['Fecha', 'Referencia', 'ReferenciaBancaria', 'TC_MARCA', 'ValorBruto', 'Comision', 'IvaCompras', 'IVA', 'FUENTE', 'RefRetencion', 'Pago', 'Banco', 'Ruc', 'NombreSN', 'TipoComprobante', 'Establecimiento', 'PtoEmision', 'Referencia1', 'AutorizacionFac']
                            columnas_a_verificar2= ['IvaCompras','Ruc', 'NombreSN', 'TipoComprobante', 'Establecimiento', 'PtoEmision', 'Referencia1', 'AutorizacionFac']
                           
                            # Verificar si hay valores NaN en las columnas específicas
                            if data[columnas_a_verificar2].isna().all().all():
                                print("SI ENTRO")
                                journal_entry_lines = []
                                journal_entry_lines.append({
                                        "AccountCode": str(max_banco),
                                        "Debit": float(round(suma_total - suma_comision - suma_valor_retencion_iva - suma_valor_retencion_fuente-suma_valor_iva_compras, 2)),
                                        "Reference1":'',
                                        "Reference2": max_ReferenciaBancaria,
                                        "AdditionalReference": ''
                                    })
                                
                                if suma_comision > 0:
                                    journal_entry_lines.append({
                                        "AccountCode": str(CuentaComision),
                                        "Debit": float(round(suma_comision, 2)),
                                        "Reference1": '',
                                        "Reference2": '',
                                        "AdditionalReference": ''
                                    })

                                if suma_valor_retencion_iva > 0:
                                    journal_entry_lines.append({
                                        "AccountCode": str(CuentaImpuestoIVA),
                                        "Debit": float(round(suma_valor_retencion_iva, 2)),
                                        "Reference1": '',
                                        "Reference2": '',
                                        "AdditionalReference": ''
                                    })
                                
                                if suma_valor_retencion_fuente > 0:
                                    journal_entry_lines.append({
                                        "AccountCode": str(CuentaImpuestoFUENTE),
                                        "Debit": float(round(suma_valor_retencion_fuente, 2)),
                                        "Reference1": '',
                                        "Reference2": '',
                                        "AdditionalReference": ''
                                    })

                                    
                                # Crear un diccionario para almacenar los valores agrupados por 'CreditAcct'
                                agrupados = defaultdict(float)

                                # Recorrer los elementos en combinados y sumar los valores para los mismos 'CreditAcct'
                                for CreditAcct in combinados:
                                    agrupados[CreditAcct['CreditAcct']] += float(CreditAcct['ValorBruto'])

                                # Crear las líneas de entrada de diario basadas en los 'CreditAcct' agrupados
                                for acct, total_bruto in agrupados.items():
                                    journal_entry_lines.append({
                                        "AccountCode": str(acct),
                                        "Credit": total_bruto,
                                        "Reference1": '',
                                        "Reference2": '',
                                        "AdditionalReference": ''
                                    })
                                # Estructura final del asiento contable
                                estructura = {
                                    "Reference": max_ReferenciaBancaria,  
                                    "Reference2": max_ReferenciaBancaria,  
                                    "Reference3": max_ReferenciaBancaria,  
                                    "TaxDate": max_fecha,
                                    "DueDate": max_fecha,
                                    "ReferenceDate": max_fecha,
                                    "TransactionCode":"LIQT",
                                    "Memo": max_comentario,
                                    "JournalEntryLines": journal_entry_lines
                                }
                                
                                print("Asiento a crear:")
                                cadena_json = json.dumps(estructura, indent=4)  
                                print(cadena_json)
                                resultadoAS = crearAsiento(estructura,sesion_Id)
                                
                                #Creación de Depósito
                                if resultadoAS:
                                    asiento_creados += 1
                                
                                    agrupacion_completa = defaultdict(lambda: {"AbsIds": defaultdict(list), "CreditAcct": {}})

                                    # Iterar sobre el arreglo combinados
                                    for CreditAcct in combinados:
                                        referencia_bancaria = CreditAcct['ReferenciaBancaria']
                                        marca = CreditAcct['TC_MARCA']
                                        abs_id = CreditAcct['AbsId']
                                        cuenta_credito = CreditAcct['CreditAcct']  # Obtener CreditAcct
                                        
                                        # Agregar el AbsId bajo la referencia bancaria y la marca
                                        agrupacion_completa[referencia_bancaria]["AbsIds"][marca].append(abs_id)
                                        
                                        # Guardar el CreditAcct asociado a la marca
                                        agrupacion_completa[referencia_bancaria]["CreditAcct"][marca] = cuenta_credito

                                    # Imprimir el resultado agrupado por Referencia Bancaria y TC_MARCA
                                    for referencia_bancaria, data1 in agrupacion_completa.items():
                                        print(f"Referencia Bancaria: {referencia_bancaria}")
                                        for marca, abs_ids in data1["AbsIds"].items():
                                            credit_acct = data1["CreditAcct"][marca]  # Obtener el CreditAcct asociado a la marca
                                            print(f"  Marca: {marca} - AbsIds: {abs_ids} - CreditAcct: {credit_acct}")

                                            # Crear la estructura JSON para cada combinación de referencia bancaria y marca
                                            estructura_json = {
                                                "DepositType": "dtCredit",
                                                "DepositDate": fecha_formateada,
                                                "DepositAccount": credit_acct,  # Usamos el CreditAcct por marca
                                                "BankReference": resultadoAS,
                                                "VoucherAccount": credit_acct,  # Usamos el CreditAcct por marca
                                                "Series": Series,
                                                "CreditLines": [{"AbsId": abs_id} for abs_id in abs_ids]  # Crear las CreditLines con los AbsIds
                                            }
                                            
                                            # Convertir a JSON con indentación para mejor legibilidad
                                            json_str = json.dumps(estructura_json, indent=4)
                                            print("Deposito a crear:")
                                            print(json_str)
                                            resultadoDep = crearDeposito(estructura_json,sesion_Id)
                                            if resultadoDep:
                                                depositos_creados += 1
                                                #messagebox.showinfo("Resultado", f"Proceso finalizado")
                                            else:
                                                depositos_fallidos += 1
                                else:
                                    depositos_fallidos += 1  
                                    asiento_fallidos += 1
                                mensaje = f"Procesamiento finalizado \nReferencia Bancaria: {max_ReferenciaBancaria}"
                                #messagebox.showerror("Error", mensaje)
                                mostrar_mensaje_temporal(mensaje)
                            elif data[columnas_a_verificar].isna().any().any():
                                ######### NO SE GENERA FACTURA #########
                                mensaje = f"Hay campos vacios no se puede realizar la factura de comisiones: {max_ReferenciaBancaria}"
                                #messagebox.showerror("Error", mensaje)
                                mostrar_mensaje_temporal(mensaje)
                                #mensaje = f"Procesamiento finalizado \nReferencia Bancaria: {max_ReferenciaBancaria}"
                                #messagebox.showerror("Error", mensaje)
                                #mostrar_mensaje_temporal(mensaje)

                                # Lista de columnas que deseas guardar
                                columnas_a_guardar = [
                                'Fecha', 
                                'Referencia', 
                                'ReferenciaBancaria', 
                                'TC_MARCA', 
                                'ValorBruto', 
                                'Comision', 
                                'IvaCompras', 
                                'IVA', 
                                'FUENTE', 
                                'RefRetencion', 
                                'Pago', 
                                'Banco', 
                                'Ruc', 
                                'NombreSN', 
                                'TipoComprobante', 
                                'Establecimiento', 
                                'PtoEmision', 
                                'Referencia1', 
                                'AutorizacionFac', 
                                'Comentario'
                            ]

                                # Luego puedes usar esta lista para filtrar el DataFrame y guardar solo esas columnas
                                df_guardar = data[columnas_a_guardar]  # Filtras solo las columnas que te interesan
                                # Crear subcarpeta "logs/Pendiente" si no existe
                                subcarpeta = "logs/Pendiente"
                                if not os.path.exists(subcarpeta):
                                    os.makedirs(subcarpeta)

                                # Generar nombre del archivo con la fecha y hora actual
                                fecha_hora_actual = datetime.now().strftime('%Y%m%d_%H%M%S')
                                nombre_archivo = f'NoProcesados_{max_ReferenciaBancaria}_{fecha_hora_actual}.xlsx'
                                ruta_excel = os.path.join(subcarpeta, nombre_archivo)

                                # Agregar una columna de observación
                                df_guardar["Observación"] = "Existen campos incompletos en una o más líneas"

                                # Guardar el DataFrame filtrado en un archivo Excel
                                df_guardar.to_excel(ruta_excel, index=False)
                                print(f"Archivo Excel generado en: {ruta_excel}")

                                # Mostrar mensaje de que existen pagos sin procesar
                                mensaje = f"Revisar logs: Existen campos incompletos en una o más líneas {max_ReferenciaBancaria}"
                                mostrar_mensaje_temporal(mensaje)
        
                            else :
                                
                                
                                journal_entry_lines = []
                            
                                journal_entry_lines.append({
                                    "AccountCode": str(max_banco),
                                    "Debit": float(round(suma_total - suma_comision - suma_valor_retencion_iva - suma_valor_retencion_fuente-suma_valor_iva_compras, 2)),
                                    "Reference1":'',
                                    "Reference2": max_ReferenciaBancaria,
                                    "AdditionalReference": ''
                                })

                                suma_total_comision= float(round(suma_comision, 2))+float(round(suma_valor_iva_compras, 2))
                                
                                if suma_comision > 0:
                                    journal_entry_lines.append({
                                        "AccountCode": str(CuentaComision),
                                        "Debit":suma_total_comision ,
                                        "Reference1": str(int(float(ref3))).zfill(9),
                                        "Reference2": '',
                                        "AdditionalReference": ''
                                    })
                            
                                if suma_valor_retencion_iva > 0:
                                    journal_entry_lines.append({
                                        "AccountCode": str(CuentaImpuestoIVA),
                                        "Debit": float(round(suma_valor_retencion_iva, 2)),
                                        "Reference1": '',
                                        "Reference2": '',
                                        "AdditionalReference": RefRetencion
                                    })
                                
                                if suma_valor_retencion_fuente > 0:
                                    journal_entry_lines.append({
                                        "AccountCode": str(CuentaImpuestoFUENTE),
                                        "Debit": float(round(suma_valor_retencion_fuente, 2)),
                                        "Reference1": '',
                                        "Reference2": '',
                                        "AdditionalReference": RefRetencion
                                    })

                                
                                
                                # Crear un diccionario para almacenar los valores agrupados por 'CreditAcct'
                                agrupados = defaultdict(float)

                                # Recorrer los elementos en combinados y sumar los valores para los mismos 'CreditAcct'
                                for CreditAcct in combinados:
                                    agrupados[CreditAcct['CreditAcct']] += float(CreditAcct['ValorBruto'])

                                # Crear las líneas de entrada de diario basadas en los 'CreditAcct' agrupados
                                for acct, total_bruto in agrupados.items():
                                    journal_entry_lines.append({
                                        "AccountCode": str(acct),
                                        "Credit": total_bruto,
                                        "Reference1": '',
                                        "Reference2": '',
                                        "AdditionalReference": ''
                                    })
                                
                                """for CreditAcct in combinados:

                                    journal_entry_lines.append({
                                        "AccountCode": str(CreditAcct['CreditAcct']),
                                        "Credit": float(CreditAcct['ValorBruto']),
                                        "Reference1": '',
                                        "Reference2": '',
                                        "AdditionalReference": ''
                                    })"""

                                """print("Contenido de journal_entry_lines:")
                                for line in journal_entry_lines:
                                    print(line)"""
                                
                                # Estructura final del asiento contable
                                estructura = {
                                    "Reference": str(int(float(ref3))).zfill(9),  
                                    "Reference2": max_ReferenciaBancaria,  
                                    "Reference3": RefRetencion,  
                                    "TaxDate": max_fecha,
                                    "DueDate": max_fecha,
                                    "ReferenceDate": max_fecha,
                                    "TransactionCode":"LIQT",
                                    "Memo": max_comentario,
                                    "JournalEntryLines": journal_entry_lines
                                }
                                
                                print("Asiento a crear:")
                                cadena_json = json.dumps(estructura, indent=4)  
                                print(cadena_json)
                                resultadoAS = crearAsiento(estructura,sesion_Id)
                                
                                #Creación de Depósito
                                if resultadoAS:
                                    asiento_creados += 1
                                
                                    agrupacion_completa = defaultdict(lambda: {"AbsIds": defaultdict(list), "CreditAcct": {}})

                                    # Iterar sobre el arreglo combinados
                                    for CreditAcct in combinados:
                                        referencia_bancaria = CreditAcct['ReferenciaBancaria']
                                        marca = CreditAcct['TC_MARCA']
                                        abs_id = CreditAcct['AbsId']
                                        cuenta_credito = CreditAcct['CreditAcct']  # Obtener CreditAcct
                                        
                                        # Agregar el AbsId bajo la referencia bancaria y la marca
                                        agrupacion_completa[referencia_bancaria]["AbsIds"][marca].append(abs_id)
                                        
                                        # Guardar el CreditAcct asociado a la marca
                                        agrupacion_completa[referencia_bancaria]["CreditAcct"][marca] = cuenta_credito

                                    # Imprimir el resultado agrupado por Referencia Bancaria y TC_MARCA
                                    for referencia_bancaria, data1 in agrupacion_completa.items():
                                        print(f"Referencia Bancaria: {referencia_bancaria}")
                                        for marca, abs_ids in data1["AbsIds"].items():
                                            credit_acct = data1["CreditAcct"][marca]  # Obtener el CreditAcct asociado a la marca
                                            print(f"  Marca: {marca} - AbsIds: {abs_ids} - CreditAcct: {credit_acct}")

                                            # Crear la estructura JSON para cada combinación de referencia bancaria y marca
                                            estructura_json = {
                                                "DepositType": "dtCredit",
                                                "DepositDate": fecha_formateada,
                                                "DepositAccount": credit_acct,  # Usamos el CreditAcct por marca
                                                "BankReference": resultadoAS,
                                                "VoucherAccount": credit_acct,  # Usamos el CreditAcct por marca
                                                "Series": Series,
                                                "CreditLines": [{"AbsId": abs_id} for abs_id in abs_ids]  # Crear las CreditLines con los AbsIds
                                            }
                                            
                                            # Convertir a JSON con indentación para mejor legibilidad
                                            json_str = json.dumps(estructura_json, indent=4)
                                            print("Deposito a crear:")
                                            print(json_str)
                                            resultadoDep = crearDeposito(estructura_json,sesion_Id)
                                            if resultadoDep:
                                                depositos_creados += 1
                                                #messagebox.showinfo("Resultado", f"Proceso finalizado")
                                            else:
                                                depositos_fallidos += 1
                                else:
                                    depositos_fallidos += 1  
                                    asiento_fallidos += 1
                                

                                #####################FACTURA############################
                                
                                suma_total_IvaC = round(data['Comision'].sum(), 2)
                                impuesto = round(data['IvaCompras'].sum(), 2) 
                                DocTotal= suma_total_IvaC+impuesto
                            
                                ruc=int(data['Ruc'].max())
                                establecimiento=int(data['Establecimiento'].max())
                                punto_emision=int(data['PtoEmision'].max())
                                autorización=int(data['AutorizacionFac'].max())
                                tipo_comprobante=int(data['TipoComprobante'].max())
                                print(ruc)
                                SN=ConsultarProveedor(ruc,sesion_Id)


                                if SN:
                                    print("================================== Factura de proveedores  ================================== ")
                                    
                                    documentsLines=[]
                                    documentsLines.append({
                                        "ItemCode": ItemCode,
                                        "Quantity": "1",
                                        "TaxCode": IndicadorImpuesto,
                                        "UnitPrice": float(round(suma_total_IvaC, 2))
                                    })
                                    
                                    
                                    """Factura = []
                                    Factura.append({
                                        "CardCode": "PN1790368718001",
                                        "DocumentLines": documentsLines
                                    })"""

                                    FacturaProv={
                                        "CardCode": SN,
                                        "Series":SeriesRB,
                                        "NumAtCard": str(int(float(ref3))).zfill(9),
                                        "DocumentLines": documentsLines,
                                        "DocTotal":DocTotal,
                                        "U_HBT_FP":20, 
                                        "U_TRP_APL_CCH": "NO",
                                        "U_HBT_TIP_COMP": tipo_comprobante,
                                        "U_HBT_SER_EST": establecimiento,
                                        "U_HBT_PTO_EST": punto_emision,
                                        "U_HBT_AUT_FAC": autorización,
                                        "WithholdingTaxDataCollection": [
                                            {
                                                "WTCode": CodigoRetencion
                                                
                                            }
                                        ]
                                    }
                                    #Solo imprimir el formato de la factura
                                    cadena_json2 = json.dumps(FacturaProv, indent=4)  
                                    print(cadena_json2)
                                    Docentry= crearFactura(FacturaProv,sesion_Id)
                                    print(Docentry)
                                    print("========================== Pago ============================")

                                    pago={
                                        "CardCode": SN,
                                        "PaymentInvoices": [
                                            {
                                                "DocEntry": Docentry,
                                                "SumApplied": DocTotal
                                                
                                            }
                                        ],
                                        
                                        "CashAccount": CuentaComisionTC,
                                        "CashSum": DocTotal
                                    }
                                    crearPago(pago,sesion_Id)

                                    mensaje = f"Procesamiento finalizado \nReferencia Bancaria: {max_ReferenciaBancaria}"
                                    #messagebox.showerror("Error", mensaje)
                                    mostrar_mensaje_temporal(mensaje)
                                    
                                else:
                                    print("No se encontro un socio de negocios en SAP para realizar la factura de proveedores")
                                     
                total_registros_procesados += 1 
                progreso['value'] = total_registros_procesados  # Actualiza la barra de progreso
                progreso.update_idletasks()

            progreso['value'] = 0
            time.sleep(2.5)
            messagebox.showinfo("Resultado", f"Proceso finalizado")
        
        except Exception as e:
            messagebox.showerror("Error", "Error: " + str(e))
            logging.exception("Error: ")




def obtener_depositos_1a1(Referencia,id):
    print(Referencia)

    global registrosNoProcesados
    config = cargar_configuracion()
    if not config:
        print("No se pudo cargar la configuración.")
        return None

    db_host = config["Configuracion"]["host"]
    port = config["Configuracion"]["port"]
    
    # Iniciar sesión en el Service Layer para obtener la sesión
    sesion_Id = id
    if not sesion_Id:
        print("No se pudo validar la sesión.")
        return None
    
    headers = {
        "Cookie": f"B1SESSION={sesion_Id}; ROUTEID=.node0",
        "Content-Type": "application/json"  # Asegurándonos de enviar el Content-Type correcto
    }
    

    resultados = []
    lista_general = []
    
 
    if str(Referencia).isdigit():
        print("El valor solo tiene números.")
        url = f"https://{db_host}:{port}/b1s/v1/SQLQueries('DepositoSC3')/List?ref='{Referencia}'"

    else:
        print("El valor contiene letras o caracteres no numéricos.")
        url = f"https://{db_host}:{port}/b1s/v1/SQLQueries('DepositoSC5')/List?ref='{Referencia}'"
        
    print(url)
                
        # Realizar la solicitud GET
    try:
            response = requests.get(url, headers=headers, verify=False)
            if response.status_code == 200:

                data = response.json()
                resultados = data.get('value', [])
                lista_resultados = [resultado for resultado in resultados]
                
                if data.get("value", []):
                    abs_id = data["value"][0]["AbsId"]
                else:
                    abs_id = None  
                    
                if abs_id:
                    #print(abs_id)
                    resultados.append(abs_id)  
                    lista_general.append(resultados[0])
                   # print(lista_general)
                #if codigos:
                    #print(f"Códigos de depósitos obtenidos con éxito para {numPago}: {codigos}")
                    #resultados.append()
        
                    #resultados.extend(codigos)
                else:
                    print("No se obtubieron pagos pendientes para deposito")
            else:
                print(response.content)
    except Exception as e:
            print("error:")
    
    cerrar_session_SL()
    
    return lista_general
   

def validar_conexionSL():
    
    config = cargar_configuracion()

    if config:
        db_host = config["Configuracion"]["host"]
        db_port = config["Configuracion"]["port"]
        db_user = config["Configuracion"]["user"]
        db_password = config["Configuracion"]["password"]
        db_name = config["Configuracion"]["database_name"]
        db_userSAP = config["Configuracion"]["userSAP"]
        db_passwordSAP = config["Configuracion"]["passSAP"]
        
    
    cuerpo = {
        "CompanyDB": db_name,
        "Password": db_passwordSAP,
        "UserName": db_userSAP
    }

    # URL del servicio web
    url = "https://"+db_host+":50000/b1s/v1/Login"
    try:
        # Realizar la solicitud POST deshabilitando la verificación SSL
        response = requests.post(url, json=cuerpo, verify=False)

        if response.status_code == 200:
            session_id = response.json().get('SessionId')
            print("Conexión exitosa Service Layer. SessionId:", session_id)
            return session_id
        else:
            #messagebox.showerror("Error", "Error en la conexión al servicio web. Código de estado: " + str(response.status_code))
            mensaje = "Error en la conexión al servicio web. Código de estado: " + str(response.content)
            logging.exception(mensaje)
            return None
    except Exception as e:
        #messagebox.showerror("Error", "Error al realizar la conexión: " + str(e))
        logging.exception("Error: ")
        return None

def crearDeposito(deposito,sesion_Id2):
    
    config = cargar_configuracion()

    if config:
        # Acceder a las configuraciones
        db_host = config["Configuracion"]["host"]
        db_port = config["Configuracion"]["port"]
        
    # URL del servicio web
    url = f"https://{db_host}:{db_port}/b1s/v1/Deposits"
    

    sesion_Id = sesion_Id2

    headers = {
        "Cookie": f"B1SESSION={sesion_Id}; ROUTEID=.node0" 
    }
    if sesion_Id is not None:
        try:
            
            response = requests.post(url, json=deposito, headers=headers, verify=False) 

            if response.status_code == 201:
                #messagebox.showinfo("Creación Exitosa", "Deposito creado")
                print("Deposito creado")
                cerrar_session_SL()
                return True
            else:
                #messagebox.showerror("Error", "No se ha creado el deposito")
                print("Error al crear Deposito:")
                print(response.content)
                mensaje = "Error: " + str(response.content)
                logging.exception(mensaje)
                
                cerrar_session_SL()
                return False
        except Exception as e:
            print("Error:" + str(e))
            #messagebox.showerror("Error", "No se ha creado el deposito: " + str(e))
            logging.exception("Error: ")
            cerrar_session_SL()
            return False
        
    else:
        #messagebox.showerror("Error", "No se ha podido conectar HANA")
        return False

def crearAsiento(deposito,id):
    global registrosNoProcesados
    config = cargar_configuracion()

    if config:
        # Acceder a las configuraciones
        db_host = config["Configuracion"]["host"]
        db_port = config["Configuracion"]["port"]
        db_user = config["Configuracion"]["user"]
        db_password = config["Configuracion"]["password"]
        db_name = config["Configuracion"]["database_name"]
        db_userSAP = config["Configuracion"]["userSAP"]
        db_passwordSAP = config["Configuracion"]["passSAP"]
    # URL del servicio web
    url = "https://"+db_host+":50000/b1s/v1/JournalEntries"
    print(url)
    

    sesion_Id = id

    headers = {
        "Cookie": f"B1SESSION={sesion_Id}; ROUTEID=.node0" 
    }
    if sesion_Id is not None:
        try:
            
            response = requests.post(url, json=deposito, headers=headers, verify=False) 
            print(response)

            if response.status_code == 201:
                #messagebox.showinfo("Creación Exitosa", "Asiento creado")
                data = response.json()
                jdt_num = data.get('JdtNum')
                print("Asiento creado")
                cerrar_session_SL()
                return jdt_num
            else:
                #messagebox.showerror("Error", "No se ha creado el asiento")
                print("Error al crear Asiento:")
                print(response.content)
                mensaje = "Error: " + str(response.content)
                logging.exception(mensaje)
                
                cerrar_session_SL()
                return False
        except Exception as e:
            print("Error:" + str(e))
            #messagebox.showerror("Error", "No se ha creado el asiento: " + str(e))
            logging.exception("Error: ")
            cerrar_session_SL()
            return False
        
    else:
        #messagebox.showerror("Error", "No se ha podido conectar HANA")
        return False


def crearFactura(factura,id):
    global registrosNoProcesados
    config = cargar_configuracion()

    if config:
        # Acceder a las configuraciones
        db_host = config["Configuracion"]["host"]
        db_port = config["Configuracion"]["port"]
        db_user = config["Configuracion"]["user"]
        db_password = config["Configuracion"]["password"]
        db_name = config["Configuracion"]["database_name"]
        db_userSAP = config["Configuracion"]["userSAP"]
        db_passwordSAP = config["Configuracion"]["passSAP"]
    # URL del servicio web
    url = "https://"+db_host+":50000/b1s/v1/PurchaseInvoices"
    print(url)

    sesion_Id = id

    headers = {
        "Cookie": f"B1SESSION={sesion_Id}; ROUTEID=.node0" 
    }
    if sesion_Id is not None:
        try:
            
            response = requests.post(url, json=factura, headers=headers, verify=False) 
            print(response)

            if response.status_code == 201:
                #messagebox.showinfo("Creación Exitosa", "Asiento creado")
                data = response.json()
                #print(data)
                DocEntry = data.get('DocEntry')
                #print(DocEntry)
                print("Factura creada")
                cerrar_session_SL()
                return DocEntry
            else:
                #messagebox.showerror("Error", "No se ha creado el asiento")
                print("Error al crear factura:")
                print(response.content)
                mensaje = "Error: " + str(response.content)
                logging.exception(mensaje)
                
                cerrar_session_SL()
                return False
        except Exception as e:
            print("Error:" + str(e))
            #messagebox.showerror("Error", "No se ha creado el asiento: " + str(e))
            logging.exception("Error: ")
            cerrar_session_SL()
            return False
        
    else:
        #messagebox.showerror("Error", "No se ha podido conectar HANA")
        return False


def ConsultarProveedor(proveedor,id):
    global registrosNoProcesados
    config = cargar_configuracion()

    if config:
        # Acceder a las configuraciones
        db_host = config["Configuracion"]["host"]
        db_port = config["Configuracion"]["port"]
        db_user = config["Configuracion"]["user"]
        db_password = config["Configuracion"]["password"]
        db_name = config["Configuracion"]["database_name"]
        db_userSAP = config["Configuracion"]["userSAP"]
        db_passwordSAP = config["Configuracion"]["passSAP"]
    # URL del servicio web
    # https://190.95.241.212:50000/b1s/v1/BusinessPartners?$select=CardCode,CardName,CardType&$filter=startswith(FederalTaxID, '1790010937001')and CardType eq 'S'
    # url = "https://"+db_host+":50000/b1s/v1/BusinessPartners?$select=CardCode,CardName,CardType&$filter=startswith(FederalTaxID,'{proveedor}')and CardType eq 'S'"
    url = f"https://{db_host}:50000/b1s/v1/BusinessPartners?$select=CardCode,CardName,CardType&$filter=startswith(FederalTaxID,'{proveedor}') and CardType eq 'S'"
    print(url)

    sesion_Id = id

    headers = {
        "Cookie": f"B1SESSION={sesion_Id}; ROUTEID=.node0" 
    }
    if sesion_Id is not None:
        try:
            
        
            response = requests.get(url, headers=headers, verify=False) 
            print(response)

            if response.status_code == 200:
                #messagebox.showinfo("Creación Exitosa", "Asiento creado")
                data = response.json()
                #print(data)
                CardCode = data['value'][0].get('CardCode')
                #print(CardCode)
                print("SN ENCONTRADO ")
                cerrar_session_SL()
                return CardCode
            else:
                #messagebox.showerror("Error", "No se ha creado el asiento")
                print("SN no encontrado")
                print(response.content)
                mensaje = "Error: " + str(response.content)
                logging.exception(mensaje)
                cerrar_session_SL()
                return False
        except Exception as e:
            print("Error:" + str(e))
            #messagebox.showerror("Error", "No se ha creado el asiento: " + str(e))
            logging.exception("Error: ")
            cerrar_session_SL()
            return False
        
    else:
        #messagebox.showerror("Error", "No se ha podido conectar HANA")
        return False




def crearPago(Pago,id):
    global registrosNoProcesados
    config = cargar_configuracion()

    if config:
        # Acceder a las configuraciones
        db_host = config["Configuracion"]["host"]
        db_port = config["Configuracion"]["port"]
        db_user = config["Configuracion"]["user"]
        db_password = config["Configuracion"]["password"]
        db_name = config["Configuracion"]["database_name"]
        db_userSAP = config["Configuracion"]["userSAP"]
        db_passwordSAP = config["Configuracion"]["passSAP"]
    # URL del servicio web
    url = "https://"+db_host+":50000/b1s/v1/VendorPayments"
    print(url)
    

    sesion_Id = id

    headers = {
        "Cookie": f"B1SESSION={sesion_Id}; ROUTEID=.node0" 
    }
    if sesion_Id is not None:
        try:
            
            response = requests.post(url, json=Pago, headers=headers, verify=False) 
            print(response)

            if response.status_code == 201:
                #messagebox.showinfo("Creación Exitosa", "Asiento creado")
                data = response.json()
                jdt_num = data.get('JdtNum')
                print("Pago realizado exitosamnte")
                cerrar_session_SL()
                return jdt_num
            else:
                #messagebox.showerror("Error", "No se ha creado el asiento")
                print("Error al realizar el pago:")
                print(response.content)
                mensaje = "Error: " + str(response.content)
                logging.exception(mensaje)           
                cerrar_session_SL()
                return False
        except Exception as e:
            print("Error:" + str(e))
            #messagebox.showerror("Error", "No se ha creado el asiento: " + str(e))
            logging.exception("Error: ")
            cerrar_session_SL()
            return False
        
    else:
        #messagebox.showerror("Error", "No se ha podido conectar HANA")
        return False



def verificar_campos_vacios_en_grupo(grupo, columnas):
    for _, row in grupo.iterrows():
        if any(pd.isna(row[col]) or str(row[col]).strip() == '' for col in columnas):
            print(f"Advertencia: El grupo con 'Referencia Bancaria' {row['Referencia Bancaria']} contiene registros con campos vacíos.")
            return True
    return False

# Crear la ventana principal
ventana = tk.Tk()
ventana.title("SAP")

# Obtener las dimensiones de la pantalla
ancho_pantalla = ventana.winfo_screenwidth()
alto_pantalla = ventana.winfo_screenheight()

# Definir el tamaño de la ventana
ancho_ventana = 230
alto_ventana = 200

# Ancho deseado para los botones
ancho_botones = 20

# Calcular la posición para centrar la ventana
x = (ancho_pantalla // 2) - (ancho_ventana // 2)
y = (alto_pantalla // 2) - (alto_ventana // 2)

# Establecer la geometría de la ventana
ventana.geometry(f"{ancho_ventana}x{alto_ventana}+{x}+{y}")
# Botón 1: Abrir archivo
btn_abrir = tk.Button(ventana, text="Seleccionar Archivo", command=abrir_archivo, width=ancho_botones)
btn_abrir.pack(pady=10)

# Botón 2: Validar líneas
btn_validar = tk.Button(ventana, text="Procesar Depositos", command=lambda: validar_formato_PR(progreso), width=ancho_botones)
btn_validar.pack(pady=10)
btn_validar.pack(pady=10)


btn_abrir_explorador = tk.Button(ventana, text="Abrir Logs", command=abrir_explorador, width=ancho_botones)
btn_abrir_explorador.pack(pady=10)

# Barra de progreso
longitud_progreso = ancho_ventana - 20  # Ajustar la longitud al ancho de la ventana menos un margen
progreso = ttk.Progressbar(ventana, orient="horizontal", length=longitud_progreso, mode="determinate")
progreso.pack(pady=15)

def mostrar_mensaje_temporal(mensaje, ventana_principal=ventana, duracion=2000):
    def cerrar_ventana():
        ventana.destroy()

    ventana = tk.Toplevel(ventana_principal)
    ventana.title("Mensaje")

    ancho_ventana = 200
    alto_ventana = 100
    ventana.geometry(f"{ancho_ventana}x{alto_ventana}")

    # Obtener la geometría de la ventana principal
    x_ventana_principal = ventana_principal.winfo_x()
    y_ventana_principal = ventana_principal.winfo_y()
    ancho_ventana_principal = ventana_principal.winfo_width()
    alto_ventana_principal = ventana_principal.winfo_height()

    # Calcular la posición para centrar la ventana emergente
    x = x_ventana_principal + (ancho_ventana_principal // 2) - (ancho_ventana // 2)
    y = y_ventana_principal + (alto_ventana_principal // 2) - (alto_ventana // 2)

    ventana.geometry(f"{ancho_ventana}x{alto_ventana}+{x}+{y}")

    label_mensaje = tk.Label(ventana, text=mensaje, wraplength=ancho_ventana - 20, justify="center", padx=10, pady=10)
    label_mensaje.pack(expand=True)

    ventana.update()  # Forzar actualización de la ventana antes de cerrar
    ventana.after(duracion, cerrar_ventana)  # Cierra la ventana después de la duración especificada


ventana.mainloop()
