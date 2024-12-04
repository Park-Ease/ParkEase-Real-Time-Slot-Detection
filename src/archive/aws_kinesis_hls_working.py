from dotenv import load_dotenv
import os
import boto3
import cv2

# Load environment variables from the parent folder
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path)

# Access the environment variables
aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
aws_region = os.getenv("AWS_DEFAULT_REGION")

print("Access Key Id:",aws_access_key_id)
print("Secret Access Key:",aws_secret_access_key)
print("Region:",aws_region)

# Initialize Kinesis client with credentials from environment variables
kvs = boto3.client(
    'kinesisvideo',
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    region_name=aws_region
)

STREAM_NAME = "ParkEase_RaspStream"

# Get the endpoint for the stream
endpoint = kvs.get_data_endpoint(
    APIName="GET_HLS_STREAMING_SESSION_URL",
    StreamName=STREAM_NAME
)['DataEndpoint']

# Initialize kinesis-video-archived-media client
kvam = boto3.client('kinesis-video-archived-media', endpoint_url=endpoint)

# Get HLS stream URL
url = kvam.get_hls_streaming_session_url(
    StreamName=STREAM_NAME,
    PlaybackMode="LIVE"
)['HLSStreamingSessionURL']

print(url)

# Capture video from the HLS stream
vcap = cv2.VideoCapture(url)

while True:
    ret, frame = vcap.read()

    if frame is not None:
        cv2.imshow('frame', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    else:
        print("Frame is None")
        break

vcap.release()
cv2.destroyAllWindows()
