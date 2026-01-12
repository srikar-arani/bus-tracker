import requests
import json
import time
import os

bpos_url = "http://api.wmata.com/Bus.svc/json/jBusPositions"
stop_url = "http://api.wmata.com/Bus.svc/json/jStops"
next_url = "http://api.wmata.com/NextBusService.svc/json/jPredictions"

headers = {
        "api_key": "5e646942735d4aa8b12512652e2c0001"
}

session = requests.Session()
session.headers.update(headers)

def get_with_delay(url, params, headers, delay=0.0):
    time.sleep(delay)
    response = session.get(url=url, params=params, headers=headers, timeout=5)
    response.raise_for_status()
    return response

def get_all_stops_for_route(route_id):
    stop_response = get_with_delay(url=stop_url, params={}, headers=headers)
    filtered_stop_data = [
        stop.get("StopID") for stop in stop_response.json().get("Stops", [])
        if route_id in stop.get("Routes", [])
    ]

    return filtered_stop_data

def parse_return_as_int(r, query):
    p = r.get(query)
    if isinstance(p, str) and p.isdigit():
        return int(p)
    elif isinstance(p, int):
        return p
    return None

def get_next_bus_for_stop(stop_id, route_id):
    next_params = {
        "StopID": stop_id
    }

    next_response = get_with_delay(url=next_url, params=next_params, headers=headers)
    predictions = next_response.json().get("Predictions", [])

    filtered_predictions = [
        parse_return_as_int(prediction, "Minutes") for prediction in predictions
        if route_id == prediction.get("RouteID")
    ]

    filtered_predictions = [
        p for p in filtered_predictions
        if p is not None
    ]

    if not filtered_predictions:
        return None
    
    first_prediction = min(filtered_predictions)

    return first_prediction

def map_bus_time_to_color(bus_time):
    if bus_time is None:
        return "OFF"
    if bus_time > 10:
        return "OFF"
    if bus_time > 5:
        return "YELLOW"
    if bus_time > 1:
        return "GREEN"
    
    return "RED"

if __name__ == "__main__":
    with open('real_stops.json') as f:
        all_stops = json.load(f).get("all_stops")

    mapped_stops = []
    for route in all_stops:
        route_id = route.get("route")
        for stop in route.get("stops"):
            mapped_stops.append((stop, route_id))

    while True:
        for stop in mapped_stops:
            bus_time = get_next_bus_for_stop(stop[0], route_id=stop[1])
            print(f"Stop:{stop[0]} with time {bus_time} and color {map_bus_time_to_color(bus_time)}")
        
        time.sleep(30)