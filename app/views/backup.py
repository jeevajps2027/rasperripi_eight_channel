import os
import json
import shutil
import time
from threading import Thread
from pathlib import Path
from datetime import datetime
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from app.models import BackupSettings  # Import your BackupSettings model
import openpyxl


# ---------------------- Helper Functions ----------------------

def get_save_directory():
    usb_base_path = '/media'
    downloads_path = str(Path.home() / 'Downloads')

    if os.path.exists(usb_base_path):
        for user_folder in os.listdir(usb_base_path):
            user_path = os.path.join(usb_base_path, user_folder)
            if os.path.isdir(user_path):
                for device_folder in os.listdir(user_path):
                    device_path = os.path.join(user_path, device_folder)
                    if os.path.ismount(device_path):
                        return device_path, 'USB'

    return downloads_path, 'Downloads'

def backup_database_to_sql():
    BASE_DIR = Path(__file__).resolve().parent.parent.parent  # adjust if needed
    source_db_path = BASE_DIR / "db.sqlite3"

    if not source_db_path.exists():
        print(f"Database not found at: {source_db_path}")
        return None, None

    save_path, location_type = get_save_directory()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_folder = Path(save_path) / f'backup_{timestamp}'
    backup_folder.mkdir(parents=True, exist_ok=True)

    backup_file = backup_folder / f"db_backup_{timestamp}.sqlite3"

    try:
        shutil.copy2(source_db_path, backup_file)
        print(f"✅ Backup successful! File saved at: {backup_file} ({location_type})")
        return str(backup_file), location_type
    except Exception as e:
        print(f"❌ Failed to back up database: {e}")
        return None, None

# ---------------------- Main Functions ----------------------

def backup(request):
    if request.method == 'POST':
        data = json.loads(request.body)

        id_value = data.get('idValue')
        confirm_value = data.get('confirm')
        date_back = data.get('backup_date')
        print('Your changed id values are:', id_value, confirm_value, date_back)

        # Update the existing BackupSettings instance
        backup_setting = get_object_or_404(BackupSettings, id=id_value)
        backup_setting.backup_date = date_back
        backup_setting.confirm_backup = confirm_value
        backup_setting.save()

        # Start a thread to create new backup setting after 2 seconds
        Thread(target=create_new_backup_setting, args=(date_back, confirm_value)).start()

        # Immediately perform a backup for the alert message
        backup_file_path, location_type = backup_database_to_sql()

        if backup_file_path:
            message = f'Backup settings updated! New entry created. Backup saved in your {location_type.lower()}.'
        else:
            message = 'Backup settings updated! New entry created. (Backup failed!)'

        return JsonResponse({'status': 'success', 'message': message})

    return render(request, 'app/login.html')

def create_new_backup_setting(existing_backup_date, confirm_value):
    if confirm_value == 'True':
        time.sleep(2)

        existing_date = datetime.strptime(existing_backup_date, '%d-%m-%Y %I:%M:%S %p')

        new_month = existing_date.month + 1 if existing_date.month < 12 else 1
        new_year = existing_date.year if existing_date.month < 12 else existing_date.year + 1
        new_backup_date = existing_date.replace(month=new_month, year=new_year)
        formatted_new_backup_date = new_backup_date.strftime('%d-%m-%Y %I:%M:%S %p')

        BackupSettings.objects.create(
            backup_date=formatted_new_backup_date,
            confirm_backup=False
        )
