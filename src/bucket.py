import boto3
import os
import logging
import shutil
import tarfile


class S3Bucket:
    def __init__(self, endpoint_url, bucket_name, access_key, secret_key):
        self.endpoint_url = endpoint_url
        self.bucket_name = bucket_name
        self.access_key = access_key
        self.secret_key = secret_key
        self.s3_client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
        )

    def list_objects(self):
        # List objects in the S3 bucket
        objects = self.s3_client.list_objects_v2(Bucket=self.bucket_name)
        return objects.get("Contents", [])

    def upload_folder(
        self, source_path, service_name, current_datetime, bakignore_rules
    ):
        # Create a repository for the backup (format: service_name/date_time)
        backup_folder_name = (
            f"{service_name}/{current_datetime.strftime('%Y-%m-%d_%H-%M-%S')}"
        )

        # Get the base path for the rules
        base_path = os.path.abspath(source_path)

        for root, dirs, files in os.walk(source_path):
            for file in files:
                source_file = os.path.join(root, file)
                s3_key = os.path.join(
                    backup_folder_name, os.path.relpath(source_file, source_path)
                )

                # Make the source_file path relative to the base_path
                rel_source_file = os.path.relpath(source_file, base_path)
                if not bakignore_rules(rel_source_file):
                    # Copy file to S3 Bucket
                    try:
                        self.s3_client.upload_file(
                            source_file,
                            self.bucket_name,
                            s3_key,
                            ExtraArgs={"ACL": "private"},
                            Callback=None,
                        )
                        logging.info(f"Backup: {s3_key} - Success")
                    except Exception as e:
                        logging.error(f"Error while backing up {s3_key}: {str(e)}")
                else:
                    logging.info(f"Backup: {s3_key} - File ignored")

    def upload_folder_has_archive(
        self, source_path, service_name, current_datetime, bakignore_rules
    ):
        # Create a repository for the backup (format: service_name/date_time)
        backup_folder_name = f"{service_name}"

        # Get the base path for the rules
        base_path = os.path.abspath(source_path)

        # Create a temporary directory to hold the compressed archive
        temp_dir = f"/tmp/{current_datetime.strftime('%Y-%m-%d_%H-%M-%S')}"
        os.makedirs(temp_dir)

        try:
            # Compress the source folder
            archive_name = os.path.join(temp_dir, "backup.tar.gz")
            with tarfile.open(archive_name, "w:gz") as archive:
                for root, dirs, files in os.walk(source_path):
                    for file in files:
                        source_file = os.path.join(root, file)
                        rel_source_file = os.path.relpath(source_file, base_path)
                        if not bakignore_rules(rel_source_file):
                            archive.add(source_file, arcname=rel_source_file)

            # Upload the compressed archive to S3
            s3_key = os.path.join(
                backup_folder_name,
                f"{current_datetime.strftime('%Y-%m-%d_%H-%M-%S')}.tar.gz",
            )
            self.s3_client.upload_file(
                archive_name, self.bucket_name, s3_key, ExtraArgs={"ACL": "private"}
            )

            logging.info(f"Backup Archive: {s3_key} - Success")
        except Exception as e:
            logging.error(f"Error while backing up {s3_key}: {str(e)}")
        finally:
            # Clean up the temporary directory
            shutil.rmtree(temp_dir)

    def delete_folder(self, folder_name):
        # List objects in the S3 bucket
        objects = self.list_objects()
        objects_to_delete = [
            obj["Key"] for obj in objects if obj["Key"].startswith(folder_name)
        ]

        for obj_key in objects_to_delete:
            try:
                # Delete objects that match the folder_name
                self.s3_client.delete_object(Bucket=self.bucket_name, Key=obj_key)
                logging.info(f"Deleted object: {obj_key}")
            except Exception as e:
                logging.error(f"Error while deleting object {obj_key}: {str(e)}")
