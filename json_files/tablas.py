import pyodbc

# Configura tu conexión ODBC (reemplaza 'YourDSN' con el nombre de tu fuente de datos ODBC)
dsn = 'TIPTI'
user = 'SYSTEM'  # Usuario de SAP
password = 'B1Admin$'  # Contraseña de SAP
database = 'SBO_EC_TENA4_01'  # Nombre de la base de datos

# Conectar a SAP Business One a través de ODBC
connection_string = f'DSN={dsn};UID={user};PWD={password};DATABASE={database}'
conn = pyodbc.connect(connection_string)

# Crear un cursor para ejecutar las consultas
cursor = conn.cursor()

# Crear la tabla de usuario con "order" entre comillas dobles
cursor.execute("""
    CREATE TABLE lineas (
        "order" VARCHAR(50),
        linenum VARCHAR(50),
        quantity VARCHAR(50),
        product_code VARCHAR(50),
        product_name VARCHAR(255),
        product_description VARCHAR(255),
        revenue_source VARCHAR(50),
        category1 VARCHAR(100),
        category2 VARCHAR(100),
        category3 VARCHAR(100),
        category4 VARCHAR(100),
        sequence VARCHAR(50),
        tax VARCHAR(50),
        price_unit VARCHAR(50),
        price_unit_without_tax VARCHAR(50),
        margin VARCHAR(50),
        validate_inventory VARCHAR(1),
        PRIMARY KEY ("order", linenum)
    )
""")

# Confirmar que la tabla fue creada correctamente
conn.commit()

# Cerrar la conexión
cursor.close()
conn.close()

print("Tabla 'lineas' creada exitosamente en SAP Business One.")
