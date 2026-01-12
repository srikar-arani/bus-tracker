import requests
import json
import time

bpos_url = "http://api.wmata.com/Bus.svc/json/jBusPositions"
stop_url = "http://api.wmata.com/Bus.svc/json/jStops"
next_url = "http://api.wmata.com/NextBusService.svc/json/jPredictions"


headers = {
        "api_key": "5e646942735d4aa8b12512652e2c0001"
}

def get_with_delay(url, params, headers, delay=0.09):
    time.sleep(delay)
    response = requests.get(url=url, params=params, headers=headers)
    response.raise_for_status()
    return response

def get_all_bus_positions():
    response = get_with_delay(url=bpos_url, params={}, headers=headers)
    all_bus_positions = response.json().get("BusPositions", [])
    return all_bus_positions

def get_bus_positions_from_routes(route_id):
    bpos_params = {
        "RouteID": route_id
    }
    response = get_with_delay(url=bpos_url, params=bpos_params, headers=headers)
    bus_positions = response.json().get("BusPositions", [])
    return bus_positions

def get_buses_from_all_positions(all_bus_positions, route_id):
    bus_positions = [
        bus for bus in all_bus_positions
        if bus.get("RouteID") in route_id
    ]
    return bus_positions

cached_stops = {}

def get_stops_from_bus_and_routes_with_radius(bus, route_id, radius=1000):
    lat = float(bus.get("Lat"))
    lon = float(bus.get("Lon"))
    key = (round(lat, 3), round(lon, 3), route_id)
    if key in cached_stops:
        return cached_stops.get(key)

    stop_params = {
        "Lat": lat,
        "Lon": lon,
        "Radius": radius
    }
    
    stop_response = get_with_delay(url=stop_url, params=stop_params, headers=headers)

    filtered_stop_data = [
        stop.get("StopID") for stop in stop_response.json().get("Stops", [])
        if route_id in stop.get("Routes", [])
    ]

    cached_stops[key] = filtered_stop_data

    return filtered_stop_data

cached_predictions = {}
def get_next_bus_for_stop(stop_id):
    if stop_id in cached_predictions:
        return cached_predictions.get(stop_id)
    
    next_params = {
        "StopID": stop_id
    }

    next_response = get_with_delay(url=next_url, params=next_params, headers=headers)
    predictions = next_response.json().get("Predictions", [])
    cached_predictions[stop_id] = predictions

    return predictions

def get_next_stop_for_bus_with_stops(bus, stop_ids):
    next_stop = None
    soonest = float("inf")

    for stop_id in stop_ids:
        predictions = get_next_bus_for_stop(stop_id)
        
        for prediction in predictions:
            if prediction.get("VehicleID") != bus.get("VehicleID"):
                continue

            minutes = prediction.get("Minutes")
            if isinstance(minutes, str) and minutes.isdigit():
                minutes = int(minutes)
            elif not isinstance(minutes, int):
                continue

            if minutes < soonest:
                soonest = minutes
                next_stop = stop_id

    return next_stop, soonest

def next_stops_for_route(route_id):
    buses = [
        bus for bus in get_bus_positions_from_routes(route_id)
        if bus.get("DirectionText", "").upper().startswith("NORTH")
    ]

    results = []

    for bus in buses:
        stop_ids = get_stops_from_bus_and_routes_with_radius(bus, route_id)

        if not stop_ids:
            continue

        next_stop, minutes = get_next_stop_for_bus_with_stops(bus, stop_ids)

        if next_stop:
            results.append({
                "VehicleID": bus.get("VehicleID"),
                "NextStop": next_stop,
                "Minutes": minutes
            })

    return results

if __name__ == "__main__":
    ROUTES = ["C53", "D20"]

    while True:
        cached_predictions.clear()
        bus_positions = get_all_bus_positions()

        for bus in bus_positions:
            if bus.get("RouteID") not in ROUTES:
                continue

            stops = get_stops_from_bus_and_routes_with_radius(bus, bus.get("RouteID"))

            next_stop, minutes = get_next_stop_for_bus_with_stops(bus, stops)
            print(bus["RouteID"], bus["VehicleID"], next_stop, minutes, bus["DirectionText"])

        time.sleep(15)