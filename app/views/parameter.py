
import json
from django.http import  JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt




@csrf_exempt
def parameter(request):
    from app.models import TableOneData, parameter_settings
    if request.method == 'GET':
        try:
            table_body_1_data = TableOneData.objects.all().order_by('id')

            # Dynamically filter constvalue objects based on the model_id parameter
            model_id = request.GET.get('model_name')
            print('your selected model from the web page is:', model_id)

            # Get the selected parameter name from the request
            parameter_name = request.GET.get('parameter_name')
            print('Your selected parameter from the web page is:', parameter_name)

            # Check if an id is provided in the query parameters
            selected_id = request.GET.get('id')
            print('Selected ID:', selected_id)  # Add this line for debugging

            if selected_id:
                # Fetch the parameter details by ID
                parameter = get_object_or_404(parameter_settings, id=selected_id)

                # Convert parameter details to a dictionary
                parameter_details = {
                    'id': parameter.id,
                    'sr_no': parameter.sr_no, 
                    'parameter_name': parameter.parameter_name,
                    'single_radio': parameter.single_radio,
                    'double_radio': parameter.double_radio,
                    'analog_zero': parameter.analog_zero,
                    'reference_value': parameter.reference_value,
                    'high_mv': parameter.high_mv,
                    'low_mv': parameter.low_mv,
                    'probe_no': parameter.probe_no,
                    'measurement_mode': parameter.measurement_mode,
                    'nominal': parameter.nominal,
                    'usl': parameter.usl,
                    'lsl': parameter.lsl,
                    'mastering': parameter.mastering,
                    'step_no': parameter.step_no,
                    'hide_checkbox': parameter.hide_checkbox,
                    'attribute': parameter.attribute,
                    'utl':parameter.utl,
                    'ltl':parameter.ltl,
                    'digits':parameter.digits,
                    'job_dia':parameter.job_dia,
                    'auto_man':parameter.auto_man,
                    'timer':parameter.timer,
                }

                # Print the parameter details in the terminal
                print('Parameter Details:', parameter_details)

                # Return parameter details as JSON
                return JsonResponse({'parameter_details': parameter_details})

            elif model_id:
                paraname = parameter_settings.objects.filter(model_id=model_id).order_by('id').values('parameter_name', 'id')
                print('your filtered values are:', paraname)
                # Return filtered parameter names as JSON
                return JsonResponse({'paraname': list(paraname)})

            else:
                paraname = []  # If no model is selected, set paraname to an empty list

            context = {
                'table_body_1_data': table_body_1_data,
                'paraname': paraname,
                'selected_model_id': model_id,
            }    

            return render(request, 'app/parameter.html',context)

        except Exception as e:
            print(f'Exception: {e}')
            return render(request, 'app/parameter.html')
            
    elif request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            print('your data recieved from frontend:',data)

            model_id = data.get('modelId')
            parameter_value = data.get('parameterValue')
            sr_no = data.get('srNo')

            # Check if the same parameter_name already exists for the given model_id
            existing_parameter = parameter_settings.objects.filter(
                model_id=model_id, parameter_name=parameter_value
            ).exclude(sr_no=sr_no).first()

            if existing_parameter:
                return JsonResponse({
                    'success': False,
                    'message': f'The parameter name "{parameter_value}" already exists for this "{model_id}".'
                }, status=400)

            # Retrieve or create a new instance
            existing_instance = parameter_settings.objects.filter(model_id=model_id, sr_no=sr_no).first()

            def get_valid_number(value):
                """Convert value to float if it's a valid number, else return 0 (or another default)."""
                try:
                    return float(value) if value and value.strip() else None
                except ValueError:
                    return None

            def get_valid_integer(value):
                """Convert value to int if it's a valid integer, else return 0 (or another default)."""
                try:
                    return int(value) if value and value.strip() else None
                except ValueError:
                    return None

            if existing_instance:
                # Update the existing instance with the received values
                existing_instance.parameter_name = parameter_value
                existing_instance.single_radio = data.get('singleRadio', False)
                existing_instance.double_radio = data.get('doubleRadio', False)

                # Initialize variables
                analog_zero = None
                reference_value = None
                high_mv = None
                low_mv = None

                # Handle conditional values based on radio button selection
                if existing_instance.single_radio:
                    analog_zero = get_valid_number(data.get('analogZero', ''))
                    reference_value = get_valid_number(data.get('referenceValue', ''))
                elif existing_instance.double_radio:
                    high_mv = get_valid_number(data.get('highMV', ''))
                    low_mv = get_valid_number(data.get('lowMV', ''))

                existing_instance.analog_zero = analog_zero
                existing_instance.reference_value = reference_value
                existing_instance.high_mv = high_mv
                existing_instance.low_mv = low_mv

                # Handle other fields
                existing_instance.probe_no = data.get('probeNo', '')
                existing_instance.measurement_mode = data.get('measurementMode', '')
                existing_instance.nominal = get_valid_number(data.get('nominal', ''))
                existing_instance.usl = get_valid_number(data.get('usl', ''))
                existing_instance.lsl = get_valid_number(data.get('lsl', ''))
                existing_instance.mastering = get_valid_number(data.get('mastering', ''))
                existing_instance.step_no = get_valid_number(data.get('stepNo', ''))
                existing_instance.hide_checkbox = data.get('hideCheckbox', False)
                existing_instance.attribute = data.get('attribute', False)
                existing_instance.utl = get_valid_number(data.get('utl', ''))
                existing_instance.ltl = get_valid_number(data.get('ltl', ''))
                existing_instance.digits = get_valid_integer(data.get('digits', ''))
                existing_instance.job_dia = data.get('job_dia', '')
                existing_instance.auto_man = data.get('auto_man', False)
                existing_instance.timer = data.get('timer', '')

                existing_instance.save()

                return JsonResponse({'success': True, 'message': 'Parameter updated successfully.'})

            else:
                # Create a new instance with the received values
                single_radio = data.get('singleRadio', False)
                double_radio = data.get('doubleRadio', False)

                # Initialize variables
                analog_zero = None
                reference_value = None
                high_mv = None
                low_mv = None

                if single_radio:
                    analog_zero = get_valid_number(data.get('analogZero', ''))
                    reference_value = get_valid_number(data.get('referenceValue', ''))
                elif double_radio:
                    high_mv = get_valid_number(data.get('highMV', ''))
                    low_mv = get_valid_number(data.get('lowMV', ''))

                const_value_instance = parameter_settings.objects.create(
                    model_id=model_id,
                    parameter_name=parameter_value,
                    sr_no=sr_no,
                    single_radio=single_radio,
                    double_radio=double_radio,
                    analog_zero=analog_zero,
                    reference_value=reference_value,
                    high_mv=high_mv,
                    low_mv=low_mv,
                    probe_no=data.get('probeNo', ''),
                    measurement_mode=data.get('measurementMode', ''),
                    nominal=get_valid_number(data.get('nominal', '')),
                    usl=get_valid_number(data.get('usl', '')),
                    lsl=get_valid_number(data.get('lsl', '')),
                    mastering=get_valid_number(data.get('mastering', '')),
                    step_no=get_valid_number(data.get('stepNo', '')),
                    hide_checkbox=data.get('hideCheckbox', False),
                    attribute=data.get('attribute', False),
                    utl=get_valid_number(data.get('utl', '')),
                    ltl=get_valid_number(data.get('ltl', '')),
                    digits=get_valid_integer(data.get('digits', '')),
                    job_dia=data.get('job_dia', ''),
                     auto_man=data.get('auto_man', False),
                    timer=get_valid_number(data.get('timer', '')),
                )

                return JsonResponse({'success': True, 'message': 'Parameter created successfully.'})

        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})



            
    elif request.method == 'DELETE':
        try:
            # Check if an ID is provided in the query parameters
            selected_id = request.GET.get('id')
            print('Selected ID:', selected_id)

            if selected_id:
                # Fetch the parameter details by ID
                parameter = get_object_or_404(parameter_settings, id=selected_id)

                # Get the model_id and sr_no before deletion
                model_id = parameter.model_id
                sr_no = parameter.sr_no

                # Delete the parameter
                parameter.delete()

                print(f'Parameter with ID {selected_id} deleted successfully.')
                # Adjust sr_no values for the remaining parameters of the same model
                remaining_parameters = parameter_settings.objects.filter(model_id=model_id).order_by('sr_no')
                for index, remaining_param in enumerate(remaining_parameters, start=1):
                    if remaining_param.sr_no != index:
                        remaining_param.sr_no = index
                        remaining_param.save()

                return JsonResponse({'success': True, 'message': f'Parameter with ID {selected_id} deleted successfully.'})

            else:
                return JsonResponse({'success': False, 'message': 'ID not provided in the query parameters.'})

        except Exception as e:
            print(f'Exception: {e}')
            return JsonResponse({'success': False, 'message': str(e)})

   
    return render(request, 'app/parameter.html')


"""
1.get_object_or_404 : is a shortcut function in Django used to retrieve an object from the database

2.CSRF (Cross-Site Request Forgery)
  csrf_exempt in Django disables CSRF protection for a specific view, allowing requests to bypass CSRF token validation.

"""
