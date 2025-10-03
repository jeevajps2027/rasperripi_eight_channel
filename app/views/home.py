from django.http import JsonResponse
from django.shortcuts import render
from app.models import BackupSettings, TableFourData,  UserLogin
import json
from django.views.decorators.csrf import csrf_exempt



@csrf_exempt
def home(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')

            # Ensure username is not empty or None
            if not username:
                return JsonResponse({'status': 'error', 'message': 'Username is required.'}, status=400)

            if not username == 'SAADMIN':
                user, created = UserLogin.objects.get_or_create(id=1)  # Always use ID 1
                user.username = username  # Update the username field with the new value
                user.save()

                # Print information about the operation
                if created:
                    print(f'New username created: {user.username}')
                else:
                    print(f'Username already exists: {user.username}')

            # Check credentials
            if username == 'SAADMIN' and password == '54321':
                request.session['username'] = username
                return JsonResponse({'status': 'success', 'message': 'Login successful', 'redirect': '/index/'})
            
            # Check against Operator_setting
            elif TableFourData.objects.filter(operator_name=username,operator_no=password ).exists() :
                request.session['username'] = username
                return JsonResponse({'status': 'success', 'message': 'Login successful', 'redirect': '/index/'})
            else:
                return JsonResponse({'status': 'error', 'message': 'Invalid username or password'})

        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid request format'}, status=400)
    elif request.method == 'GET':
        # Fetch all operator names
        operators = TableFourData.objects.all()
        operator_names = [operator.operator_name for operator in operators]

        # Get the latest BackupSettings entry
        backup_settings = BackupSettings.objects.order_by('-id').first()

        # Prepare context for BackupSettings
        if backup_settings:
            # Print both backup_date and confirm_backup values in the terminal
            print('ID:', backup_settings.id)
            print('Backup Date:', backup_settings.backup_date)
            print('Confirm Backup:', backup_settings.confirm_backup)

            # Add backup settings data to the context
            context = {
                'operator_names': operator_names,
                'backup_date': backup_settings.backup_date,
                'confirm_backup': backup_settings.confirm_backup,
                'id': backup_settings.id
            }
        else:
            # Handle empty backup settings
            context = {
                'operator_names': operator_names,
                'backup_date': None,
                'confirm_backup': None,
                'id': None
            }

        # Render the template with the combined context
        return render(request, 'app/home.html', context)

    else:
        # Handle invalid HTTP method
        return JsonResponse({'status': 'error', 'message': 'Invalid HTTP method'}, status=405)




# import os
# from django.http import JsonResponse
# from django.shortcuts import redirect, render
# import json
# from datetime import datetime
# from app.models import UserLogin,BackupSettings, comport_settings
# import serial.tools.list_ports
# from django.conf import settings  # ⬅️ Add this import at the top


# # def get_available_com_ports():
# #     return [port.device for port in serial.tools.list_ports.comports()]



# def home(request):
#     error_message = ''
#     if request.method == 'POST':
#         username = request.POST.get('user')
#         password = request.POST.get('password')

#         # Get or create UserLogin instance with id=1
#         user_login, created = UserLogin.objects.get_or_create(id=1, defaults={'username': username, 'password': password})

#         # Update username and password if already exists
#         if not created:
#             user_login.username = username
#             user_login.password = password
#             user_login.save()

#         # Check username and password for redirection
#         if username in ['admin', 'o', 'saadmin'] and password == username:
#             return redirect('index')  # Redirect after successful login without backing up
#         else:
#             error_message = 'Invalid username or password'

#         # Pass the backup date to the template
#         return render(request, "app/home.html", {
#             'error_message': error_message,
#         })

#     elif request.method == 'GET':
#         try:

#             print("[DEBUG TEMPLATE] Looking for:", os.path.abspath("app/templates/app/home.html"))
#             print("[DEBUG BASE_DIR]:", settings.BASE_DIR)
#             print("[DEBUG TEMPLATE DIRS]:", settings.TEMPLATES[0]['DIRS'])
#             # Get the latest BackupSettings entry
#             backup_settings = BackupSettings.objects.order_by('-id').first()

#             # ports_string = ''

#             # # Get all comport settings
#             # all_comport_settings = list(comport_settings.objects.values_list('com_port', 'baud_rate', 'parity', 'stopbits', 'bytesize', 'card'))

#             # print('ypur data for thsi card is this:',all_comport_settings)
#             # # Find indices where card is "plc"
#             # plc_settings = [entry for entry in all_comport_settings if entry[5].strip().upper() == "PLC"]
#             # print('Filtered PLC Data:', plc_settings)  # Debugging Output


#             # if plc_settings:
#             #     # Unzip the filtered data into separate lists
#             #     comport_com_port, comport_baud_rate, comport_parity, comport_stopbit, comport_databit, comport_card = zip(*plc_settings)
#             # else:
#             #     # No matching PLC entries found
#             #     comport_com_port = []
#             #     comport_baud_rate = []
#             #     comport_parity = []
#             #     comport_stopbit = []
#             #     comport_databit = []
#             #     comport_card = []

#             # print('Filtered PLC Cards:', comport_card)
#             # print('Filtered Baud Rates:', comport_baud_rate)
#             # print('Filtered COM Ports:', comport_com_port)

#             # com_ports = get_available_com_ports()
#             # print('Available COM Ports:', com_ports)

#             # if com_ports:
#             #     # Get all matching ports
#             #     matching_ports = [port for port in comport_com_port if port in com_ports]
#             #     if matching_ports:
#             #         ports_string = ' '.join(matching_ports)  # Convert list to space-separated string
#             #         print('Matching COM ports found:', ports_string)
#             #     else:
#             #         ports_string = ' '.join(com_ports)  # Convert list to space-separated string
#             #         print('No matching COM port found. Sending all available ports:', ports_string)
#             # else:
#             #     ports_string = 'No COM ports available'
#             #     print(ports_string)

#             if backup_settings:
#                 # Print both backup_date and confirm_backup values in the terminal
#                 print('ID:', backup_settings.id)
#                 print('Backup Date:', backup_settings.backup_date)
#                 print('Confirm Backup:', backup_settings.confirm_backup)

#                 # Pass the values to the context
#                 context = {
#                     'backup_date': backup_settings.backup_date,
#                     'confirm_backup': backup_settings.confirm_backup,
#                     'id': backup_settings.id,
#                     # 'comport_com_port': ' '.join(comport_com_port),  
#                     # 'ports_string': ports_string,  
#                     # 'comport_baud_rate': ' '.join(map(str, comport_baud_rate)),  
#                     # 'comport_parity': ' '.join(comport_parity),  
#                     # 'comport_stopbit': ' '.join(map(str, comport_stopbit)),  
#                     # 'comport_databit': ' '.join(map(str, comport_databit)),
#                     # 'comport_card': ' '.join(comport_card),
#                 }
#             else:
#                 # If no BackupSettings found, pass empty values
#                 context = {
#                     'backup_date': None,
#                     'confirm_backup': None,
#                     'id': None,
#                     # 'comport_com_port': None,  
#                     # 'ports_string': None,  
#                     # 'comport_baud_rate': None,  
#                     # 'comport_parity': None,  
#                     # 'comport_stopbit': None,  
#                     # 'comport_databit': None,
#                     # 'comport_card': None,
#                 }

#             return render(request, 'app/home.html', context)

#         except Exception as e:
#             return JsonResponse({'error': str(e)}, status=500)


#     return render(request, 'app/home.html')
