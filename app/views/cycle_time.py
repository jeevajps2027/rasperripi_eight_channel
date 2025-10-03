# views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from app.models import TimeSetting

@csrf_exempt
def save_time(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        start_time = data.get('start_time')
        stop_time = data.get('stop_time')

        # Either update existing record or create new one
        time_record, created = TimeSetting.objects.get_or_create(id=1)
        time_record.start_time = start_time
        time_record.stop_time = stop_time
        time_record.save()

        return JsonResponse({'status': 'success', 'message': 'Time saved successfully!'})

def get_time(request):
    try:
        obj = TimeSetting.objects.get(id=1)
        print('your object is this :', obj)
        print('Returning JSON:', {'start_time': obj.start_time, 'stop_time': obj.stop_time})
        return JsonResponse({
            'start_time': obj.start_time,
            'stop_time': obj.stop_time,
        })
    except TimeSetting.DoesNotExist:
        print('No object found with id=1')
        return JsonResponse({'start_time': '', 'stop_time': ''})

