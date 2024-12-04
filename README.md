# ParkEase - Parking Slot Detection and Management - Image Processing

![ParkEase Banner](./parkease-front-banner.png "ParkEase Parking Slot Management")

# Introduction:

This is the main Python and OpenCV code that runs to mark the parking slots, check whether a parking slot is filled and then dynamically update the slot status in the DB in real-time with the power of Prisma and WebSockets.

---

# Key Features
- Real-Time Updates: Dynamically reflects parking slot status in the database.
- Remote Processing: Integrates with remote EC2 instances for centralized processing.
- Efficient Communication: Utilizes WebSockets for seamless real-time updates.
- Intelligent Detection: Leverages YOLO models for advanced object detection.

---

# Required Packages - Local:

## Python
1) os - Operating/File System interactions
2) time - Functions to manipulate time values
3) pickle - Serializes and deserializes Python objects for storage or transfer

## External
4) watchdog - Monitors file system events such as modifications or creations
5) paramiko - Enables secure SSH connections for remote server interactions
6) scp - Facilitates secure file transfers over SSH
7) opencv-python - Computer Vision Library for image and video processing
8) numpy - Operations on multi-dimensional arrays and matrices, often used with OpenCV
9) cvzone - High-level OpenCV functions to draw or create shapes on videos/images
10) python-dotenv - Loads environment variables from a .env file into application settings

# Required Packages - Docker Container:

## Python 
1) os - Operating/File System interactions 
2) pickle - Serializes and deserializes Python objects for storage or transfer 
3) time - Functions to manipulate time values 
4) asyncio - Library for writing concurrent code using async/await syntax 
5) json - Parses and manipulates JSON data 
6) typing - Provides support for type hints in Python

## External
7) fastapi - Web framework for building APIs with Python 3.6+
8) uvicorn - ASGI server for running FastAPI applications
9) pydantic - Data validation and settings management using Python type annotations
10) prisma - Database client for connecting to and interacting with Prisma-managed databases
11) python-dotenv - Loads environment variables from a .env file into application settings
12) opencv-python - Computer Vision Library for image and video processing (OpenCV)
13) pandas - Data manipulation and analysis library
14) ultralytics - Library for using YOLO models for object detection
15) cvzone - High-level OpenCV functions to draw or create shapes on videos/images
16) websockets - Library for creating WebSocket servers and clients in Python
17) requests - Library for sending HTTP requests

---

# Prisma Commands for MongoDB
1) prisma init - Creates a prisma folder and a schema.prisma
1) prisma generate - Generates the tables based on the schema
2) prisma db push - Pushes changes in schema directly to DB

---

# Docker Commands:
1) docker-compose up --build - Build and start the container
2) docker ps - See the container process status
2) docker exec -it parking_detection bash - Open an interactive shell inside the container

---

# Code Execution Flow:

## Local System
1) Configure the auto_transfer_pos.py Script
- Update the auto_transfer_pos.py script with the appropriate paths, EC2 instance configurations, and SSH key details.

2) Run the auto_transfer_pos.py Script
- Execute the auto_transfer_pos.py script in a shell session and keep it running.

3) Execute the mark_slots.py Script
- Open another shell and run the mark_slots.py script. Follow the command-line instructions to mark the parking slots.

4) File Transfer
- After completing the slot marking process, ensure the generated parkease file is saved. Wait for the file to be automatically transferred to the remote instance.

## Docker Container on Remote Instance
1) Initialize the Docker Environment
- Run the Docker commands as outlined in the setup instructions to initialize the container environment.

2) Bring up the FastAPI Server:
- Run the websocket_server_fastapi.py script to enable the server via uvicorn. Keep it running in a shell.

3) Modify and Run the init_lot_n_slots.py Script
- Add the coordinates of the parking slots in the list under "locations".
- Execute the init_lot_n_slots.py script to prepare the parking lot and slot configurations.

4) Run the Parking Slot Detection Script
- In a separate shell session, execute the parking_slot_detection.py script to begin real-time parking slot detection.

## Raspberry Pi
1) Get into the virtual environment inside "parkease-final" folder.

2) Run the script to capture the real-time stream and transfer 5 min chunks to the AWS S3 instance.

3) Access the web app under any manager account and view the videos in the manager dashboard under the videos tab.

---

# Testing

## Unit Testing
Test individual modules and functions, such as:
- Object serialization/deserialization using pickle.
- Slot detection logic using test images or videos.
- WebSocket event handling for real-time updates.

## Functional Testing
- Verify that parking slots are marked correctly using the mark_slots.py script.
- Test real-time slot status updates via WebSocket communication.

## Integration Testing
- Confirm that the EC2 instance processes the parkease file correctly.
- Ensure the init_lot_n_slots.py and WebSocket server interact as expected.

## Performance Testing
- Test the system’s ability to handle multiple parking slots simultaneously.
- Validate the YOLO model’s performance under varying lighting and object occlusion conditions.

## System Testing
- Test the complete workflow:
- Detect and mark parking slots using mark_slots.py.
- Transfer the generated file to the remote EC2 instance.
- Execute init_lot_n_slots.py to initialize slots in the database.
- Verify the correct operation of the WebSocket server and the parking_slot_detection.py script.

---

# Contributions

## How to Contribute
1) Fork the Repository: Clone the repository to your local machine for development.
2) Set Up the Environment: Follow the instructions in this document to set up the local or Dockerized environment.
3) Make Changes: Work on improvements, bug fixes, or new features.
4) Test Thoroughly: Run all relevant tests, including unit, integration, and system tests.
5) Create a Pull Request: Submit your changes for review.

---

# Areas to Contribute
1) Documentation: Enhance or correct README.md to ensure clarity and completeness.
2) Improvements: Suggest a better and easier execution flow for the program.
2) Testing: Add more test cases to improve coverage and reliability.
3) Optimization: Improve performance for larger parking lots or more complex scenarios.
4) Feature Development: Suggest and implement new features to enhance functionality.

