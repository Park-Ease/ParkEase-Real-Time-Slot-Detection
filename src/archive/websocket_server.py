import os
from quart import Quart, websocket, request, jsonify
from prisma import Prisma
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path)

app = Quart(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise EnvironmentError("DATABASE_URL environment variable is missing or not set")

prisma = Prisma()

@app.route("/create_parking_lot", methods=["POST"])
async def create_parking_lot():
    await prisma.connect()
    data = await request.get_json()

    name = data.get("name")
    location = data.get("location")
    total_slots = data.get("total_slots")

    if not name or not location or not total_slots:
        return jsonify({"error": "Missing required fields"}), 400

    try:
        parking_lot = await prisma.parkinglot.create(
            data={
                "name": name,
                "location": location,
                "totalSlots": total_slots
            })
        return jsonify({"id": parking_lot.id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        await prisma.disconnect()

@app.route("/create_parking_slots", methods=["POST"])
async def create_parking_slots():
    await prisma.connect()
    data = await request.get_json()

    num_parking_slots = data.get("num_parking_slots")
    parking_lot_id = data.get("parking_lot_id")
    slot_numbers = data.get("slot_numbers")
    locations = data.get("locations")

    if not num_parking_slots or not parking_lot_id or not slot_numbers or not locations:
        return jsonify({"error": "Missing required fields"}), 400

    if len(slot_numbers) != len(locations) or len(slot_numbers) != num_parking_slots:
        return jsonify({"error": "Mismatch between num_parking_slots, slot_numbers, and locations"}), 400

    try:
        slots = []
        for slot_number, location in zip(slot_numbers, locations):
            slot = await prisma.parkingslot.create(
                data={
                    "slotNumber": int(slot_number),
                    "locationX": float(location["lat"]),
                    "locationY": float(location["long"]),
                    "lotId": parking_lot_id,
                    "status": True  # True means available (slot is free)
                }
            )
            slots.append(slot)

        return jsonify({"slots": [slot.dict() for slot in slots]}), 200
    except Exception as e:
        return jsonify({"Error occurred": str(e)}), 500
    finally:
        await prisma.disconnect()

@app.websocket('/connect')
async def handle_connect():
    print("Client connected")
    try:
        while True:
            # Continuously listen for incoming messages from the client
            message = await websocket.receive()
            print(f"Message received: {message}")
            await websocket.send(f"Echo: {message}")
    except Exception as e:
        print(f"Error in WebSocket connection: {e}")

@app.websocket('/update_slot_status')
async def handle_update_slot_status():
    print("WebSocket connection established for slot updates.")
    PARKING_LOT_ID = os.getenv("PARKING_LOT_ID")
    if not PARKING_LOT_ID:
        raise EnvironmentError("PARKING_LOT_ID environment variable is missing or not set")
    try:
        await prisma.connect()
    except Exception as e:
        print("Connection failed!",e)

    while True:
        try:
            data = await websocket.receive_json()
            filled_slots = data.get("filled_slots")
            free_space = data.get("free_space")
            timestamp = data.get("timestamp")

            print(f"Received data: filled_slots={filled_slots}, free_space={free_space}, timestamp={timestamp}")

            print("hello")
            for slot_num in filled_slots:
                print("hi")
                slot = await prisma.parkingslot.find_first(
                    where={
                        "lotId": PARKING_LOT_ID,
                        "slotNumber": slot_num
                    }
                )

                print("Slot:",slot)
                if not slot:
                    print(f"Slot {slot_num} not found for lot {PARKING_LOT_ID}. Skipping...")
                    continue

                updated_slot = await prisma.parkingslot.update(
                    where={"id": slot.id},
                    data={"status": False}
                )
                print(f"Updated slot {slot_num} to status {'Vacant' if updated_slot.status else 'Filled'}")

            await websocket.send_json({"message": "Slot statuses updated successfully"})
        except Exception as e:
            print(f"Error in WebSocket update: {e}")
        finally:
            await prisma.disconnect()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)