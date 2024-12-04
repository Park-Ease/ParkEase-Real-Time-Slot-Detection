import cv2 
import numpy as np 
import cvzone 
import pickle 
import os 
from dotenv import load_dotenv 

dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path)

CAMERA_STREAM_URL = os.getenv("CAMERA_STREAM_URL")
if not CAMERA_STREAM_URL:
    raise EnvironmentError("CAMERA_STREAM_URL environment variable is not set!")

cap = cv2.VideoCapture(CAMERA_STREAM_URL)

drawing=False
area_names=[]
try:
    with open("parkease","rb") as f:
        data = pickle.load(f)
        polylines, area_names = data['polylines'], data['area_names']
except:
    polylines=[]

points=[]
current_name=""

print("**Welcome to ParkEase - Parking Slot Detection and Management**")
print("Step 1: Use mouse buttons and drag to mark a slot.")
print("Step 2: Press 's' to save the coordinates and quit.")
print("Step 3: Press 'q' to quit.")

def draw(event,x,y,flags,param):
    global points,drawing
    drawing=True
    if event==cv2.EVENT_LBUTTONDOWN:
        points=[(x,y)]
        print(x,y)
    elif event==cv2.EVENT_MOUSEMOVE:
        if drawing: 
            points.append((x,y))
    elif event==cv2.EVENT_LBUTTONUP:
        drawing=False
        current_name = input("Enter the area name: ")
        if current_name:
            area_names.append(current_name)
            polylines.append(np.array(points,np.int32))
    

while True:
    ret, frame = cap.read()
    if not ret:
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        continue
    frame=cv2.resize(frame,(1020,500))
    for i,polyline in enumerate(polylines):
        cv2.polylines(frame,[polyline],True,(0,0,255),2)
        cvzone.putTextRect(frame,f"{area_names[i]}",tuple(polyline[0]),1,1)
    
    cv2.imshow('FRAME', frame)
    cv2.setMouseCallback('FRAME',draw)
    key = cv2.waitKey(1) & 0xFF
    if key==ord('s'):
        with open("parkease","wb") as f:
            data = {'polylines': polylines, 'area_names': area_names}
            pickle.dump(data,f)
            break
    elif key==ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

