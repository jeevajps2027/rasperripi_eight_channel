import json
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt




@csrf_exempt
def trace(request, row_id=None):
    from app.models import TableFiveData, TableFourData, TableOneData, TableThreeData, TableTwoData, Master_settings, parameter_settings,MeasurementData,ShiftSettings
    if request.method == 'POST':
        try:
              # Ensure the request body is not empty
            if not request.body:
                return JsonResponse({'error': 'Empty request body'}, status=400)

            received_data = json.loads(request.body)
            print('received_data', received_data)

            if not received_data:
                return JsonResponse({'error': 'Invalid or empty data'}, status=400)


            if 'rowId' in received_data:
                row_id = received_data['rowId']
                print('row_id:', row_id)

                table_body_id = received_data.get('tableBodyId')
                print('your table_body_id is:',table_body_id)
                values = received_data.get('values')

                if table_body_id and values:
                    if table_body_id == 'tableBody-1':
                        try:
                            table_data = TableOneData.objects.get(pk=row_id)
                            table_data.part_model = values[0]
                            table_data.customer_name = values[1]
                            table_data.part_name = values[2]
                            table_data.part_no = values[3]
                            table_data.char_lmt = values[4]
                            table_data.hide = values[5]
                            table_data.save()
                            return JsonResponse({'message': 'Data updated successfully'}, status=200)
                        except TableOneData.DoesNotExist:
                            pass
                    elif table_body_id == 'tableBody-2':
                        try:
                            table_data = TableTwoData.objects.get(pk=row_id)
                            table_data.batch_no = values[0]
                            table_data.save()
                            return JsonResponse({'message': 'Data updated successfully'}, status=200)
                        except TableTwoData.DoesNotExist:
                            pass
                    elif table_body_id == 'tableBody-3':
                        try:
                            table_data = TableThreeData.objects.get(pk=row_id)
                            table_data.machine_no = values[0]
                            table_data.machine_name = values[1]
                            table_data.save()
                            return JsonResponse({'message': 'Data updated successfully'}, status=200)
                        except TableThreeData.DoesNotExist:
                            pass
                    elif table_body_id == 'tableBody-4':
                        try:
                            table_data = TableFourData.objects.get(pk=row_id)
                            table_data.operator_no = values[0]
                            table_data.operator_name = values[1]
                            table_data.save()
                            return JsonResponse({'message': 'Data updated successfully'}, status=200)
                        except TableFourData.DoesNotExist:
                            pass
                    elif table_body_id == 'tableBody-5':
                        try:
                            table_data = TableFiveData.objects.get(pk=row_id)
                            table_data.vendor_code = values[0]
                            table_data.email = values[1]
                            table_data.save()
                            return JsonResponse({'message': 'Data updated successfully'}, status=200)
                        except TableFiveData.DoesNotExist:
                            pass

                return JsonResponse({'message': 'Record with provided rowId does not exist'}, status=404)

            # Code to handle creation of new records
            # This part of the code is based on your previous logic
            # It will create new records if the 'rowId' is not provided in the received data
            else:
                if received_data:
                    for item_id, rows in received_data.items():
                        for row in rows:
                            values = row['values']
                            if item_id == 'tableBody-1':
                                table_data = TableOneData.objects.create(
                                    part_model=values[0],
                                    customer_name=values[1],
                                    part_name=values[2],
                                    part_no=values[3],
                                    char_lmt=values[4],
                                    hide=values[5]
                                )
                            elif item_id == 'tableBody-2':
                                table_data = TableTwoData.objects.create(
                                    batch_no=values[0]
                                )
                            elif item_id == 'tableBody-3':
                                table_data = TableThreeData.objects.create(
                                    machine_no=values[0],
                                    machine_name=values[1]
                                )
                            elif item_id == 'tableBody-4':
                                table_data = TableFourData.objects.create(
                                    operator_no=values[0],
                                    operator_name=values[1]
                                )
                            elif item_id == 'tableBody-5':
                                table_data = TableFiveData.objects.create(
                                    vendor_code=values[0],
                                    email=values[1]
                                )
                            table_data.save()

                    return JsonResponse({'message': 'New record(s) created successfully'}, status=201)
                else:
                    return JsonResponse({'message': 'No data provided'}, status=400)

        except json.decoder.JSONDecodeError:
            return JsonResponse({'message': 'Invalid JSON format'}, status=400)
        except Exception as e:
            print('Error:', e)
            return JsonResponse({'error': 'An error occurred'}, status=500)

        

    elif request.method == 'GET':
        try:
            # Fetch stored data for tableBody-1 from your database or any storage mechanism
            # Replace this with your actual logic to fetch data for tableBody-1
            table_body_1_data = TableOneData.objects.all().order_by('id')
            table_body_2_data = TableTwoData.objects.all().order_by('id')
            table_body_3_data = TableThreeData.objects.all().order_by('id')
            table_body_4_data = TableFourData.objects.all().order_by('id')
            table_body_5_data = TableFiveData.objects.all().order_by('id')
            # Pass the retrieved data for tableBody-1 to the template for rendering
            return render(request, 'app/trace.html', {'table_body_1_data': table_body_1_data,'table_body_2_data':table_body_2_data,'table_body_3_data': table_body_3_data,'table_body_4_data': table_body_4_data,'table_body_5_data': table_body_5_data})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    elif request.method == 'DELETE':
        try:
            received_data = json.loads(request.body)

            for item_id, row_ids in received_data.items():
                print(f"Deleting rows with IDs {row_ids} from {item_id}")

                # Depending on the item_id, fetch the rows from the database
                if item_id == 'tableBody-1':
                    rows = TableOneData.objects.filter(id__in=row_ids)
                    # Print the column values of each row before deleting
                    for row in rows:
                        part_model_value = row.part_model
                        delete_parameter = parameter_settings.objects.filter(model_id=part_model_value).delete()
                        delete_master = Master_settings.objects.filter(selected_value=part_model_value).delete()
                        delete_measurement = MeasurementData.objects.filter(part_model=part_model_value).delete()

                elif item_id == 'tableBody-2':
                    rows = TableTwoData.objects.filter(id__in=row_ids)

                    for row in rows:
                        print(f"Received row: ID={row.id}, batch_no={row.batch_no}")

                        # Find matching ShiftSettings (shift == batch_no)
                        matching_shifts = ShiftSettings.objects.filter(shift=row.batch_no)
                        if matching_shifts.exists():
                            print(f"Deleting matching ShiftSettings for batch_no={row.batch_no}")
                            matching_shifts.delete()
                        else:
                            print(f"No ShiftSettings found for batch_no={row.batch_no}")

                    # finally delete the TableTwoData rows themselves
                    rows.delete()
                elif item_id == 'tableBody-3':
                    rows = TableThreeData.objects.filter(id__in=row_ids)
                elif item_id == 'tableBody-4':
                    rows = TableFourData.objects.filter(id__in=row_ids)
                elif item_id == 'tableBody-5':
                    rows = TableFiveData.objects.filter(id__in=row_ids)

                
                # Delete the rows
                rows.delete()

            return JsonResponse({'message': 'Data deleted successfully'}, status=200)

        except Exception as e:
            print(f"Error deleting rows: {e}")
            return JsonResponse({'error': 'Error deleting rows'}, status=500)
    
    else:
        return render(request, 'app/trace.html')



"""
1.CSRF (Cross-Site Request Forgery)
  csrf_exempt in Django disables CSRF protection for a specific view, allowing requests to bypass CSRF token validation.

2. JSON is a lightweight data interchange format 

3.Render:
    the process of loading a template, rendering it with context data, and returning an HttpResponse
"""