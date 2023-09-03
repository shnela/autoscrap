from geopy.geocoders import (
    Nominatim,
)
from scrapy.utils.project import (
    get_project_settings,
)


def get_geolocation(city):
    user_agent = get_project_settings()["USER_AGENT"]
    geolocator = Nominatim(user_agent=user_agent, timeout=10)
    return geolocator.geocode(city)


def autoscout_geo2geopy(as_geo):
    return as_geo["Longitude"], as_geo["Latitude"]


def geopy2autoscout_geo(geopy_geo):
    return {
        "Longitude": geopy_geo.longitude,
        "Latitude": geopy_geo.latitude,
    }
