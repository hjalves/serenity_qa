from django.conf import settings
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive


def init_google_drive(client_json_file_path=None):
    client_json_file_path = client_json_file_path or settings.DRIVE_SERVICE_ACCOUNT_JSON
    gauth = GoogleAuth(
        settings={
            "client_config_backend": "service",
            "service_config": {"client_json_file_path": client_json_file_path},
        }
    )
    gauth.ServiceAuth()
    return GoogleDrive(gauth)
