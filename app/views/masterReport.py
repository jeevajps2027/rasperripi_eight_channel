from django.shortcuts import render

from app.models import CustomerDetails, Master_settings, master_report, parameter_settings,MailSettings
from django.utils import timezone  
from datetime import datetime
from django.db.models import Q
import pandas as pd
from django.db.models import Q

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from django.http import JsonResponse


from django.http import HttpResponse
from django.template.loader import get_template
from django.conf import settings
from weasyprint import HTML,CSS
import pandas as pd
from io import BytesIO
import re

from pathlib import Path

def get_save_directory(subfolder):
    """
    Check if USB is mounted under /media, else return local Downloads path.
    subfolder: e.g. 'pdf_files/ParameterWise' or 'xlsx_files/ParameterWise'
    """
    usb_base_path = '/media'
    downloads_path = Path.home() / 'Downloads' / subfolder

    # --- Check USB mounts ---
    if os.path.exists(usb_base_path):
        for user_folder in os.listdir(usb_base_path):
            user_path = os.path.join(usb_base_path, user_folder)
            if os.path.isdir(user_path):
                for device_folder in os.listdir(user_path):
                    device_path = os.path.join(user_path, device_folder)
                    if os.path.ismount(device_path):
                        # USB is mounted → save inside it
                        return os.path.join(device_path, 'Gauge_Logic', subfolder), 'USB'

    # --- Default to Downloads ---
    return str(downloads_path), 'Downloads'

# Function to remove HTML tags
def strip_html_tags(text):
    # Check if text is a string, then remove HTML tags
    if isinstance(text, str):
        return re.sub(r'<.*?>', '', text)
    return text

# Function to replace <br> with \n for multi-line headers
def replace_br_with_newline(text):
    if isinstance(text, str):
        return text.replace('<br>', '\n')
    return text

def convert_columns_to_numeric(df):
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='ignore')
    return df

def masterReport(request):
    if request.method == 'GET':
        master_date_values = master_report.objects.all()
        part_model = master_report.objects.values_list('part_model', flat=True).distinct().get()
        print("part_model:", part_model)

        email_1 = CustomerDetails.objects.values_list('primary_email', flat=True).first() or 'No primary email'
        print('your primary mail id from server to front end now:', email_1)

        email_2 = CustomerDetails.objects.values_list('secondary_email', flat=True).first() or 'No secondary email'
        print('your secondary mail id from server to front end now:', email_2)

        fromDateStr = master_report.objects.values_list('formatted_from_date', flat=True).get()
        toDateStr = master_report.objects.values_list('formatted_to_date', flat=True).get()
        print("fromDate:", fromDateStr, "toDate:", toDateStr)

        parameter_name = master_report.objects.values_list('parameter_name', flat=True).get()
        print("parameter_name:", parameter_name)
        operator = master_report.objects.values_list('operator', flat=True).get()
        print("operator:", operator)
        machine = master_report.objects.values_list('machine', flat=True).get()
        print("machine:", machine)
        shift = master_report.objects.values_list('shift', flat=True).get()
        print("shift:", shift)
        job_no = master_report.objects.values_list('job_no', flat=True).get()
        print("job_no:", job_no)

        date_format_input = '%d-%m-%Y %I:%M:%S %p'
        from_datetime = datetime.strptime(fromDateStr, date_format_input)
        to_datetime = datetime.strptime(toDateStr, date_format_input)

        # Print the datetime objects to verify correct conversion
        print("from_datetime:", from_datetime, "to_datetime:", to_datetime)

       # Prepare the filter based on parameters
        filter_kwargs = {
            'date_time__range': (from_datetime, to_datetime), 
            'selected_value': part_model,
        }

        # Conditionally add filters based on values being "ALL"
        if parameter_name != "ALL":
            filter_kwargs['parameter_name'] = parameter_name

        if operator != "ALL":
            filter_kwargs['operator'] = operator

        if machine != "ALL":
            filter_kwargs['machine'] = machine

        if shift != "ALL":
            filter_kwargs['shift'] = shift

       

        # Filtered data based on the required filters
        filtered_data = Master_settings.objects.filter(**filter_kwargs).order_by('date_time')
        if not filtered_data:
            context = {
                'no_results': True
            }
            return render(request, 'app/reports/masterReport.html', context)


        # Initialize the data_dict with required headers
        data_dict = {
            'Date': [],
            'ProbeNo': [],
            'Shift': [],
            'Operator': [],
            'Machine': [],
        }

        hidden_parameters = parameter_settings.objects.filter(hide_checkbox=True, model_id=part_model).values_list('parameter_name', flat=True)
        # Fetch parameter data and exclude specific conditions
        parameter_data = parameter_settings.objects.filter(
            model_id=part_model
        ).exclude(parameter_name__in=hidden_parameters).exclude(
            Q(measurement_mode='TIR') | Q(attribute=True)
        ).values('parameter_name').order_by('id')

        # Create a list to hold the column headers
        column_headers = []

        # Generate column headers for LOW and HIGH values dynamically
        for param in parameter_data:
            column_headers.append(param['parameter_name'] + " LOW")
            column_headers.append(param['parameter_name'] + " HIGH")

        # Update the data_dict with the new column headers and empty lists
        data_dict.update({header: [] for header in column_headers})

        # Group data by common fields (date, operator, compono, shift, machine)
        grouped_data = {}

        for record in filtered_data:
            # Grouping key based on common fields
            group_key = (
                record.date_time.strftime('%d-%m-%Y %I:%M:%S %p'),
                record.probe_no,
                record.shift,
                record.operator,
                record.machine,
            )

            # Initialize the group if not already present
            if group_key not in grouped_data:
                grouped_data[group_key] = {header: "" for header in column_headers}

            # Update the corresponding LOW and HIGH values for the parameter_name
            if record.parameter_name in [param['parameter_name'] for param in parameter_data]:
                grouped_data[group_key][record.parameter_name + " LOW"] = record.a if record.a is not None else ""
                grouped_data[group_key][record.parameter_name + " HIGH"] = record.b if record.b is not None else ""

        # Flatten the grouped data into rows for the DataFrame
        for key, param_values in grouped_data.items():
            date, compono, shift, operator, machine = key

            # Append the grouped values to the data_dict
            data_dict['Date'].append(date)
            data_dict['ProbeNo'].append(compono)
            data_dict['Shift'].append(shift)
            data_dict['Operator'].append(operator)
            data_dict['Machine'].append(machine)

            # Add parameter values to the corresponding headers
            for header in column_headers:
                data_dict[header].append(param_values.get(header, ""))

        # Create a pandas DataFrame from the dictionary
        df = pd.DataFrame(data_dict)

        # Shift index by 1 to start from 1
        df.index = df.index + 1

        # Convert the DataFrame to an HTML table with custom styling
        table_html = df.to_html(
            index=True,
            escape=False,
            classes='table table-striped'
        )

        # Print or return the HTML table
        print(table_html)
        context = {
            'table_html': table_html,
            'master_report_values': master_date_values,
            'email_1': email_1,
            'email_2': email_2
        }

        request.session['data_dict'] = data_dict  # Save data_dict to the session for POST request

        return render(request,"app/reports/masterReport.html",context)

        
    elif request.method == 'POST':
        export_type = request.POST.get('export_type')
        recipient_email = request.POST.get('recipient_email')
        data_dict = request.session.get('data_dict')  # Retrieve data_dict from session
        if data_dict is None:
            return HttpResponse("No data available for export", status=400)

        df = pd.DataFrame(data_dict)
        df.index = df.index + 1


        if export_type == 'pdf' or export_type == 'send_mail':
            template = get_template('app/reports/masterReport.html')
            context = {
                'table_html': df.to_html(index=True, escape=False, classes='table table-striped table_data'),
                'master_vallues': master_report.objects.all(),
            }
            html_string = template.render(context)

            # CSS for scaling down the content to fit a single PDF page
            css = CSS(string='''
               @page {
                    size: A4 landscape; /* Landscape for more width */
                    margin: 1cm;
                }

                body {
                    margin: 0;
                    font-size: 20px; /* Big readable font */
                }
                
                .no-pdf {
                    display: none;
                }
            ''')


            pdf = HTML(string=html_string).write_pdf(stylesheets=[css])

            # Get the Downloads folder path
            target_folder, save_location = get_save_directory("pdf_files/MasterReport")

            # Ensure the target folder exists
            os.makedirs(target_folder, exist_ok=True)
            pdf_filename = f"masterReport_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.pdf"
            pdf_file_path = os.path.join(target_folder, pdf_filename)

            # Save the PDF file in the Downloads folder
            with open(pdf_file_path, 'wb') as pdf_file:
                pdf_file.write(pdf)

            # Return the PDF file for download
            if export_type == 'pdf':
                response = HttpResponse(pdf, content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'
                  # Pass success message to the context to show on the front end
                success_message = "PDF generated successfully!"
                context['success_message'] = success_message
                return render(request, 'app/reports/masterReport.html', context)

            elif export_type == 'send_mail':
                pdf_filename = f"masterReport_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.pdf"
                # Send the PDF as an email attachment
                send_mail_with_pdf(pdf, recipient_email, pdf_filename)
                success_message = "PDF generated and email sent successfully!"
                return render(request, 'app/reports/masterReport.html', {'success_message': success_message, **context})
        
        elif request.method == 'POST' and export_type == 'excel':
            template = get_template('app/reports/masterReport.html')
            context = {
                'table_html': df.to_html(index=True, escape=False, classes='table table-striped table_data'),
                'master_vallues': master_report.objects.all(),
            }
            # Remove HTML tags from the DataFrame before exporting
            df = df.applymap(strip_html_tags)

            # Replace <br> with newline in column headers to make them multi-line in Excel
            df.columns = [replace_br_with_newline(col) for col in df.columns]

            # ✅ Convert string values to numeric (for formulas to work)
            df = convert_columns_to_numeric(df)

            # Create a new DataFrame for master_vallues
            master_vallues = master_report.objects.all()
            master_data_values = []

            for data in master_vallues:
                master_data_values.append({
                    'PARTMODEL': data.part_model,
                    'PARAMETER NAME': data.parameter_name,
                    'OPERATOR': data.operator,
                    'FROM DATE': data.formatted_from_date,
                    'TO DATE': data.formatted_to_date,
                    'MACHINE': data.machine,
                    'VENDOR CODE': data.vendor_code,
                    'JOB NO': data.job_no,
                    'SHIFT': data.shift,
                    'CURRENT DATE': data.current_date_time,
                })

            parameterwise_df = pd.DataFrame(master_data_values)

            # Create an Excel writer object using BytesIO as a file-like object
            excel_buffer = BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                # Write parameterwise_df to the Excel sheet first
                parameterwise_df.to_excel(writer, sheet_name='masterReport', index=False, startrow=0)

                # Write the original DataFrame to the same sheet below the parameterwise data
                df.to_excel(writer, sheet_name='masterReport', index=True, startrow=len(parameterwise_df) + 2)

                # Get access to the workbook and worksheet objects
                workbook = writer.book
                worksheet = writer.sheets['masterReport']

                # Format for multi-line header
                header_format = workbook.add_format({
                    'text_wrap': True,  # Enable text wrap
                    'valign': 'top',    # Align to top
                    'align': 'center',  # Center align the text
                    'bold': True        # Make the headers bold
                })

                # Apply formatting to the headers of the parameterwise data
                for col_num, value in enumerate(parameterwise_df.columns.values):
                    worksheet.write(0, col_num, value, header_format)

                # Apply formatting to the headers of the main DataFrame (startrow=len(parameterwise_df)+2)
                for col_num, value in enumerate(df.columns.values):
                    worksheet.write(len(parameterwise_df) + 2, col_num + 1, value, header_format)

                number_format = workbook.add_format({'num_format': '0.000'})
                for col_num, col in enumerate(df.columns):
                    if pd.api.types.is_numeric_dtype(df[col]):
                        worksheet.set_column(col_num + 1, col_num + 1, 15, number_format)    

            # Get the Downloads folder path
           
            target_folder, save_location = get_save_directory("xlsx_files/MasterReport")

            # Ensure the target folder exists
            os.makedirs(target_folder, exist_ok=True)
            excel_filename = f"masterReport_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.xlsx"
            excel_file_path = os.path.join(target_folder, excel_filename)

            # Save the Excel file in the Downloads folder
            with open(excel_file_path, 'wb') as excel_file:
                excel_file.write(excel_buffer.getvalue())

            # Return the Excel file for download
            response = HttpResponse(excel_buffer.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = f'attachment; filename="{excel_filename}"'
            
            success_message = "Excel file generated successfully!"
            
            # Render success message in the frontend
            return render(request, 'app/reports/masterReport.html', {'success_message': success_message ,**context})

        return HttpResponse("Unsupported request method", status=405)



def send_mail_with_pdf(pdf_content, recipient_email, pdf_filename):

    try:
        mail_settings = MailSettings.objects.get(id=1)  # Assuming only one settings row
    except MailSettings.DoesNotExist:
        print("Mail settings not configured.")
        return


    sender_email = mail_settings.sender_email
    sender_password = mail_settings.sender_password
    smtp_server = mail_settings.smtp_server
    smtp_port = mail_settings.smtp_port
    subject = "Final Gate JobReport PDF"
    body = "Please find the attached PDF report."

    # Setup email parameters
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject

    # Attach the email body
    msg.attach(MIMEText(body, 'plain'))

    # Attach the PDF file
    attachment = MIMEBase('application', 'octet-stream')
    attachment.set_payload(pdf_content)
    encoders.encode_base64(attachment)
    attachment.add_header('Content-Disposition', f'attachment; filename="{pdf_filename}"')
    msg.attach(attachment)

    # Send the email using SMTP
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, msg.as_string())
        print("Email sent successfully.")
    except Exception as e:
        print(f"Error sending email: {e}")


       
    