using SAPbobsCOM;

class Program
{
    static void Main(string[] args)
    {
        // Conectar al sistema SAP Business One
        Company oCompany = new Company();
        oCompany.Server = "13.92.0.225"; // Nombre del servidor
        oCompany.DbServerType = BoDataServerTypes.dst_MSSQL2012; // Tipo de base de datos
        oCompany.CompanyDB = "SBO_EC_TENA4_01"; // Nombre de la base de datos
        oCompany.UserName = "USUARIO7"; // Usuario SAP
        oCompany.Password = "HYC909"; // Contraseña
        oCompany.Connect();

        // Crear una nueva tabla de usuario
        UserTablesMD oUserTable = (UserTablesMD)oCompany.GetBusinessObject(BoObjectTypes.oUserTables);
        oUserTable.TableName = "CABECERA"; // Nombre de la tabla
        oUserTable.TableDescription = "Tabla de cabecera de orden";
        int result = oUserTable.Add();
        
        if (result != 0)
        {
            Console.WriteLine("Error al crear la tabla: " + oCompany.GetLastErrorDescription());
            return;
        }
        Console.WriteLine("Tabla de usuario creada exitosamente.");

        // Agregar los campos a la tabla
        AddFieldToTable(oCompany, "CABECERA", "Numero_FacturasCompras", BoFieldTypes.db_Alpha, 255);
        AddFieldToTable(oCompany, "CABECERA", "bill_number", BoFieldTypes.db_Alpha, 50);
        AddFieldToTable(oCompany, "CABECERA", "authorization_number", BoFieldTypes.db_Alpha, 255);
        AddFieldToTable(oCompany, "CABECERA", "date", BoFieldTypes.db_Date, 0); // Fecha
        AddFieldToTable(oCompany, "CABECERA", "user_ref", BoFieldTypes.db_Alpha, 255);
        AddFieldToTable(oCompany, "CABECERA", "user_name", BoFieldTypes.db_Alpha, 255);
        AddFieldToTable(oCompany, "CABECERA", "tipticard_id", BoFieldTypes.db_Int, 0); // Entero
        AddFieldToTable(oCompany, "CABECERA", "email", BoFieldTypes.db_Alpha, 255);
        AddFieldToTable(oCompany, "CABECERA", "partner_name", BoFieldTypes.db_Alpha, 255);
        AddFieldToTable(oCompany, "CABECERA", "vat", BoFieldTypes.db_Alpha, 20);
        AddFieldToTable(oCompany, "CABECERA", "vat_type", BoFieldTypes.db_Alpha, 10);
        AddFieldToTable(oCompany, "CABECERA", "street", BoFieldTypes.db_Alpha, 255);
        AddFieldToTable(oCompany, "CABECERA", "phone", BoFieldTypes.db_Alpha, 20);
        AddFieldToTable(oCompany, "CABECERA", "email_partner", BoFieldTypes.db_Alpha, 255);
        AddFieldToTable(oCompany, "CABECERA", "city", BoFieldTypes.db_Alpha, 100);
        AddFieldToTable(oCompany, "CABECERA", "Grupo", BoFieldTypes.db_Alpha, 100);
        AddFieldToTable(oCompany, "CABECERA", "Subcategoria", BoFieldTypes.db_Alpha, 100);
        AddFieldToTable(oCompany, "CABECERA", "purchase_shopper_id", BoFieldTypes.db_Int, 0);
        AddFieldToTable(oCompany, "CABECERA", "purchase_shopper_name", BoFieldTypes.db_Alpha, 255);
        AddFieldToTable(oCompany, "CABECERA", "purchase_shopper_ruc", BoFieldTypes.db_Alpha, 20);
        AddFieldToTable(oCompany, "CABECERA", "purchase_shopper_canal", BoFieldTypes.db_Alpha, 100);
        AddFieldToTable(oCompany, "CABECERA", "delivery_shopper_id", BoFieldTypes.db_Int, 0);
        AddFieldToTable(oCompany, "CABECERA", "delivery_shopper_name", BoFieldTypes.db_Alpha, 255);
        AddFieldToTable(oCompany, "CABECERA", "delivery_shopper_ruc", BoFieldTypes.db_Alpha, 20);
        AddFieldToTable(oCompany, "CABECERA", "delivery_shopper_canal", BoFieldTypes.db_Alpha, 100);
        AddFieldToTable(oCompany, "CABECERA", "retailer_bills", BoFieldTypes.db_Alpha, 1000); // Usando Alpha para CLOB
        AddFieldToTable(oCompany, "CABECERA", "vat_subtotal", BoFieldTypes.db_Float, 0); // DECIMAL
        AddFieldToTable(oCompany, "CABECERA", "amount_total", BoFieldTypes.db_Float, 0); // DECIMAL
        AddFieldToTable(oCompany, "CABECERA", "retailer_name", BoFieldTypes.db_Alpha, 255);
        AddFieldToTable(oCompany, "CABECERA", "retailer_ruc", BoFieldTypes.db_Alpha, 20);
        AddFieldToTable(oCompany, "CABECERA", "retailer_id", BoFieldTypes.db_Int, 0);
        AddFieldToTable(oCompany, "CABECERA", "Ciudad_id", BoFieldTypes.db_Int, 0);
        AddFieldToTable(oCompany, "CABECERA", "Ciudad_desc", BoFieldTypes.db_Alpha, 100);
        AddFieldToTable(oCompany, "CABECERA", "Sector_id", BoFieldTypes.db_Int, 0);
        AddFieldToTable(oCompany, "CABECERA", "Sector_desc", BoFieldTypes.db_Alpha, 100);
        AddFieldToTable(oCompany, "CABECERA", "Tienda_id", BoFieldTypes.db_Int, 0);
        AddFieldToTable(oCompany, "CABECERA", "Tienda_desc", BoFieldTypes.db_Alpha, 100);
        AddFieldToTable(oCompany, "CABECERA", "delivery_city_id", BoFieldTypes.db_Int, 0);
        AddFieldToTable(oCompany, "CABECERA", "delivery_city", BoFieldTypes.db_Alpha, 100);
        AddFieldToTable(oCompany, "CABECERA", "delivery_sector_id", BoFieldTypes.db_Int, 0);
        AddFieldToTable(oCompany, "CABECERA", "delivery_sector", BoFieldTypes.db_Alpha, 100);
        AddFieldToTable(oCompany, "CABECERA", "delivery_address", BoFieldTypes.db_Alpha, 255);

        Console.WriteLine("Todos los campos fueron añadidos exitosamente.");

        // Cerrar la conexión
        oCompany.Disconnect();
    }

    static void AddFieldToTable(Company oCompany, string tableName, string fieldName, BoFieldTypes fieldType, int size)
    {
        UserFieldsMD oUserField = (UserFieldsMD)oCompany.GetBusinessObject(BoObjectTypes.oUserFields);
        oUserField.TableName = tableName;
        oUserField.Name = fieldName;
        oUserField.Description = fieldName;
        oUserField.Type = fieldType;
        oUserField.Size = size;
        int result = oUserField.Add();

        if (result != 0)
        {
            Console.WriteLine($"Error al agregar el campo {fieldName}: " + oCompany.GetLastErrorDescription());
        }
    }
}
