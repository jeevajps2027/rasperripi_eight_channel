from datetime import datetime

import json

from django.http import JsonResponse
from django.shortcuts import render

from app.models import MeasurementData, TableFourData, TableOneData, TableThreeData, TableTwoData, measure_data


def measurebox(request):

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            part_model = data.get('partModel')
            operator = data.get('operator')
            machine = data.get('machine')
            # shift = data.get('shift')

            # Save the data to the database
# Get or create a measureBox_data object with id=1
            measure, created = measure_data.objects.get_or_create(id=1, defaults={
                'part_model': part_model,
                'operator': operator,
                'machine': machine,
                # 'shift': shift
            })

            # If the object already exists, update its fields
            if not created:
                measure.part_model = part_model
                measure.operator = operator
                measure.machine = machine
                # measure.shift = shift
                measure.save()

            print('measure data is:', measure)
            
            return JsonResponse({'status': 'success'})
        except json.JSONDecodeError as e:
            return JsonResponse({'error': 'Invalid JSON format in the request body'}, status=400)


    elif request.method == 'GET':
        try:
            part_model_values = TableOneData.objects.order_by('id').values_list('part_model', flat=True).distinct()
            print('part_model_values:', part_model_values)

            operator_values = TableFourData.objects.order_by('id').values_list('operator_name', flat=True).distinct()
            print('operator_values:', operator_values)

            batch_no_values = TableTwoData.objects.order_by('id').values_list('batch_no', flat=True).distinct()
            print('batch_no_values:', batch_no_values)

            machine_name_values = TableThreeData.objects.order_by('id').values_list('machine_name', flat=True).distinct()
            print('machine_name_values:', machine_name_values)

            customer_name_values = TableOneData.objects.order_by('id').values_list('customer_name', flat=True).distinct()
            print('customer_name_values:', customer_name_values)

            # Retrieve the first instance of measure_data ordered by id
            current_selection = measure_data.objects.order_by('id').first()
            
            context = {
                'part_model_values': part_model_values,
                'operator_values': operator_values,
                'batch_no_values': batch_no_values,
                'machine_name_values': machine_name_values,
                'customer_name_values': customer_name_values,
                'current_selection': current_selection,

            }

        except json.JSONDecodeError as e:
            return JsonResponse({'error': 'Invalid JSON format in the request body'}, status=400)
    return render(request,'app/measurebox.html',context)

