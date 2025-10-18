from django.shortcuts import render
import serial 
import serial.tools.list_ports
import json
from django.http import JsonResponse
from app.models import comport_settings
from django.views.decorators.csrf import csrf_exempt

def get_available_com_ports():
    return [port.device for port in serial.tools.list_ports.comports()]

@csrf_exempt  # Add CSRF exemption only if not handling with CSRF token
def comport(request):
    if request.method == 'GET':

        selected_card = request.GET.get('card', '')  # Default value if no card is selected
        
        # You can use this card value for any processing or rendering
        print("Selected card:", selected_card)

        filtered_data = comport_settings.objects.filter(card=selected_card).values(
            'com_port', 'baud_rate', 'bytesize', 'stopbits', 'parity'
        )

         # Convert QuerySet to a list of dictionaries
        filtered_data_list = list(filtered_data)
        print('Your filtered data is:', filtered_data_list)

        # If it's an AJAX request, return JSON response
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'filtered_data': filtered_data_list})

        # Assuming get_available_com_ports() is defined elsewhere to retrieve available COM ports
        com_ports = get_available_com_ports()
        baud_rates = ["4800", "9600", "14400","19200", "38400", "57600", "115200", "128000"]

        
        return render(request, 'app/comport.html', {"com_ports": com_ports, "baud_rates": baud_rates})
    
    elif request.method == 'POST':
        data = json.loads(request.body)

        card_id = data.get('card_id')
        print('card id is received to delete:',card_id)

        if card_id:
            # Delete entries with the matching card_id
            deleted_count, _ = comport_settings.objects.filter(card=card_id).delete()
            
            if deleted_count > 0:
                return JsonResponse({'message': f'Successfully deleted {deleted_count} entries for {card_id}.'})
            else:
                return JsonResponse({'message': f'No records found for {card_id}.'}, status=404)
        
        
        card = data.get('card')  # Retrieve the 'card' value
        com_port = data.get("com_port")
        baud_rate = data.get("baud_rate")
        parity = data.get("parity")
        stopbit = data.get("stopbit")
        databit = data.get("databit")

        print('card value is this:', card)
        print('comport value is :',com_port)
        print('comport value is :',baud_rate)
        print('comport value is :',parity)
        print('comport value is :',stopbit)
        print('comport value is :',databit)

        allowed_cards = ["LVDT_4CH", "PIEZO_4CH", "PIEZO_11CH", "LVDT_8CH"]
        if card not in allowed_cards:
            return JsonResponse({"error": "Invalid card name."}, status=400)


        existing_comport = comport_settings.objects.filter(com_port=com_port).exclude(card=card)
        if existing_comport.exists():
            deleted_count, _ = existing_comport.delete()
            print(f"Deleted {deleted_count} records with com_port: {com_port}")    

        # Try fetching an existing record first
        comport_instance = comport_settings.objects.filter(card=card).first()

        if comport_instance:
            # If it exists, update it
            comport_instance.com_port = com_port
            comport_instance.baud_rate = baud_rate
            comport_instance.bytesize = databit
            comport_instance.stopbits = stopbit
            comport_instance.parity = parity
            comport_instance.save()
        else:
            # If not, create a new one
            comport_instance = comport_settings.objects.create(
                card=card,
                com_port=com_port,
                baud_rate=baud_rate,
                bytesize=databit,
                stopbits=stopbit,
                parity=parity,
            )

        return JsonResponse({"message": "Settings have been updated successfully."})
    
    elif request.method == 'DELETE':  # Handle DELETE request
        comport_settings.objects.all().delete()  # Delete all records
        return JsonResponse({"message": "All COM port settings have been deleted successfully."})


    return JsonResponse({"error": "Invalid request method."}, status=400)

    