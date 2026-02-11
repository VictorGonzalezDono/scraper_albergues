import googlemaps
import pandas as pd
import time

# --- CONFIGURACIÓN ---
# PEGA TU API KEY AQUÍ
API_KEY = 'TU_API_KEY_AQUI' # El usuario debe colocar su propia key

gmaps = googlemaps.Client(key=API_KEY)

def buscar_y_enriquecer():
    print("🚀 Iniciando búsqueda profunda (Search + Details)...")
    
    # Coordenadas de Ensenada
    ensenada_coords = (31.8667, -116.5964)
    
    # Lista de términos para "atacar" por varios frentes y obtener más resultados
    busquedas = ['albergue de perros', 'refugio de animales', 'adopcion canina', 'protectora de animales']
    
    resultados_unicos = {} # Diccionario para evitar duplicados (Key = Place_ID)

    for termino in busquedas:
        print(f"\n🔎 Buscando con palabra clave: '{termino}'...")
        
        places_result = gmaps.places_nearby(
            location=ensenada_coords,
            radius=15000, 
            keyword=termino, 
            language='es'
        )
        
        while True:
            for place in places_result.get('results', []):
                place_id = place.get('place_id')
                
                # Si ya tenemos este lugar, lo saltamos
                if place_id in resultados_unicos:
                    continue
                
                nombre = place.get('name')
                
                # --- AQUÍ ESTÁ LA MAGIA (Fase de Enriquecimiento) ---
                # Hacemos una llamada EXTRA para pedir el teléfono
                try:
                    # Solo pedimos teléfono y web para ahorrar datos
                    detalles = gmaps.place(place_id=place_id, fields=['formatted_phone_number', 'website', 'url'])
                    info_extra = detalles.get('result', {})
                    
                    telefono = info_extra.get('formatted_phone_number', 'No disponible')
                    website = info_extra.get('website', 'No disponible')
                    maps_link = info_extra.get('url', 'No disponible')
                    
                except Exception as e:
                    print(f"   ⚠️ Error obteniendo detalles de {nombre}")
                    telefono = "Error"
                    website = "-"
                    maps_link = "-"

                print(f"   🐶 Encontrado: {nombre} | 📞 {telefono}")
                
                # Guardamos en nuestro diccionario maestro
                resultados_unicos[place_id] = {
                    'Nombre': nombre,
                    'Teléfono': telefono,
                    'Dirección': place.get('vicinity'),
                    'Rating': place.get('rating', 'N/A'),
                    'Website': website,
                    'Google Maps': maps_link,
                    'Keyword origen': termino # Para saber con qué palabra lo encontramos
                }

            # Paginación
            if 'next_page_token' in places_result:
                time.sleep(2) 
                places_result = gmaps.places_nearby(
                    location=ensenada_coords,
                    radius=15000,
                    keyword=termino,
                    language='es',
                    page_token=places_result['next_page_token']
                )
            else:
                break
    
    # Convertir diccionario a DataFrame
    lista_final = list(resultados_unicos.values())
    return pd.DataFrame(lista_final)

if __name__ == "__main__":
    df = buscar_y_enriquecer()
    
    if not df.empty:
        # Filtro rápido: Eliminar cosas que claramente no son albergues si contienen "Pétreos"
        # (Esto es Data Cleaning básico)
        df = df[~df['Nombre'].str.contains("Petreos", case=False, na=False)]
        
        archivo = 'albergues_ensenada_completo.xlsx'
        df.to_excel(archivo, index=False)
        print(f"\n✅ ¡Éxito! Se generó '{archivo}' con {len(df)} resultados y teléfonos.")
    else:
        print("❌ No se encontraron resultados.")