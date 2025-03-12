import json
import os
import random
from datetime import datetime, timedelta

# Función para generar datos de facturas aleatorias
def generate_invoice(order_number):
    invoice = {
        "order": order_number,
        "Numero_FacturasCompras": str(random.randint(100000000000000, 999999999999999)),
        "bill_number": f"001-100-00{random.randint(1000000, 9999999)}",
        "authorization_number": f"{random.randint(1000000000000000, 9999999999999999)}",
        "date": (datetime.now() - timedelta(days=random.randint(1, 30))).strftime("%Y-%m-%d %H:%M:%S"),
        "user": {
            "ref": "user@example.com",
            "name": "John Doe",
            "tipticard_id": random.randint(100000, 999999),
            "email": "user@example.com"
        },
        "partner": {
            "name": "John Doe",
            "vat": f"{random.randint(1000000000, 9999999999)}",
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
                "quantity": random.randint(1, 5),
                "product_code": f"0101{random.randint(10000000000000, 99999999999999)}",
                "product_name": "Sample Product",
                "product_description": "Sample Product Description",
                "revenue_source": "PRODUCT",
                "discounts": [
                    {
                        "discount_id": random.randint(10000, 99999),
                        "discount_rate": f"{random.randint(5, 50)}.00",
                        "discount_name": "Sample Discount",
                        "discount_group": "Discount-Group",
                        "amount": f"{random.uniform(1, 10):.2f}"
                    }
                ],
                "tax": "vat15",
                "price_unit": random.uniform(1, 10),
                "price_unit_without_tax": random.uniform(1, 10),
                "margin": "10.00",
                "validate_inventory": True,
                "line_total": random.uniform(10, 100),
                "product_code_secundario": f"0101{random.randint(10000000000000, 99999999999999)}"
            }
        ]
    }
    return invoice

# Directorio donde guardar las facturas
output_dir = "facturas"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Generar y guardar 200 facturas en archivos JSON
for i in range(1, 201):
    invoice_data = generate_invoice(i)
    file_path = os.path.join(output_dir, f"factura_{i}.json")
    
    with open(file_path, 'w') as json_file:
        json.dump(invoice_data, json_file, indent=4)
    print(f"Factura {i} guardada en {file_path}")

print("Generación de facturas completada.")
