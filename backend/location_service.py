import requests
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

class LocationService:
    def __init__(self):
        self.geolocator = Nominatim(user_agent="khadamat_ai_locator")

    def get_coordinates(self, address):
        """
        Geocodes an address to (latitude, longitude).
        Returns None if address not found.
        """
        try:
            location = self.geolocator.geocode(address + ", Morocco", timeout=10) # Append Morocco for better accuracy
            if location:
                return location.latitude, location.longitude
            return None
        except GeocoderTimedOut:
            return None
        except Exception as e:
            print(f"Geocoding error: {e}")
            return None

    def find_nearby_centers(self, lat, lon, category):
        """
        Finds nearby administrative centers using Overpass API (OpenStreetMap).
        Category mapping:
        - 'police': Police stations (Commissariat)
        - 'all': All administrative offices
        - 'health': Hospitals/Clinics
        - 'justice': Courts
        """
        overpass_url = "http://overpass-api.de/api/interpreter"
        
        # Define tags based on category
        if category == 'police':
            tags = '["amenity"="police"]'
        elif category == 'municipality': # Moqataa / Commune
            tags = '["office"~"government|administrative"]["admin_level"~"8|9|10"]' 
        elif category == 'wilaya':
            tags = '["office"="government"]["admin_level"="4"]'
        elif category == 'court':
            tags = '["amenity"="courthouse"]'
        elif category == 'hospital':
            tags = '["amenity"="hospital"]'
        else:
            # General administrative search
            tags = '["office"="government"]'

        # Query for nodes within 5km radius (5000m)
        overpass_query = f"""
        [out:json];
        (
          node{tags}(around:5000,{lat},{lon});
          way{tags}(around:5000,{lat},{lon});
          relation{tags}(around:5000,{lat},{lon});
        );
        out center;
        """
        
        try:
            response = requests.get(overpass_url, params={'data': overpass_query}, timeout=20)
            if response.status_code == 200:
                data = response.json()
                results = []
                for element in data.get('elements', []):
                    # Use center coordinates if available (for ways/relations), else lat/lon
                    lat_elem = element.get('lat') or element.get('center', {}).get('lat')
                    lon_elem = element.get('lon') or element.get('center', {}).get('lon')
                    
                    name = element.get('tags', {}).get('name') or element.get('tags', {}).get('name:fr') or element.get('tags', {}).get('name:ar') or "Centre Administratif"
                    
                    if lat_elem and lon_elem:
                        results.append({
                            "name": name,
                            "lat": lat_elem,
                            "lon": lon_elem,
                            "type": category
                        })
                return results[:10] # Return top 10 to keep it clean
            else:
                print(f"Overpass API error: {response.status_code}")
                return []
        except Exception as e:
            print(f"Error fetching nearby centers: {e}")
            return []

if __name__ == "__main__":
    # Test
    service = LocationService()
    coords = service.get_coordinates("Rabat, Agdal")
    if coords:
        print(f"Coords: {coords}")
        print(service.find_nearby_centers(coords[0], coords[1], "police"))
