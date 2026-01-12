import requests
import json
import time
import os

next_url = "http://api.wmata.com/NextBusService.svc/json/jPredictions"

headers = {
        "api_key": "5e646942735d4aa8b12512652e2c0001"
}

session = requests.Session()
session.headers.update(headers)

def get_with_delay(url, params, delay=0.0):
    time.sleep(delay)
    response = session.get(url=url, params=params, timeout=5)
    response.raise_for_status()
    return response

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

    next_response = get_with_delay(url=next_url, params=next_params)
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
    with open('stops.json') as f:
        all_stops = json.load(f).get("all_stops")

    mapped_stops = []
    for stop in all_stops:
        mapped_stops.append((stop.get("stop_id"), stop.get("route")))

    while True:
        for stop_id, route_id in mapped_stops:
            try:
                bus_time = get_next_bus_for_stop(stop_id, route_id)
            except (requests.RequestException, ValueError) as e:
                print(f"Error fetching stop data for stop {stop_id}: {e}")
                bus_time = None

            print(f"Stop:{stop_id} with time {bus_time} and color {map_bus_time_to_color(bus_time)}")
        
        time.sleep(30)