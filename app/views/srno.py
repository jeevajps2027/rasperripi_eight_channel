from datetime import datetime
import pandas as pd
from django.shortcuts import render
from django.utils import timezone
from app.models import MeasurementData, parameter_settings, consolidate_with_srno,CustomerDetails,MailSettings
from django.http import HttpResponse
from django.template.loader import get_template
from weasyprint import HTML, CSS
from io import BytesIO
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from django.http import JsonResponse
import os
import re
from io import BytesIO

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


def srno(request):
    if request.method == 'GET':
        consolidate_values = consolidate_with_srno.objects.all()
        part_model = consolidate_with_srno.objects.values_list('part_model', flat=True).distinct().get()
        print("part_model:", part_model)

        email_1 = CustomerDetails.objects.values_list('primary_email', flat=True).first() or 'No primary email'
        email_2 = CustomerDetails.objects.values_list('secondary_email', flat=True).first() or 'No secondary email'

        fromDateStr = consolidate_with_srno.objects.values_list('formatted_from_date', flat=True).get()
        toDateStr = consolidate_with_srno.objects.values_list('formatted_to_date', flat=True).get()

        parameter_name = consolidate_with_srno.objects.values_list('parameter_name', flat=True).get()
        operator = consolidate_with_srno.objects.values_list('operator', flat=True).get()
        machine = consolidate_with_srno.objects.values_list('machine', flat=True).get()
        shift = consolidate_with_srno.objects.values_list('shift', flat=True).get()
        job_no = consolidate_with_srno.objects.values_list('job_no', flat=True).get()

        date_format_input = '%d-%m-%Y %I:%M:%S %p'
        from_datetime = datetime.strptime(fromDateStr, date_format_input)
        to_datetime = datetime.strptime(toDateStr, date_format_input)

        print("from_datetime",from_datetime)
        print("to_datetime jjjjjjjjjjjjjjjjjjjjjjjjj",to_datetime)

        # Get parameter names that should not be filtered out
        excluded_parameters = parameter_settings.objects.filter(hide_checkbox=True).values_list('parameter_name', flat=True)

        filter_kwargs = {
            'date__range': (from_datetime, to_datetime),
            'part_model': part_model,
        }

        if parameter_name != "ALL" and parameter_name not in excluded_parameters:
            filter_kwargs['parameter_name'] = parameter_name

        if operator != "ALL":
            filter_kwargs['operator'] = operator

        if machine != "ALL":
            filter_kwargs['machine'] = machine

        if shift != "ALL":
            filter_kwargs['shift'] = shift

        if job_no != "ALL":
            filter_kwargs['comp_sr_no'] = job_no

        filtered_data = MeasurementData.objects.filter(**filter_kwargs).values()
       

        hidden_parameters = parameter_settings.objects.filter(hide_checkbox=True, model_id=part_model).values_list('parameter_name', flat=True)

        # Ensure we include all parameter names that should not be filtered
        parameter_data = parameter_settings.objects.filter(
            model_id=part_model
        ).exclude(parameter_name__in=hidden_parameters).values('parameter_name', 'utl', 'ltl').order_by('id')

        data_dict = {
            'Date': [],
            'Job Number': [],
            'Shift': [],
            'Operator': [],
        }

        for param in parameter_data:
            param_name = param['parameter_name']
            utl = param['utl']
            ltl = param['ltl']
            key = f"{param_name} <br>{utl} <br>{ltl}"
            data_dict[key] = []

        data_dict['Status'] = []
        status_counts = {'ACCEPT': 0, 'REJECT': 0, 'REWORK': 0}

        distinct_comp_sr_nos = filtered_data.exclude(comp_sr_no__isnull=True).exclude(comp_sr_no__exact='').values_list('comp_sr_no', flat=True).distinct().order_by('date')

        for comp_sr_no in distinct_comp_sr_nos:
            filter_params = filter_kwargs.copy()
            filter_params['comp_sr_no'] = comp_sr_no

            part_status = MeasurementData.objects.filter(**filter_params).values_list('part_status', flat=True).distinct().first()

            comp_sr_no_data = MeasurementData.objects.filter(**filter_params).values(
                'parameter_name', 'readings', 'status_cell', 'operator', 'shift', 'machine', 'date'
            )

            combined_row = {
                'Date': '',
                'Job Number': comp_sr_no,
                'Shift': '',
                'Operator': '',
                'Status': ''
            }

            for data in comp_sr_no_data:
                parameter_name = data.get('parameter_name')

                try:
                    parameter_setting = parameter_settings.objects.get(parameter_name=parameter_name, model_id=part_model)
                    utl = parameter_setting.utl
                    ltl = parameter_setting.ltl
                    key = f"{parameter_name} <br>{utl} <br>{ltl}"
                    formatted_date = data['date'].strftime('%d-%m-%Y %I:%M:%S %p')
                except parameter_settings.DoesNotExist:
                    print(f"No parameter_settings found for {parameter_name} and model_id={part_model}")
                    continue

                # Check if the parameter is excluded from filtering
                if parameter_name in excluded_parameters:
                    continue  # Skip filtering for this parameter

                reading = data["readings"]
                try:
                    formatted_reading = "{:.3f}".format(float(reading))
                except (TypeError, ValueError):
                    formatted_reading = "N/A"

                status_cell = data.get("status_cell")
                if status_cell == 'ACCEPT':
                    readings_html = f'<span style="background-color: #00ff00; padding: 2px;">{formatted_reading}</span>'
                elif status_cell == 'REWORK':
                    readings_html = f'<span style="background-color: yellow; padding: 2px;">{formatted_reading}</span>'
                elif status_cell == 'REJECT':
                    readings_html = f'<span style="background-color: red; padding: 2px;">{formatted_reading}</span>'
                else:
                    readings_html = f'<span style="padding: 2px;">{formatted_reading}</span>'

                combined_row[key] = readings_html
                combined_row['Date'] = formatted_date
                combined_row['Operator'] = data['operator']
                combined_row['Shift'] = data['shift']

            if part_status == 'ACCEPT':
                status_html = '<span style="background-color: #00ff00; padding: 2px;">ACCEPT</span>'
                status_counts['ACCEPT'] += 1
            elif part_status == 'REWORK':
                status_html = '<span style="background-color: yellow; padding: 2px;">REWORK</span>'
                status_counts['REWORK'] += 1
            elif part_status == 'REJECT':
                status_html = '<span style="background-color: red; padding: 2px;">REJECT</span>'
                status_counts['REJECT'] += 1
            else:
                status_html = '<span style="padding: 2px;">N/A</span>'

            combined_row['Status'] = status_html

            for key in data_dict:
                data_dict[key].append(combined_row.get(key, ''))

        print(f"Status counts: ACCEPT={status_counts['ACCEPT']}, REJECT={status_counts['REJECT']}, REWORK={status_counts['REWORK']}")

        df = pd.DataFrame(data_dict)
        df.index = df.index + 1

        table_html = df.to_html(index=True, escape=False, classes='table table-striped')
       

        context = {
            'table_html': table_html,
            'consolidate_values': consolidate_values,
            'total_count': len(distinct_comp_sr_nos),
            'accept_count': status_counts['ACCEPT'],
            'reject_count': status_counts['REJECT'],
            'rework_count': status_counts['REWORK'],
            'email_1': email_1,
            'email_2': email_2,
        }

        request.session['data_dict'] = data_dict

        return render(request, 'app/reports/consolidateSrNo.html', context)

    elif request.method == 'POST':
        export_type = request.POST.get('export_type')
        recipient_email = request.POST.get('recipient_email')
        data_dict = request.session.get('data_dict')  # Retrieve data_dict from session
        if data_dict is None:
            return HttpResponse("No data available for export", status=400)

        df = pd.DataFrame(data_dict)
        df.index = df.index + 1

       

        if export_type == 'pdf' or export_type == 'send_mail':

            
            template = get_template('app/reports/consolidateSrNo.html')
            context = {
                'table_html': df.to_html(index=True, escape=False, classes='table table-striped table_data'),
                'consolidate_values': consolidate_with_srno.objects.all(),
                'total_count': df.shape[0],  # Use DataFrame shape for total count
                'accept_count': df[df['Status'].str.contains('ACCEPT')].shape[0],
                'reject_count': df[df['Status'].str.contains('REJECT')].shape[0],
                'rework_count': df[df['Status'].str.contains('REWORK')].shape[0],

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
            # Get the Downloads folder path
           
            target_folder, save_location = get_save_directory("pdf_files/WithSrNo")

            # Ensure the target folder exists
            os.makedirs(target_folder, exist_ok=True)
            pdf_filename = f"consolidateSrNo_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.pdf"
            pdf_file_path = os.path.join(target_folder, pdf_filename)

            # Save the PDF file in the Downloads folder
            with open(pdf_file_path, 'wb') as pdf_file:
                pdf_file.write(pdf)


            if export_type == 'pdf':
                response = HttpResponse(pdf, content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'
                  # Pass success message to the context to show on the front end
                success_message = "PDF generated successfully!"
                context['success_message'] = success_message
                return render(request, 'app/reports/consolidateSrNo.html', context)

            elif export_type == 'send_mail':
                pdf_filename = f"consolidateSrNo_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.pdf"
                # Send the PDF as an email attachment
                send_mail_with_pdf(pdf, recipient_email, pdf_filename)
                success_message = "PDF generated and email sent successfully!"
                return render(request, 'app/reports/consolidateSrNo.html', {'success_message': success_message, **context})
        elif request.method == 'POST' and export_type == 'excel':

            template = get_template('app/reports/consolidateSrNo.html')
            context = {
                'table_html': df.to_html(index=True, escape=False, classes='table table-striped table_data'),
                'consolidate_values': consolidate_with_srno.objects.all(),
                'total_count': df.shape[0],  # Use DataFrame shape for total count
                'accept_count': df[df['Status'].str.contains('ACCEPT')].shape[0],
                'reject_count': df[df['Status'].str.contains('REJECT')].shape[0],
                'rework_count': df[df['Status'].str.contains('REWORK')].shape[0],
            }
            df = df.applymap(strip_html_tags)

            # Replace <br> with newlines in headers
            df.columns = [replace_br_with_newline(col) for col in df.columns]

            # ✅ Convert string values to numeric (for formulas to work)
            df = convert_columns_to_numeric(df)

            # Create a new DataFrame for parameterwise_values
            consolidateSrNowise_values = consolidate_with_srno.objects.all()
            consolidateSrNowise_data = []

            for data in consolidateSrNowise_values:
                consolidateSrNowise_data.append({
                    'PARTMODEL': data.part_model,
                    'PARAMETERNAME': data.parameter_name,
                    'OPERATOR': data.operator,
                    'MACHINE':data.machine,
                    'VENDOR CODE': data.vendor_code,
                    'JOB NO': data.job_no,
                    'SHIFT': data.shift,
                    'FROM DATE': data.formatted_from_date,
                    'TO DATE': data.formatted_to_date,
                    'CURRENT DATE': data.current_date_time,
                    'TOTAL_COUNT': df.shape[0],  # Use DataFrame shape for total count
                    'ACCEPT_COUNT': df[df['Status'].str.contains('ACCEPT')].shape[0],
                    'REJECT_COUNT': df[df['Status'].str.contains('REJECT')].shape[0],
                    'REWORK_COUNT': df[df['Status'].str.contains('REWORK')].shape[0],
                })

            consolidateSrNowise_df = pd.DataFrame(consolidateSrNowise_data)

            # Create an Excel writer object using BytesIO as a file-like object
            excel_buffer = BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                # Write parameterwise_df to the Excel sheet first
                consolidateSrNowise_df.to_excel(writer, sheet_name='consolidateSrNo', index=False, startrow=0)

                # Write the original DataFrame to the same sheet below the parameterwise data
                df.to_excel(writer, sheet_name='consolidateSrNo', index=True, startrow=len(consolidateSrNowise_df) + 2)

                # Get access to the workbook and worksheet objects
                workbook = writer.book
                worksheet = writer.sheets['consolidateSrNo']

                # Format for multi-line header
                header_format = workbook.add_format({
                    'text_wrap': True,  # Enable text wrap
                    'valign': 'top',    # Align to top
                    'align': 'center',  # Center align the text
                    'bold': True        # Make the headers bold
                })

                for col_num, value in enumerate(consolidateSrNowise_df.columns.values):
                    worksheet.write(0, col_num, value, header_format)

                for col_num, value in enumerate(df.columns.values):
                    worksheet.write(len(consolidateSrNowise_df) + 2, col_num + 1, value, header_format)

                # ✅ Format numeric columns so Excel treats them correctly
                number_format = workbook.add_format({'num_format': '0.000'})
                for col_num, col in enumerate(df.columns):
                    if pd.api.types.is_numeric_dtype(df[col]):
                        worksheet.set_column(col_num + 1, col_num + 1, 15, number_format)

            # Get the Downloads folder path
           
            target_folder, save_location = get_save_directory("xlsx_files/WithSrNo")

            # Ensure the target folder exists
            os.makedirs(target_folder, exist_ok=True)

            excel_filename = f"consolidateSrNo_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.xlsx"
            excel_file_path = os.path.join(target_folder, excel_filename)

            # Save the Excel file in the Downloads folder
            with open(excel_file_path, 'wb') as excel_file:
                excel_file.write(excel_buffer.getvalue())

            # Return the Excel file for download
            response = HttpResponse(excel_buffer.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = f'attachment; filename="{excel_filename}"'
            
            success_message = "Excel file generated successfully!"
            
            # Render success message in the frontend
            return render(request, 'app/reports/consolidateSrNo.html', {'success_message': success_message ,**context})

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