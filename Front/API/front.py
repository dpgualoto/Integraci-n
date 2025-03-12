import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox
import json
import requests

# URL de la API Flask
API_URL = "http://127.0.0.1:5000/procesar"

def cargar_json():
    """Abre un cuadro de diálogo para seleccionar un archivo JSON"""
    archivo = filedialog.askopenfilename(filetypes=[("Archivos JSON", "*.json")])
    if archivo:
        try:
            with open(archivo, "r", encoding="utf-8") as f:
                data = json.load(f)
                text_area.delete(1.0, tk.END)
                # Muestra el contenido cargado en el área de texto
                text_area.insert(tk.END, json.dumps(data, indent=4, ensure_ascii=False))
                btn_enviar.config(state=tk.NORMAL)  # Habilita el botón de enviar
                global json_data
                json_data = data  # Guarda el JSON en memoria para enviarlo más tarde
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar JSON: {str(e)}")


def enviar_json():
    """Envía el JSON a la API Flask y, si el servidor responde correctamente, guarda el resultado en un archivo de texto"""
    try:
        # Intentamos enviar la solicitud con un timeout de 30 segundos
        respuesta = requests.post(API_URL, json=json_data, timeout=30)
        
        if respuesta.status_code == 200:
            try:
                # Intentamos convertir la respuesta a JSON
                resultado = respuesta.json()
                if resultado is None:
                    messagebox.showerror("Error", "La respuesta de la API está vacía o es inválida.")
                else:
                    # Procesar el resultado aquí si es necesario
                    print(resultado)  # Puedes mostrar el resultado en la interfaz si lo deseas
            except ValueError:
                messagebox.showerror("Error", "La respuesta de la API no es un JSON válido.")
        else:
            messagebox.showerror("Error", f"Error en la API: {respuesta.text}")
    except requests.exceptions.Timeout:
        messagebox.showerror("Error", "La solicitud ha superado el tiempo de espera.")
    except requests.exceptions.RequestException as e:
        messagebox.showerror("Error", f"No se pudo conectar con la API: {str(e)}")


# Crear ventana principal
root = tk.Tk()
root.title("Cliente JSON para API Flask")
root.geometry("800x600")

# Botón para cargar JSON
btn_cargar = tk.Button(root, text="Cargar JSON", command=cargar_json)
btn_cargar.pack(pady=5)

# Área de texto para mostrar el JSON cargado
text_area = scrolledtext.ScrolledText(root, height=10, width=80)
text_area.pack(padx=10, pady=5)

# Botón para enviar JSON a la API
btn_enviar = tk.Button(root, text="Enviar a la API", command=enviar_json, state=tk.DISABLED)
btn_enviar.pack(pady=5)
 
# Ejecutar la interfaz gráfica
root.mainloop()
