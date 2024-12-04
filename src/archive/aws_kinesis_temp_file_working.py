import boto3
import cv2
import tempfile
import time

def stream_kinesis_video(stream_name, region):
    # Initialize the Kinesis Video Streams client
    client = boto3.client('kinesisvideo', region_name=region)
    
    # Get the endpoint for the media playback
    response = client.get_data_endpoint(
        StreamName=stream_name,
        APIName='GET_MEDIA'
    )
    endpoint = response['DataEndpoint']
    
    # Get the media stream
    media_client = boto3.client('kinesis-video-media', endpoint_url=endpoint, region_name=region)
    stream_response = media_client.get_media(
        StreamName=stream_name,
        StartSelector={'StartSelectorType': 'NOW'}
    )
    
    # Use a temporary file to store the stream data
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        # Start reading the stream and write chunks of data to the file
        temp_file_path = temp_file.name
        temp_file.close()  # Close the temp file to allow OpenCV to read it

        # OpenCV capture object to read from the file
        cap = cv2.VideoCapture(temp_file_path)

        # Create a separate thread or loop for reading and writing to the file
        while True:
            # Read a chunk of data from the Kinesis stream
            chunk = stream_response['Payload'].read(1024*1024)  # Read in 1MB chunks
            if chunk:
                # Append the chunk to the temporary file
                with open(temp_file_path, 'ab') as f:
                    f.write(chunk)

            # Once some data is available, start reading and displaying the video
            if cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    cv2.imshow('Kinesis Video Stream', frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

            # Prevent high CPU usage by sleeping briefly while waiting for more data
            time.sleep(0.1)

        # Clean up
        cap.release()
        cv2.destroyAllWindows()

# Parameters

# Start the video stream
stream_name = 'ParkEase_RaspStream'
region = 'us-east-1'
stream_kinesis_video(stream_name, region)
