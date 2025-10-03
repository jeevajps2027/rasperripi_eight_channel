from datetime import datetime
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from app.models import MeasurementData, TableClearFlag, parameter_settings
from collections import defaultdict
from django.db.models import Count
from django.db.models import Max

@csrf_exempt
def measurement_data_retrive(request):
    if request.method == 'POST':
        input_date = request.POST.get('date')
        input_shift = request.POST.get('shift')
        input_partModel = request.POST.get('part_model')
        

        print("Received Date:", input_date)
        print("Received Shift:", input_shift)
        print("Received partModel :", input_partModel)

        parameter_settings_qs = parameter_settings.objects.filter(model_id=input_partModel, hide_checkbox=False,attribute=False).values_list('parameter_name', flat=True).order_by('id')
        print("parameter_settings_qs",parameter_settings_qs)


        formatted_date = None
        if input_date:
            try:
                input_date_obj = datetime.strptime(input_date, '%Y/%m/%d %I:%M:%S %p')
                formatted_date = input_date_obj.date().strftime('%Y-%m-%d')
            except ValueError as e:
                print(f"Error parsing date: {e}")

        # ---- Query for aggregated counts (your original logic) ----
        filtered_data = (
            MeasurementData.objects
            .filter(part_model=input_partModel, date__date=formatted_date, shift=input_shift)
            .values('date', 'part_status')
            .annotate(count=Count('part_status'))
            .order_by('date')
        )

        print('your data for filtered data is this:', filtered_data)

        distinct_status_counts = defaultdict(int)
        status_with_datetime = defaultdict(list)
        last_occurrence = {'accept': None, 'reject': None, 'rework': None}
        total_occurrence = 0

        for entry in filtered_data:
            status = entry['part_status'].lower()
            date_time = entry['date']
            formatted_date_time = date_time.strftime('%d/%m/%Y %I:%M:%S %p')

            distinct_status_counts[status] += 1

            status_with_datetime[formatted_date_time].append({
                'status': status,
                'count': entry['count'],
                'occurrence': distinct_status_counts[status]
            })

            if status in last_occurrence:
                last_occurrence[status] = {
                    'formatted_date': formatted_date_time,
                    'count': entry['count'],
                    'occurrence': distinct_status_counts[status]
                }

        for status in ['accept', 'reject', 'rework']:
            occurrence = last_occurrence[status]
            if occurrence:
                total_occurrence += occurrence['occurrence']

        print("\nLast Occurrence for Each Status:")
        for status in ['accept', 'reject', 'rework']:
            occurrence = last_occurrence[status]
            if occurrence:
                print(f"{status.capitalize()} -> {occurrence}")
        print(f"\nTotal Occurrence: {total_occurrence}")

        # Get last 5 records
        last_five = (
            MeasurementData.objects
            .filter(part_model=input_partModel, date__date=formatted_date, shift=input_shift)
            .order_by('-date')[:5]   # get last 5 by date
        )
        print('Last five data :', last_five)

        # Check if all last 5 records are 'reject' (or whatever status you want)
        reject_in_last_five = all(obj.part_status.lower() == 'reject' for obj in last_five)

        notification_message = ""
        if reject_in_last_five and last_five:
            notification_message = "YOUR LAST 5 JOBS ARE REJECTED PLEASE CHECK"
            print("notification_message",notification_message)

        


        # 2. Get the last `id` for each parameter_name in MeasurementData
        latest_measurements = (
            MeasurementData.objects.filter(
                part_model=input_partModel,
                parameter_name__in=parameter_settings_qs 
            )
            .values('parameter_name')
            .annotate(last_id=Max('id'))
        )

        # 3. Build a dictionary of last records with required fields
        last_measurement_dict = {}
        for entry in latest_measurements:
            param_name = entry['parameter_name']
            last_id = entry['last_id']

            last_record = MeasurementData.objects.filter(id=last_id).values(
                'id', 'parameter_name', 'readings', 'status_cell'
            ).first()

            if last_record:
                last_measurement_dict[param_name] = last_record

        # 4. Format and print the result
        for param_name, values in last_measurement_dict.items():
            print(
                f"Parameter : {param_name}, ID : {values['id']}, "
                f"Output : {values['readings']}, status_cell : {values['status_cell']}, "
                
            )

        # Format the parameter_name values
        measurement_values = [
            {
                "parameter_name": param_name,
                "id": values.get("id"),
                "output": values.get("readings"),
                "status_cell": values.get("status_cell"),
                
            }
            for param_name, values in last_measurement_dict.items()
        ]
        # Convert queryset to list for JSON serialization
        parameter_settings_list = list(parameter_settings_qs)

        try:
            flag = TableClearFlag.objects.get(id=1)
            clear_flag_value = flag.clear_table
        except TableClearFlag.DoesNotExist:
            clear_flag_value = False  # fallback




        # ---- Prepare Response ----
        response_data = {
            
            "measurement_data": measurement_values, 
            "clear_flag_value":clear_flag_value,
            "parameter_settings_list":parameter_settings_list,
        }

       


        return JsonResponse(response_data)

    return render(request, "app/measurement.html")