import requests
import json

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

    def actualizar_articulo(self, item_code):
        if not self.session_id:
            if not self.obtener_session():
                return None

        # Datos a actualizar en el artículo
        update_data = {
            "PurchaseItem": "tYES",
            "ItemsGroupCode":111,
            "SalesItem": "tYES",
            "InventoryItem": "tNO"
        }

        url = f"{self.service_layer_url}Items('{item_code}')"
        headers = {
            "Content-Type": "application/json",
            "Cookie": f"B1SESSION={self.session_id}; ROUTEID=.node0"
        }

        try:
            # Realizar la solicitud PATCH para actualizar el artículo
            response = requests.patch(url, json=update_data, headers=headers, verify=False, timeout=30)
            if response.status_code == 204:
                print(f"Artículo {item_code} actualizado con éxito.")
            else:
                print(f"Error al actualizar el artículo {item_code}. Código de error: {response.status_code}")
                print(f"Detalles del error: {response.text}")
        except Exception as e:
            print(f"Error al realizar la solicitud para el artículo {item_code}: {e}")

    def actualizar_articulos(self, item_codes):
        for item_code in item_codes:
            self.actualizar_articulo(item_code)


# Listado de códigos de artículos a actualizar
item_codes = [
    "01011080854322", "01011080775356", "01011080897926", "0101108043701",
    "0101108008541", "01011080900462", "010110801090385", "01011080846824",
    "0101108035872", "01011080897927", "0101108023987", "0101108012358",
    "0101108017292", "0101108002769", "0101108017326", "0101108020790",
    "0101108037123", "0101108002331", "0101108012853", "0101108006102",
    "0101108000195", "0101108012928", "0101108013259", "0101108003542",
    "0101108001281", "0101108006346", "0101108009811", "0101108006248",
    "0101108018695", "0101108019292", "0101108013788", "0101108014835",
    "0101108015016", "0101108018756", "0101108017097", "0101108019187",
    "0101108017192", "0101108022106", "0101108033513", "0101108028116",
    "0101108026654", "0101108033829", "0101108025717", "0101108027848",
    "0101108024964", "0101108027910", "0101108030566", "0101108031667",
    "0101108034321", "0101108043484", "0101108042500", "0101108038846",
    "0101108042539", "0101108035251", "0101108038435", "0101108040519",
    "0101108043162", "0101108036551", "0101108042847", "01011080291272",
    "01011080296127", "01011080778024", "01011080778054", "01011080846825",
    "01011080846826", "01011080318696", "01011080775352", "01011080775353",
    "01011080897786", "01011080900458", "01011080903854", "01011080319100",
    "01011080652340", "01011080450715", "010110801090386", "01011080964483",
    "01011080949326", "010110801011923", "0101108017011", "01011080486345",
    "0101108014778", "0101108035969", "0101108037122", "0101108021055",
    "0101108012434", "0101108029604", "0101108038805", "0101108019241",
    "0101108012964", "0101108023090", "0101108034706", "0101108040612",
    "01011080775334", "0101108028080", "0101108041502"
]

# Instancia de SAPBusinessOne
sap = SAPBusinessOne(config_file='config.json')

# Actualizar los artículos
sap.actualizar_articulos(item_codes)
