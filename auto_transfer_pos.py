import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import paramiko
from scp import SCPClient

# Configuration
LOCAL_FILE = r"D:\PROJECTS\ParkEase-Python-Backend\src\parkease"  # File to monitor
EC2_HOST = "ec2-44-201-94-87.compute-1.amazonaws.com"  # EC2 instance public DNS
EC2_USER = "ubuntu"  # EC2 username
PEM_KEY_PATH = r"C:\Users\arjun\Downloads\parkease-test-free-key.pem"  # Private key path
REMOTE_DIRECTORY = "/home/ubuntu/parkease-final/src/"  # Directory on EC2

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
                self.transfer_file(event.src_path)
            except Exception as e:
                print(f"Error transferring file: {e}")

    def on_created(self, event):
        self.on_modified(event)  # Handle file creation the same way

    def transfer_file(self, file_path):
        try:
            with create_scp_client() as scp:
                # Specify the exact destination path for the file
                remote_file_path = os.path.join(REMOTE_DIRECTORY, "parkease")
                scp.put(file_path, remote_file_path)
                print(f"Transferred {file_path} to EC2:{remote_file_path}")
        except Exception as e:
            print(f"Error during file transfer: {e}")

# Watch Directory
if __name__ == "__main__":
    # Check if the file exists initially
    if os.path.exists(LOCAL_FILE):
        print(f"File already exists. Transferring {LOCAL_FILE} to EC2.")
        handler = FileHandler()
        handler.transfer_file(LOCAL_FILE)

    # Monitor the file for changes or creation
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
