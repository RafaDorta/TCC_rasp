from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import time
from pymongo import MongoClient
from googlemaps import exceptions
import googlemaps
import serial

client = MongoClient('mongodb+srv://admin:admin@tcc.rvv4i.mongodb.net/?retryWrites=true&w=majority&appName=TCC')
db = client['meu_banco']
users_graficos = db['graficos']

gps_serial=serial.Serial('/dev/ttyAMA0', baudrate=9600, timeout=1)

def convert_to_decimal(degree_minute, direction):
    if degree_minute == "":
        print("Erro: degree_minute est� vazio")
        return None
    
    if direction in ['N', 'S']:
        degrees = int(degree_minute[:2])
        minutes = float(degree_minute[2:])
    else:
        degrees = int(degree_minute[:3])
        minutes = float(degree_minute[3:])

    decimal = degrees + (minutes / 60)

    if direction in ['S', 'W']:
        decimal = -decimal

    return round(decimal, 4)

def parse_gga_sentence(sentence):
    try:
        parts = sentence.split(',')
        latitude = parts[1]
        latitude_direction = parts[2]
        longitude = parts[3]
        longitude_direction = parts[4]
        
        
        if not latitude or not longitude or not latitude_direction or not longitude_direction:
            print("Erro: Valores de latitude ou longitude est�o vazios")
            return None
        
        latitude_final = convert_to_decimal(latitude, latitude_direction)
        longitude_final = convert_to_decimal(longitude, longitude_direction)
        return latitude_final, longitude_final
    except IndexError:
        print("Erro: Linha GGA incompleta")
        return None

def read_gps_data(timeout=5):
    """Tenta ler novos dados do GPS por um tempo m�ximo (timeout)"""
    start_time = time.time()
    new_data = None
    gps_serial.reset_input_buffer()  # Limpa o buffer antes de come�ar a ler novos dados
    while time.time() - start_time < timeout:
        try:
            while gps_serial.in_waiting > 0:
                line = gps_serial.readline().decode('utf-8', errors='ignore').strip()
                if line.startswith('$GPGLL'):
                    lat,lng = parse_gga_sentence(line)
                    if lat:
                        return lat,lng
        except serial.SerialException as e:
            print(f"Erro na porta serial: {e}")
            return None
    return None

_GEOLOCATION_BASE_URL = "https://www.googleapis.com"
client = googlemaps.Client(key='AIzaSyBu2IkPNjkUMYtoWSEtQWF6NbPqSE7_hwM')

def get_address_from_coordinates(latitude, longitude):
    try:
        result = client.reverse_geocode((latitude, longitude))
        if result:
            return result[0]['formatted_address']
        else:
            return "Endereco nao encontrado."
    except exceptions.ApiError as e:
        print(f"Erro ao chamar a API: {e}")
        return None

    

def calculateSpeed(origem, destino):
    now = datetime.now()
    directions_result = client.directions(origem, destino, mode="driving", departure_time=now)

    if directions_result:
        distancia_em_metros = directions_result[0]['legs'][0]['distance']['value']
        print(distancia_em_metros)
        avg_Speed = (distancia_em_metros/10) * 3.6
        print(avg_Speed)
        return avg_Speed
    else:
        return None


gps_data = None




user = "Admin"
latitude,longitude = read_gps_data(timeout=5)
initial_Lat,initial_Lng = latitude,longitude
date = datetime.now().strftime("%d/%m/%Y, %H:%M:%S")
initial_LocAddress = get_address_from_coordinates(initial_Lat, initial_Lng)
print(initial_LocAddress)
time.sleep(10)
final_Lat,final_Lng = "-22.852109", "-47.054464"
final_LocAddress = get_address_from_coordinates(final_Lat, final_Lng)
print(final_LocAddress)
speed = calculateSpeed(initial_LocAddress,final_LocAddress)

data_to_insert = {
    'username': user,
    'date': date,
    'address': initial_LocAddress,
    'speed': speed
}

users_graficos.insert_one(data_to_insert)


print("Dados inseridos com sucesso:", data_to_insert)