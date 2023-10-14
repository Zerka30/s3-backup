import yaml
import logging
from datetime import datetime, timedelta
from gotify import Gotify
from gitignore_parser import parse_gitignore

from bucket import S3Bucket

# Configure logging
logging.basicConfig(
    filename="backup.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

if __name__ == "__main__":
    # Load configuration from the config.yml file
    with open("./config.yml", "r") as config_file:
        config = yaml.load(config_file, Loader=yaml.FullLoader)

    # Create an S3Bucket instance with configuration settings
    bucket = S3Bucket(
        config["s3"]["endpoint_url"],
        config["s3"]["bucket_name"],
        config["s3"]["access_key"],
        config["s3"]["secret_key"],
    )
    current_datetime = datetime.now()

    # Create a Gotify instance for sending notifications
    gotify = Gotify(config["gotify"]["api_url"], config["gotify"]["api_token"])

    # Initialize the summary message
    summary = []

    # Read the .bakignore file and parse the ignore rules
    bakignore_rules = parse_gitignore(".bakignore")

    # Start the backup process for each configured folder
    for folder_info in config["backup_folders"]:
        source_path = folder_info["path"]
        service_name = folder_info["service_name"]

        # Log that we are starting the backup for the service
        logging.info(f"Starting backup for service: {service_name}")

        try:
            # Save the folder
            bucket.upload_folder(
                source_path, service_name, current_datetime, bakignore_rules
            )
            logging.info(f"Backup for service {service_name} completed successfully.")

            # Accumulate information for the summary
            summary.append(f"Service: {service_name} - Backup completed successfully")
        except Exception as e:
            # Log an error if there is an issue with the backup
            logging.error(f"Error while backing up service {service_name}: {str(e)}")

            # Accumulate error information for the summary
            summary.append(f"Service: {service_name} - Error: {str(e)}")

    # Delete folders older than 3 months
    for folder_info in config["backup_folders"]:
        service_name = folder_info["service_name"]
        # Get all directories in the bucket/service_name
        objects = bucket.list_objects()
        for obj in objects:
            obj_key = obj["Key"]
            if obj_key.startswith(f"{service_name}/"):
                obj_datetime = obj["LastModified"]

                # Convert obj_datetime to naive datetime for comparison
                obj_datetime_naive = obj_datetime.replace(tzinfo=None)

                if obj_datetime_naive < current_datetime - timedelta(days=90):
                    try:
                        # Delete the folder
                        bucket.delete_folder(obj_key)

                        # Accumulate information for the summary
                        summary.append(
                            f"Deleted folder: {obj_key} - completed successfully."
                        )
                    except Exception as e:
                        # Accumulate information for the summary
                        summary.append(f"Deleted folder: {obj_key} - Error: {str(e)}")

    if config['enable_gotify']:
        # Send a Gotify notification with the summary
        gotify.create_message(
            title="Backup Summary",
            message="\n".join(summary),
            extras={"format": "text/plain"},
        )
