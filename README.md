# 📁 Infomaniak S3 Backup Script

This Python script allows you to back up local folders to Infomaniak S3 and schedule automatic deletions of backups older than 3 months.

## Prerequisites

Before getting started, make sure you have the following in place:

- Python 3 installed on your system.
- Required Python libraries installed. You can install them using `pip` by running `pip install -r requirements.txt`.
- An Infomaniak Public Cloud (IPC) account with access keys to access S3.
- An S3 bucket on IPC to store the backups.
- A running Gotify server for receiving notifications (optional).

## Configuration

1. Clone the GitHub repository to your local machine:

    ```
    git clone https://github.com/Zerka30/s3-backup.git
    ```

2. Navigate to the project directory:

    ```
    cd s3-backup
    ```

3. Copy the `config.example.yml` file to `config.yml`:

    ```
    cp config.example.yml config.yml
    ```

4. Edit the `config.yml` file to set your own values, including IPC access keys, S3 bucket name, folders to back up, and more.

5. Create a `.bakignore` file if you want to exclude specific files or folders from the backup. You can use Gitignore-style matching rules in this file.

6. If you're using Gotify for notifications, ensure you have a running Gotify server and configure the API URL and API token in the `config.yml` file.

## Usage

Run the script with the following command: `python3 main.py`

You can schedule the automatic execution of this script using a task scheduling tool such as Cron on Linux. For example, to run the script every Sunday at 3 AM, add the following entry to your crontab:

```bash
0 3 * * 0 python3 /path/to/s3-backup/main.py
