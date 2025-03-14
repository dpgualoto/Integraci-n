import requests
import random
import json
from datetime import datetime

# URL del endpoint
url = "http://127.0.0.1:5000/procesar"

# Función para generar valores aleatorios para el producto, vat, order y bill_number
def generar_valores_aleatorios():
    # Genera un código de producto aleatorio
    product_code = str(random.randint(1000000000000, 9999999999999))

    # Genera un VAT aleatorio
    vat = str(random.randint(1000000000, 9999999999))

    # Genera un número de orden aleatorio
    order = random.randint(100, 200)

    # Genera un número de bill_number aleatorio
    bill_number = f"001-100-{random.randint(100000000, 999999999)}"

    return product_code, vat, order, bill_number

# Estructura base para el JSON
base_json = {
    "order": 74,
    "Numero_FacturasCompras": "230964940159274",
    "bill_number": "001-100-007524249",
    "authorization_number": "6695533609310730",
    "date": "2025-03-12 10:18:39",
    "user": {
        "ref": "user@example.com",
        "name": "John Doe",
        "tipticard_id": 507603,
        "email": "user@example.com"
    },
    "partner": {
        "name": "John Doe",
        "vat": "28593445311",
        "vat_type": "05",
        "street": "123 Main St",
        "phone": "+593 990376052",
        "email": "user@example.com",
        "city": "Quito",
        "Grupo": "B2B",
        "Subcategoria": "Subgrupo B2B"
    },
    "sale_lines": [
        {
            "quantity": 4,
            "product_code": "0101306123846",
            "product_name": "Sample Product",
            "product_description": "Sample Product Description",
            "revenue_source": "PRODUCT",
            "discounts": [
                {
                    "discount_id": 66870,
                    "discount_rate": "31.00",
                    "discount_name": "Sample Discount",
                    "discount_group": "Discount-Group",
                    "amount": "4.84"
                }
            ],
            "tax": "vat15",
            "price_unit": 6.892955152023639,
            "price_unit_without_tax": 3.590135994971847,
            "margin": "10.00",
            "validate_inventory": True,
            "line_total": 30.977618076769648,
            "product_code_secundario": "010175746211774"
        },
        {
            "quantity": 100,
            "product_code": "01013061238",
            "product_name": "Sample Product",
            "product_description": "Sample Product Description",
            "revenue_source": "PRODUCT",
            "discounts": [
                {
                    "discount_id": 66870,
                    "discount_rate": "31.00",
                    "discount_name": "Sample Discount",
                    "discount_group": "Discount-Group",
                    "amount": "4.84"
                }
            ],
            "tax": "vat15",
            "price_unit": 6.892955152023639,
            "price_unit_without_tax": 3.590135994971847,
            "margin": "10.00",
            "validate_inventory": True,
            "line_total": 30.977618076769648,
            "product_code_secundario": "010175746211"
        }
    ],
    "payments": [
        {
            "id_interno": "6233913(1/1)",
            "method": "pymtz",
            "amount": "19.40",
            "date": "2025-12-03",
            "id_externo": "DF-25447131",
            "authorization_code": "973497"
        },
        {
            "id_interno": "6233907(1/1)",
            "method": "tipti",
            "amount": "50",
            "date": "2025-12-03",
            "id_externo": None,
            "authorization_code": None
        }
    ]
}

# Enviar 50 peticiones
for i in range(50):
    # Obtener valores aleatorios para product_code, vat, order y bill_number
    product_code, vat, order, bill_number = generar_valores_aleatorios()

    # Crear una copia del JSON base
    data = base_json.copy()

    # Actualizar los valores de product_code, vat, order y bill_number
    data['sale_lines'][0]['product_code'] = product_code
    data['sale_lines'][1]['product_code'] = product_code
    data['partner']['vat'] = vat
    data['order'] = order
    data['bill_number'] = bill_number

    # Mandar la petición POST
    response = requests.post(url, json=data)
    
    # Imprimir el estado de la respuesta
    if response.status_code == 200:
        print(f"Petición {i+1} enviada correctamente.")
    else:
        print(f"Error al enviar la petición {i+1}. Código de respuesta: {response.status_code}")
