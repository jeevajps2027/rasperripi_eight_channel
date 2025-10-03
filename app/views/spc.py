
import json
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt 
from openpyxl import Workbook



@csrf_exempt
def spc(request):
    from app.models import MeasurementData, TableFiveData,parameter_settings,TableOneData,TableThreeData,TableTwoData,TableFourData
    from app.models import X_Bar_Chart,X_Bar_R_Chart,X_Bar_S_Chart,Histogram_Chart,Pie_Chart,ShiftSettings
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            print("data:",data)
            part_model = data.get('partModel')
            print(part_model)
            form_id = data.get('itemId')
            print("form_id:",form_id)
            if form_id == 'x_bar_chart':
                partModel = data.get('partModel')
                parameterName = data.get('parameter_name')
                operator = data.get('operator')
                formatted_from_date = data.get('from_date')
                formatted_to_date = data.get('to_date')
                machine = data.get('machine')
                vendor_code = data.get('vendor_code')
                shift = data.get('shift')
                current_date_time = data.get('currentDateTime')

                # Get or create consolidate_with_srno instance with id=1
                instance, created = X_Bar_Chart.objects.get_or_create(id=1)

                # Update the instance with the new data
                instance.part_model = partModel
                instance.parameter_name = parameterName
                instance.operator = operator
                instance.formatted_from_date = formatted_from_date
                instance.formatted_to_date = formatted_to_date
                instance.machine = machine
                instance.vendor_code = vendor_code
                instance.shift = shift
                instance.current_date_time = current_date_time

                # Save the instance
                instance.save()
            elif form_id == 'x_bar_r_chart':
                partModel = data.get('partModel')
                parameterName = data.get('parameter_name')
                operator = data.get('operator')
                formatted_from_date = data.get('from_date')
                formatted_to_date = data.get('to_date')
                machine = data.get('machine')
                vendor_code = data.get('vendor_code')
                sample_size = data.get('sample_size')
                shift = data.get('shift')
                current_date_time = data.get('currentDateTime')

                 # Get or create consolidate_with_srno instance with id=1
                instance, created = X_Bar_R_Chart.objects.get_or_create(id=1)

                # Update the instance with the new data
                instance.part_model = partModel
                instance.parameter_name = parameterName
                instance.operator = operator
                instance.formatted_from_date = formatted_from_date
                instance.formatted_to_date = formatted_to_date
                instance.machine = machine
                instance.vendor_code = vendor_code
                instance.sample_size = sample_size
                instance.shift = shift
                instance.current_date_time = current_date_time

                # Save the instance
                instance.save()
            elif form_id == 'x_bar_s_chart':
                partModel = data.get('partModel')
                parameterName = data.get('parameter_name')
                operator = data.get('operator')
                formatted_from_date = data.get('from_date')
                formatted_to_date = data.get('to_date')
                machine = data.get('machine')
                vendor_code = data.get('vendor_code')
                sample_size = data.get('sample_size')
                shift = data.get('shift')
                current_date_time = data.get('currentDateTime')

                # Get or create consolidate_with_srno instance with id=1
                instance, created = X_Bar_S_Chart.objects.get_or_create(id=1)

                # Update the instance with the new data
                instance.part_model = partModel
                instance.parameter_name = parameterName
                instance.operator = operator
                instance.formatted_from_date = formatted_from_date
                instance.formatted_to_date = formatted_to_date
                instance.machine = machine
                instance.vendor_code = vendor_code
                instance.sample_size = sample_size
                instance.shift = shift
                instance.current_date_time = current_date_time

                # Save the instance
                instance.save()
            elif form_id == 'histogram':
                partModel = data.get('partModel')
                parameterName = data.get('parameter_name')
                operator = data.get('operator')
                formatted_from_date = data.get('from_date')
                formatted_to_date = data.get('to_date')
                machine = data.get('machine')
                vendor_code = data.get('vendor_code')
                sample_size = data.get('sample_size')
                shift = data.get('shift')
                current_date_time = data.get('currentDateTime')

                # Get or create consolidate_with_srno instance with id=1
                instance, created = Histogram_Chart.objects.get_or_create(id=1)

                # Update the instance with the new data
                instance.part_model = partModel
                instance.parameter_name = parameterName
                instance.operator = operator
                instance.formatted_from_date = formatted_from_date
                instance.formatted_to_date = formatted_to_date
                instance.machine = machine
                instance.vendor_code = vendor_code
                instance.sample_size = sample_size
                instance.shift = shift
                instance.current_date_time = current_date_time

                # Save the instance
                instance.save()
            
            elif form_id == 'pie_chart':
                partModel = data.get('partModel')
                parameterName = data.get('parameter_name')
                operator = data.get('operator')
                formatted_from_date = data.get('from_date')
                formatted_to_date = data.get('to_date')
                machine = data.get('machine')
                vendor_code = data.get('vendor_code')
                sample_size = data.get('sample_size')
                shift = data.get('shift')
                current_date_time = data.get('currentDateTime')

                # Get or create consolidate_with_srno instance with id=1
                instance, created = Pie_Chart.objects.get_or_create(id=1)

                # Update the instance with the new data
                instance.part_model = partModel
                instance.parameter_name = parameterName
                instance.operator = operator
                instance.formatted_from_date = formatted_from_date
                instance.formatted_to_date = formatted_to_date
                instance.machine = machine
                instance.vendor_code = vendor_code
                instance.sample_size = sample_size
                instance.shift = shift
                instance.current_date_time = current_date_time

                # Save the instance
                instance.save()

                

            

            # Filter parameter_settings where model_id matches part_model and get distinct parameter_name
            parameter_data = parameter_settings.objects.order_by('id').filter(model_id=part_model).values_list('parameter_name', flat=True).distinct()
            print('Filtered parameter_name:', parameter_data)

            punch_data = MeasurementData.objects.filter(part_model=part_model).values_list('comp_sr_no', flat=True).distinct()
            print('your component_serial_number from that views:',punch_data)
                        
             # Prepare the response data
            response_data = {
                'status': 'success',
                'message': f"Received model: {part_model}",
                'parameter_names': list(parameter_data),
                'component_serial_numbers': list(punch_data)
            }
            return JsonResponse(response_data)
        except json.JSONDecodeError:
            response = {'status': 'error', 'message': 'Invalid JSON'}
            return JsonResponse(response, status=400)
         
    elif request.method == 'GET':
        try:
            model_data = TableOneData.objects.order_by('id').values_list('part_model', flat=True).distinct()
            print('your part_model from that views:',model_data)
            
            machine_data = TableThreeData.objects.order_by('id').values_list('machine_name', flat=True).distinct()
            print('your part_model from that views:',machine_data)
            
            shift_data = TableTwoData.objects.order_by('id').values_list('batch_no', flat=True).distinct()
            print('your part_model from that views:',shift_data)
            
            operator_data = TableFourData.objects.order_by('id').values_list('operator_name', flat=True).distinct()
            print('your part_model from that views:',operator_data)
            
           
            vendor_data = TableFiveData.objects.order_by('id').values_list('vendor_code', flat=True).distinct()
            print('your vendor from that views:',vendor_data)

            shift_values = ShiftSettings.objects.order_by('id').values_list('shift', 'shift_time').distinct()
    
            # Convert the QuerySet to a list of lists
            shift_values_list = list(shift_values)
            
            # Serialize the list to JSON
            shift_values_json = json.dumps(shift_values_list)
            print("shift_values_json",shift_values_json)
            
            # Create a context dictionary to pass the data to the template
            context = {
                'model_data' : model_data,
                'machine_data' : machine_data,
                'shift_data' : shift_data,
                'operator_data' : operator_data,
                'vendor_data' : vendor_data,
                'shift_values': shift_values_json,

            }
        except json.JSONDecodeError as e:
            return JsonResponse({'error': 'Invalid JSON format in the request body'}, status=400)    
    # Render the template with the context
    return render(request, 'app/spc.html', context)
