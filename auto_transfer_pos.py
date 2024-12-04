import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import paramiko
from scp import SCPClient

# Configuration
LOCAL_FILE = r"D:\PROJECTS\Parking_Slot_Detection_docker&websocket\src\parkease"  # File to monitor
EC2_HOST = "ec2-3-84-95-33.compute-1.amazonaws.com"  # EC2 instance public DNS
EC2_USER = "ubuntu"  # EC2 username
PEM_KEY_PATH = r"C:\Users\arjun\Downloads\parkease-test-free-key.pem"  # Private key path
REMOTE_DIRECTORY = "/home/ubuntu/parkease/"  # Directory on EC2 where file will be stored temporarily

# Specify your Docker container name or ID
DOCKER_CONTAINER_NAME = "your_container_name_or_id"  # Change this to your container's name or ID

# SCP Helper
def create_scp_client():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(EC2_HOST, username=EC2_USER, key_filename=PEM_KEY_PATH)
    return SCPClient(ssh.get_transport())

# Event Handler
class FileHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path == LOCAL_FILE:  # Only handle changes to the specified file
            try:
                print(f"Detected change in file: {event.src_path}")
                with create_scp_client() as scp:
                    # Upload the file to the remote EC2 directory
                    scp.put(event.src_path, os.path.join(REMOTE_DIRECTORY, os.path.basename(event.src_path)))
                    print(f"Transferred {event.src_path} to EC2:{REMOTE_DIRECTORY}")
                    self.move_to_docker_container()  # Move file to Docker container's expected location
            except Exception as e:
                print(f"Error transferring file: {e}")

    def on_created(self, event):
        self.on_modified(event)  # Handle file creation the same way

    # Move the file from EC2's temp directory to Docker's src folder
    def move_to_docker_container(self):
        try:
            # Command to move the file into the Docker container's src folder
            docker_move_command = f"docker cp /home/ubuntu/parkease {DOCKER_CONTAINER_NAME}:/app/src/"

            # Use Paramiko to execute the move command inside the EC2 instance
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(EC2_HOST, username=EC2_USER, key_filename=PEM_KEY_PATH)

            # Execute the move command inside the EC2 instance
            stdin, stdout, stderr = ssh.exec_command(docker_move_command)
            stdout.channel.recv_exit_status()  # Ensure the command was successful

            print(f"File successfully moved to Docker container '{DOCKER_CONTAINER_NAME}' at /app/src")
        except Exception as e:
            print(f"Error moving file to Docker container: {e}")

# Watch Directory
if __name__ == "__main__":
    observer = Observer()
    handler = FileHandler()
    monitored_dir = os.path.dirname(LOCAL_FILE)
    observer.schedule(handler, path=monitored_dir, recursive=False)
    print(f"Monitoring file: {LOCAL_FILE}")
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
