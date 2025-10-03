import json
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render

from app.models import comport_settings


def probe(request):
    from app.models import probe_calibrations
    if request.method == 'POST':
        probe_id = request.POST.get('probeId')
        a_values = [float(value) for value in request.POST.getlist('a[]')]
        a1_values = [float(value) for value in request.POST.getlist('a1[]')]
        b_values = [float(value) for value in request.POST.getlist('b[]')]
        b1_values = [float(value) for value in request.POST.getlist('b1[]')]
        e_values = [float(value) for value in request.POST.getlist('e[]')]

        print('THESE ARE THE DATA YOU WANT TO DISPLAY:', probe_id, a_values, a1_values, b_values, b1_values, e_values)

        probe, created = probe_calibrations.objects.get_or_create(probe_id=probe_id)

        probe.low_ref = a_values[0] if a_values else None
        probe.low_count = a1_values[0] if a1_values else None
        probe.high_ref = b_values[0] if b_values else None
        probe.high_count = b1_values[0] if b1_values else None
        probe.coefficent = e_values[0] if e_values else None

        probe.save()
        

        low_count = probe.low_count
        coefficient = probe.coefficent

        # Print the values in the terminal (server side)
        print(f'Retrieved values for probe {probe_id}:')
        print(f'Low Count: {low_count}')
        print(f'Coefficient: {coefficient}')

        # Send the retrieved values back as a JSON response
        return JsonResponse({
            'probe_id': probe_id,
            'low_count': low_count,
            'coefficient': coefficient
        })

    


    

# In your view:
    elif request.method == 'GET':
        # Retrieve the distinct probe IDs
        probe_ids = probe_calibrations.objects.values_list('probe_id', flat=True).distinct().order_by('probe_id')

        settings_list = list(comport_settings.objects.values(
            'card', 'com_port', 'baud_rate', 'bytesize', 'stopbits', 'parity'
        ))

        # Create dictionaries to store coefficient and low count values for each probe ID
        probe_coefficients = {}
        low_count = {}

        for probe_id in probe_ids:
            # Retrieve the latest calibration for the current probe ID
            latest_calibration = probe_calibrations.objects.filter(probe_id=probe_id).latest('id')

            # Extract the coefficient and low count values
            coefficient_value = latest_calibration.coefficent
            low_value = latest_calibration.low_count

            # Store the coefficient and low count values in the dictionaries with the probe ID as the key
            probe_coefficients[probe_id] = coefficient_value
            low_count[probe_id] = low_value

        # Convert dictionaries to JSON strings
        probe_coefficients_json = json.dumps(probe_coefficients)
        low_count_json = json.dumps(low_count)

        print('your probecoefficent values for probes:',probe_coefficients_json)
        print('your lowcount values for probes:',low_count_json)
        context = {
            'probe_coefficients_json': probe_coefficients_json ,
            'low_count_json':low_count_json ,
             'settings_json': json.dumps(settings_list),
        }

    return render(request, 'app/probe.html',context)