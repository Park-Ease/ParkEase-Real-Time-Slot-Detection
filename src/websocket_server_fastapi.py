from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from pydantic import BaseModel
from typing import List, Dict, Any
from prisma import Prisma
from dotenv import load_dotenv
import uvicorn
import asyncio
import os 

dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path)

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise EnvironmentError("DATABASE_URL environment variable is missing or not set")

# Deprecated #
# Connect to Prisma at the startup
# @app.on_event("startup")
# async def startup():
#     await prisma.connect()

# # Disconnect Prisma at shutdown
# @app.on_event("shutdown")
# async def shutdown():
#     await prisma.disconnect()

@asynccontextmanager
async def lifespan(app: FastAPI):
    await prisma.connect()
    yield
    await prisma.disconnect()

# Dependency to inject Prisma into the route handlers
async def get_prisma():
    return prisma

app = FastAPI()
prisma = Prisma()

# Request models
class ParkingLotCreateRequest(BaseModel):
    name: str
    location: str
    total_slots: int


class ParkingSlotCreateRequest(BaseModel):
    num_parking_slots: int
    parking_lot_id: str
    slot_numbers: List[int]
    locations: List[Dict[str, float]]


@app.post("/create_parking_lot", status_code=201)
async def create_parking_lot(data: ParkingLotCreateRequest, prisma: Prisma = Depends(get_prisma)):
    try:
        parking_lot = await prisma.parkinglot.create(
            data={
                "name": data.name,
                "location": data.location,
                "totalSlots": data.total_slots
            }
        )
        return {"id": parking_lot.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/create_parking_slots", status_code=200)
async def create_parking_slots(data: ParkingSlotCreateRequest, prisma: Prisma = Depends(get_prisma)):
    if len(data.slot_numbers) != len(data.locations) or len(data.slot_numbers) != data.num_parking_slots:
        raise HTTPException(status_code=400, detail="Mismatch between num_parking_slots, slot_numbers, and locations")

    try:
        slots = []
        for slot_number, location in zip(data.slot_numbers, data.locations):
            slot = await prisma.parkingslot.create(
                data={
                    "slotNumber": int(slot_number),
                    "locationX": location["lat"],
                    "locationY": location["long"],
                    "lotId": data.parking_lot_id,
                    "status": True
                }
            )
            slots.append(slot)
        return {"slots": [slot.dict() for slot in slots]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# WebSocket handling
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: Dict[str, Any]):
        for connection in self.active_connections:
            await connection.send_json(message)


manager = ConnectionManager()


@app.websocket("/connect")
async def websocket_connect(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast({"message": f"Echo: {data}"})
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.websocket("/update_slot_status")
async def update_slot_status(websocket: WebSocket, prisma: Prisma = Depends(get_prisma)):
    await manager.connect(websocket)

    ## Docker Env:
    load_dotenv("/etc/environment")
    ##

    PARKING_LOT_ID = os.getenv("PARKING_LOT_ID")
    if not PARKING_LOT_ID:
        raise EnvironmentError("PARKING_LOT_ID environment variable is missing or not set")
    
    print("PARKING_LOT_ID:",PARKING_LOT_ID)
    
    try:
        while True:
            # Receive data from the client
            data = await websocket.receive_json()
            filled_slots = data.get("filled_slots", [])
            free_slots = data.get("free_slots", [])
            timestamp = data.get("timestamp")

            # Logging information
            print(f"Filled Slot Numbers: {filled_slots}")
            print(f"Free Slot Numbers: {free_slots}")
            print(f"Timestamp: {timestamp}")

            # Use asyncio.gather to batch the updates for efficiency
            async def update_slot_status(slot_number: str, status: bool):
                slot = await prisma.parkingslot.find_first(
                    where={"lotId": PARKING_LOT_ID, "slotNumber": int(slot_number)}
                )
                if slot:
                    await prisma.parkingslot.update(
                        where={"id": slot.id},
                        data={"status": status}
                    )

            # Run updates concurrently for filled and free slots
            tasks = []
            for slot_num in filled_slots:
                tasks.append(update_slot_status(slot_num, False))
            for slot_num in free_slots:
                tasks.append(update_slot_status(slot_num, True))
            
            # Wait for all updates to complete
            await asyncio.gather(*tasks)

            print("Slot statuses updated successfully!")

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        await websocket.send_json({"error": str(e)})

if __name__=="__main__":
    uvicorn.run(app,host="127.0.0.1",port=5000)

