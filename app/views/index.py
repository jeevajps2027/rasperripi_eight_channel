import json
from django.shortcuts import render
from app.models import comport_settings,TableFourData
import serial.tools.list_ports
from django.views.decorators.csrf import csrf_exempt

def get_available_com_ports():
    return [port.device for port in serial.tools.list_ports.comports()]


def index(request):
    from app.models import UserLogin 
    if request.method == 'GET':
        ports_string = ''

        # Convert QuerySet values to lists
        comport_settings_qs = comport_settings.objects.exclude(card="PLC")  # Exclude PLC card
        comport_com_port = list(comport_settings_qs.values_list('com_port', flat=True))
        comport_baud_rate = list(comport_settings_qs.values_list('baud_rate', flat=True))
        comport_parity = list(comport_settings_qs.values_list('parity', flat=True))
        comport_stopbit = list(comport_settings_qs.values_list('stopbits', flat=True))
        comport_databit = list(comport_settings_qs.values_list('bytesize', flat=True))
        comport_card = list(comport_settings_qs.values_list('card', flat=True))

        print('Filtered cards (excluding PLC):', comport_card)
        print('Filtered baud_rate:', comport_baud_rate)
        print('Filtered COM ports:', comport_com_port)

        com_ports = get_available_com_ports()
        print('Available COM ports:', com_ports)

        if com_ports:
            matching_ports = [port for port in comport_com_port if port in com_ports]
            ports_string = ' '.join(matching_ports) if matching_ports else ' '.join(com_ports)
            print('Matching COM ports:', ports_string)
        else:
            ports_string = 'No COM ports available'
            print(ports_string)

        # Query all UserLogin entries
        user_logins = UserLogin.objects.all()
        user_logins_list = list(user_logins.values())
        user_logins_json = json.dumps(user_logins_list)

        operators = TableFourData.objects.all().values('operator_name', 'operator_no')
    # Convert to JSON
        user_logins_json = json.dumps(list(operators))

        # --- Fetch Logged-in User from Session ---
        logged_in_user = request.session.get('username', None)
        print("logged_in_user",logged_in_user)

        # Context with filtered data
        context = {
            'user_logins_json': user_logins_json,
            'comport_com_port': ' '.join(comport_com_port),
            'ports_string': ports_string,
            'comport_baud_rate': ' '.join(map(str, comport_baud_rate)),
            'comport_parity': ' '.join(comport_parity),
            'comport_stopbit': ' '.join(map(str, comport_stopbit)),
            'comport_databit': ' '.join(map(str, comport_databit)),
            'comport_card': ' '.join(map(str, comport_card)),
           'user_logins_json': user_logins_json,
           'logged_in_user':logged_in_user,
        }
        print("Context:", context)
        return render(request, 'app/index.html', context)

