from datetime import datetime
import json
import threading

from django.http import JsonResponse
from django.shortcuts import render


from app.models import measure_data, parameter_settings,Master_settings



def measure(request):
    if request.method == 'POST':
        try:
            # Retrieve the data from the request body
            data = json.loads(request.body.decode('utf-8'))
            print("data", data)
            
            # Extract fields
            selected_value = data.get('selectedValue')
                        
            dataArray = data.get('data', [])
            print("data array",dataArray)

            for row in dataArray:
                # Access fields
                parameterName = row.get('parameterName')
                probeNumber = row.get('probeNumber')
                a = row.get('a')
                a1 = row.get('a1')
                b = row.get('b')
                b1 = row.get('b1')
                e = row.get('e')
                d = row.get('d')
                o1 = row.get('o1')
                operatorValues = row.get('operatorValues')
                shiftValues = row.get('shiftValues')
                machineValues = row.get('machineValues')
                dateTime = row.get('dateTime')
                selectedValue = row.get('selectedValue')
                selectedMastering = row.get('selectedMastering')

              
                 # Convert date string to naive datetime object
                date_obj = datetime.strptime(dateTime, '%d/%m/%Y %I:%M:%S %p')
                print("date_obj", date_obj)

               

               
                print("parameterName",parameterName)
                print("probeNumber",probeNumber)
                print("a",a)
                print("a1",a1)
                print("b",b)
                print("b1",b1)
                print("e",e)
                print("d",d)
                print("o1",o1)
                print("operatorValues",operatorValues)
                print("shiftValues",shiftValues)
                print("machineValues",machineValues)
                print("selected values:",selectedValue)
                print("selectedMastering",selectedMastering)

                # Save each row to the Master_settings model
                Master_settings.objects.create(
                    probe_no=probeNumber,
                    a=a,
                    a1=a1,
                    b=b,
                    b1=b1,
                    e=e,
                    d=d,
                    o1=o1,
                    parameter_name=parameterName,
                    selected_value=selectedValue,
                    selected_mastering=selectedMastering,
                    operator=operatorValues,
                    shift=shiftValues,
                    machine=machineValues,
                    date_time=date_obj,
                )

           # Filtering logic based on selected_value and selected_mastering
            filtered_data = parameter_settings.objects.filter(
                model_id=selected_value,
                hide_checkbox=False,
                attribute=False
            ).exclude(
                measurement_mode__in=["TIR", "TAP"]  # Exclude records with "TIR" or "TAP" in measurement_mode
            ).values().order_by('id')

            # Fetching data from Master_settings
            last_stored_parameter = {
                item['parameter_name']: item 
                for item in Master_settings.objects.filter(
                    selected_value=selected_value, 
                    parameter_name__in=filtered_data.values_list('parameter_name', flat=True)
                ).values()
            }
            

            # Print e, d, and o1 values
            for param_name, values in last_stored_parameter.items():
                id = values.get('id')
                e = values.get('e')
                d = values.get('d')
                o1 = values.get('o1')
                print(f"Parameter: {param_name}, id:{id}, e: {e}, d: {d}, o1: {o1}")


            response_data = {
                'message': 'Successfully received the selected values.',
                'selectedValue': selected_value,
                'parameter_names': [item['parameter_name'] for item in filtered_data],
                'low_mv': [item['low_mv'] for item in filtered_data],
                'high_mv': [item['high_mv'] for item in filtered_data],
                'probe_no': [item['probe_no'] for item in filtered_data],
                'mastering': [item['mastering'] for item in filtered_data],
                'nominal': [item['nominal'] for item in filtered_data],
                'lsl': [item['lsl'] for item in filtered_data],
                'usl': [item['usl'] for item in filtered_data],
                'utl': [item['utl'] for item in filtered_data],
                'ltl': [item['ltl'] for item in filtered_data],
                'job_dia':[item['job_dia'] for item in filtered_data],
                'digits': [item['digits'] for item in filtered_data],
                'e_values': [values.get('e') for values in last_stored_parameter.values()],
                'd_values': [values.get('d') for values in last_stored_parameter.values()],
                'o1_values': [values.get('o1') for values in last_stored_parameter.values()],
                'id': [values.get('id') for values in last_stored_parameter.values()]
            
            }

            return JsonResponse(response_data)
        
        except json.JSONDecodeError as e:
            return JsonResponse({'error': 'Invalid JSON format in the request body'}, status=400)
        except Exception as e:
            print(f"Unexpected error: {e}")
            return JsonResponse({'error': 'Internal Server Error'}, status=500)
        
    elif request.method == 'GET':
        try:

            # Your initial queryset for part_model_values
            part_model_values = measure_data.objects.values_list('part_model', flat=True).distinct()
            print('part_model_values:', part_model_values)

            operator_values = ', '.join(measure_data.objects.values_list('operator', flat=True))
            print('operator_values:', operator_values)

            shift_values = ', '.join(measure_data.objects.values_list('shift', flat=True))
            print('shift_values:', shift_values)

            machine_values = ', '.join(measure_data.objects.values_list('machine', flat=True))
            print('machine_values:', machine_values)

            context = {
                'part_model_values': part_model_values,
                'operator_values': operator_values,
                'shift_values': shift_values,
                'machine_values':machine_values,

            }

        except Exception as e:
            print(f'Exception: {e}')
            return JsonResponse({'key': 'value'})
        
    
   
    return render(request, 'app/measure.html', context)
