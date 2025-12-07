from dotenv import load_dotenv
load_dotenv()

from google import genai
import os

client = genai.Client(api_key=os.getenv("GOOGLE_GEMINI_API_KEY"))




def naturalize_response(base):
    # En este método nos conectamos con la api de gemini de google, para obtener una respuesta naturalizada
    
    message = f'Eres un asistente de ventas  para una empresa de electrónicos llamada Arc -- tienda de electrónicos avanzada, de una forma amigable y cómoda, no uses decoradores de texto, es decir escribe principalmente lo necesario de forma amigable, y si el contenido no existe, da un mensaje de error.  Debes presentarle al usuario la siguiente información'+str(base)+"aqui terminan los datos, si estos se encuentran vacíos, presenta un mensaje de error, en lugar de datos incorrectos"
    
    response = client.models.generate_content(
        model="gemini-2.5-flash", contents=message
    )
        
    print(response.text)
    return response.text