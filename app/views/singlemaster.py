from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from app.models import single_master  # Replace with your actual model

@csrf_exempt  # Temporarily disable CSRF for testing (use proper authentication in production)
def singlemaster(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)  # Parse JSON data
            print('your data is this :::',data)

            for item in data.get('data', []):
                single_master.objects.create(
                    parameter_name=item.get('parameterName'),
                    probe_number=item.get('probeNumber'),
                    a=item.get('a'),
                    a1=item.get('a1'),
                    b=item.get('b'),
                    b1=item.get('b1'),
                    e=item.get('e'),
                    d=item.get('d'),
                    o1=item.get('o1'),
                    operator_values=item.get('operatorValues'),
                    shift_values=item.get('shiftValues'),
                    machine_values=item.get('machineValues'),
                    date_time=item.get('dateTime'),
                    selected_value=item.get('selectedValue'),
                    selected_mastering=item.get('selectedMastering'),
                )

            return JsonResponse({'message': 'Data saved successfully'}, status=201)
        
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)

    return JsonResponse({'error': 'Invalid request method'}, status=405)
