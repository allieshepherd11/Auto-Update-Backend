import math

def haversine_distance(lat1, lon1, lat2, lon2):
    # Radius of the Earth in miles
    radius = 3958.8 

    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return radius * c

print(haversine_distance(28.65,-99.6,))