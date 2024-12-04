import os 
import pickle 
import requests
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path)

WEBSOCKET_HOST = os.getenv("WEBSOCKET_HOST")
WEBSOCKET_PORT = os.getenv("WEBSOCKET_PORT")
PARKING_LOT_ID = os.getenv("PARKING_LOT_ID")

# Dummy Data
locations = [
    {"lat": 12.281175, "long": 76.640907},
    {"lat": 12.281155, "long": 76.640903},
    {"lat": 12.281136, "long": 76.640898},
    {"lat": 12.281145, "long": 76.640898},
]

if not WEBSOCKET_HOST or not WEBSOCKET_PORT:
    raise EnvironmentError("Either WEBSOCKET_HOST or WEBSOCKET_PORT environment variable is not set!")

try:
    with open("parkease", "rb") as f:
        data = pickle.load(f)
        polylines, area_names = data["polylines"], data["area_names"]
        PARKING_SLOTS = len(polylines)
except FileNotFoundError:
    print("Error: 'parkease' file not found. Run 'mark_slots.py' first.")
    exit(1)

if not PARKING_LOT_ID:
    try:
        API_URL = f"http://{WEBSOCKET_HOST}:{WEBSOCKET_PORT}/create_parking_lot"

        payload = {
            "name": "Docker Test Parking Lot",
            "location": "MC PG, Vishweshwara Nagar",
            "total_slots": int(PARKING_SLOTS)
        }
        headers = {"Content-Type": "application/json"}

        response = requests.post(API_URL, json=payload, headers=headers)

        if response.status_code == 201:
            PARKING_LOT_ID = response.json().get("id")
            print(f"Created Parking Lot with ID: {PARKING_LOT_ID}")

            ## For Local:
            # with open(dotenv_path, "a") as env_file:
            #     env_file.write(f"\nPARKING_LOT_ID={PARKING_LOT_ID}")
            ##

            ## For Docker Env:
            with open("/etc/environment", "w") as env_file:
                env_file.write(f"\nPARKING_LOT_ID={PARKING_LOT_ID}\n")

            load_dotenv("/etc/environment")
            ##

            print(f"Added PARKING_LOT_ID to /etc/environment: {PARKING_LOT_ID}")
        else:
            print(f"Failed to create parking lot: {response.status_code} - {response.text}")
    except Exception as e:
        print("Some error occurred while creating the parking lot:", str(e))

if PARKING_SLOTS:
    try:
        API_URL = f"http://{WEBSOCKET_HOST}:{WEBSOCKET_PORT}/create_parking_slots"

        payload = {
            "num_parking_slots": int(PARKING_SLOTS),
            "parking_lot_id": PARKING_LOT_ID,
            "slot_numbers": area_names,
            "locations": locations
        }
        headers = {"Content-Type": "application/json"}

        response = requests.post(API_URL, json=payload, headers=headers)

        if response.status_code == 200:
            slots = response.json().get("slots")
            print("Slots created successfully!")
            print(slots)
        else:
            print(f"Failed to create the parking slots: {response.status_code} - {response.text}")
    except Exception as e:
        print("Some error occurred while creating the parking slots:", str(e))
else:
    print("PARKING_SLOTS variable doesn't exist! Run mark_slots.py again.")
