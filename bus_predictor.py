import requests
import json

route_id = "C53"

base_url = "http://api.wmata.com/Bus.svc/json/jBusPositions"
stop_url = "http://api.wmata.com/Bus.svc/json/jStops"
next_url = "http://api.wmata.com/NextBusService.svc/json/jPredictions"

params = {
        "RouteID": route_id
}

headers = {
        "api_key": "5e646942735d4aa8b12512652e2c0001"
}

response = requests.get(url=base_url, params=params, headers=headers)

if response.status_code == 200:
    data = response.json()
    print(response.status_code)
    # print(json.dumps(data, indent=2))
    filtered_data = [
        bus for bus in data["BusPositions"]
        if bus["DirectionText"] == "NORTH"
    ]
    # print(json.dumps(filtered_data, indent=2))

    bus0 = filtered_data[0]
    print(json.dumps(bus0, indent=2))

    stop_params = {
        "Lat": float(bus0.get("Lat")),
        "Lon": float(bus0.get("Lon")),
        "Radius": 500
    }
    
    stop_response = requests.get(url=stop_url, params=stop_params, headers=headers)
    stop_data = stop_response.json()

    filtered_stop_data = [
        stop["StopID"] for stop in stop_data["Stops"]
        if route_id in stop["Routes"]
    ]

    print(filtered_stop_data)

    next_stop = None
    soonest = float("inf")

    for stop in filtered_stop_data:
        next_params = {
            "StopID": stop
        }

        next_response = requests.get(url=next_url, params=next_params, headers=headers)
        next_data = next_response.json().get("Predictions", [])
        
        for prediction in next_data:
            if prediction.get("VehicleID") == bus0.get("VehicleID"):
                minutes = prediction.get("Minutes")
                if isinstance(minutes, str) and minutes.isdigit():
                    minutes = int(minutes)
                elif not isinstance(minutes, int):
                    continue

                if minutes < soonest:
                    soonest = minutes
                    next_stop = stop
    if next_stop:
        print(f"Next stop for bus {bus0['VehicleID']}: {next_stop} in {soonest} min")

else:
    print("Error:", response.status_code, response.text)

