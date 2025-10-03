from collections import defaultdict
from datetime import datetime
import io
from django.shortcuts import render
from django.utils import timezone
from django.db.models import Q
import pandas as pd
from django.template.loader import get_template
from django.http import HttpResponse
from weasyprint import CSS, HTML
from app.models import MeasurementData,CustomerDetails, consolidate_without_srno, parameter_settings,MailSettings

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


def withoutsrno(request):
    if request.method == 'GET':
        consolidate_without_values = consolidate_without_srno.objects.all()
        part_model = consolidate_without_srno.objects.values_list('part_model', flat=True).distinct().get()

        # Handling the case when no email exists
        email_1 = CustomerDetails.objects.values_list('primary_email', flat=True).first() or 'No primary email'
        print('your primary mail id from server to front end now:', email_1)

        email_2 = CustomerDetails.objects.values_list('secondary_email', flat=True).first() or 'No secondary email'
        print('your secondary mail id from server to front end now:', email_2)

        fromDateStr = consolidate_without_srno.objects.values_list('formatted_from_date', flat=True).get()
        toDateStr = consolidate_without_srno.objects.values_list('formatted_to_date', flat=True).get()

        parameter_name = consolidate_without_srno.objects.values_list('parameter_name', flat=True).get()
        operator = consolidate_without_srno.objects.values_list('operator', flat=True).get()
        machine = consolidate_without_srno.objects.values_list('machine', flat=True).get()
        shift = consolidate_without_srno.objects.values_list('shift', flat=True).get()

        date_format_input = '%d-%m-%Y %I:%M:%S %p'
        from_datetime = datetime.strptime(fromDateStr, date_format_input)
        to_datetime = datetime.strptime(toDateStr, date_format_input)

        print("from_datetime",from_datetime)
        print("to_datetime jjjjjjjjjjjjjjjjjjjjjjjjj",to_datetime)
        filter_kwargs = {
            'date__range': (from_datetime, to_datetime),
            'part_model': part_model,
        }

        if parameter_name != "ALL":
            filter_kwargs['parameter_name'] = parameter_name

        if operator != "ALL":
            filter_kwargs['operator'] = operator

        if machine != "ALL":
            filter_kwargs['machine'] = machine

        if shift != "ALL":
            filter_kwargs['shift'] = shift

        filtered_data = MeasurementData.objects.filter(**filter_kwargs).values()
        distinct_comp_sr_nos = filtered_data.filter(Q(comp_sr_no__isnull=True) | Q(comp_sr_no__exact='')).order_by('date')
        if not distinct_comp_sr_nos:
            context = {
                'no_results': True
            }
            return render(request, 'app/reports/consolidateWithoutSrNo.html', context)

        grouped_by_date = defaultdict(list)
        for entry in distinct_comp_sr_nos:
            grouped_by_date[entry['date']].append(entry)

        distinct_dates = grouped_by_date.keys()
        total_count = len(distinct_dates)

        data_dict = {
            'Date': [],
            'Operator': [],
            'Shift': []
        }
        hidden_parameters = parameter_settings.objects.filter(hide_checkbox=True, model_id=part_model).values_list('parameter_name', flat=True)
        print('your DATA IS THIS FOR HIODDEN PARAMETERS:::',hidden_parameters)

        # Ensure we include all parameter names that should not be filtered
        parameter_data = parameter_settings.objects.filter(
            model_id=part_model
        ).exclude(parameter_name__in=hidden_parameters).values('parameter_name', 'utl', 'ltl').order_by('id')

        for param in parameter_data:
            param_name = param['parameter_name']
            utl = param['utl']
            ltl = param['ltl']
            key = f"{param_name} <br>{utl} <br>{ltl}"
            data_dict[key] = []

        data_dict['Status'] = []



        accept_count = 0
        rework_count = 0
        reject_count = 0

        for date, records in grouped_by_date.items():
            formatted_date = date.strftime('%d-%m-%Y %I:%M:%S %p')
            operator = records[0]['operator']
            shift = records[0]['shift']
            part_status = records[0]['part_status']

            data_dict['Date'].append(formatted_date)
            data_dict['Operator'].append(operator)
            data_dict['Shift'].append(shift)

            temp_dict = {key: '' for key in data_dict.keys() if key not in ['Date', 'Operator', 'Shift', 'Status']}

            for record in records:
                param_name = record.get('parameter_name')

                # Skip hidden parameters
                if param_name in hidden_parameters:
                    continue

                try:
                    parameter_setting = parameter_settings.objects.get(parameter_name=param_name, model_id=part_model)
                    utl = parameter_setting.utl
                    ltl = parameter_setting.ltl
                    key = f"{param_name} <br>{utl} <br>{ltl}"
                    # Process further as needed
                except parameter_settings.DoesNotExist:
                    print(f"No parameter_settings found for parameter_name={param_name} and model_id={part_model}")
                    continue

                if record['readings'] is None or record['readings'] == '':
                    if record['status_cell'] == 'ACCEPT':
                        readings_html = f'<span style="background-color: #00ff00; padding: 2px;">ACCEPT</span>'
                    elif record['status_cell'] == 'REWORK':
                        readings_html = f'<span style="background-color: yellow; padding: 2px;">REWORK</span>'
                    elif record['status_cell'] == 'REJECT':
                        readings_html = f'<span style="background-color: red; padding: 2px;">REJECT</span>'
                    else:
                        readings_html = '<span style="padding: 2px;">N/A</span>'
                else:
                    # If readings exist, use the actual readings
                    try:
                        formatted_reading = "{:.3f}".format(float(record["readings"]))
                    except (ValueError, TypeError):
                        formatted_reading = record["readings"]  # fallback to original if conversion fails

                    if record['status_cell'] == 'ACCEPT':
                        readings_html = f'<span style="background-color: #00ff00; padding: 2px;">{formatted_reading}</span>'
                    elif record['status_cell'] == 'REWORK':
                        readings_html = f'<span style="background-color: yellow; padding: 2px;">{formatted_reading}</span>'
                    elif record['status_cell'] == 'REJECT':
                        readings_html = f'<span style="background-color: red; padding: 2px;">{formatted_reading}</span>'
                    else:
                        readings_html = f'<span style="padding: 2px;">{formatted_reading}</span>'
                
                temp_dict[key] = readings_html

            for key in temp_dict:
                data_dict[key].append(temp_dict[key])

            if part_status == 'ACCEPT':
                status_html = f'<span style="background-color: #00ff00; padding: 2px;">{part_status}</span>'
                accept_count += 1
            elif part_status == 'REWORK':
                status_html = f'<span style="background-color: yellow; padding: 2px;">{part_status}</span>'
                rework_count += 1
            elif part_status == 'REJECT':
                status_html = f'<span style="background-color: red; padding: 2px;">{part_status}</span>'
                reject_count += 1

            data_dict['Status'].append(status_html)

       
        df = pd.DataFrame(data_dict)
        df.index = df.index + 1  # Shift index by 1 to start from 1

        table_html = df.to_html(index=True, escape=False, classes='table table-striped')

        context = {
            'table_html': table_html,
            'consolidate_without_values': consolidate_without_values,
            'accept_count': accept_count,
            'rework_count': rework_count,
            'reject_count': reject_count,
            'total_count': total_count,
            'email_1': email_1,
            'email_2': email_2
        }  
        request.session['data_dict'] = data_dict  
        return render(request, 'app/reports/consolidateWithoutSrNo.html', context)

    elif request.method == 'POST':
        export_type = request.POST.get('export_type')
        recipient_email = request.POST.get('recipient_email')
        print('your recipient mail from front end:',recipient_email)
        data_dict = request.session.get('data_dict')  # Retrieve data_dict from session
        if data_dict is None:
            return HttpResponse("No data available for export", status=400)

        df = pd.DataFrame(data_dict)
        df.index = df.index + 1

       

        if export_type == 'pdf' or export_type == 'send_mail':
            template = get_template('app/reports/consolidateWithoutSrNo.html')
            context = {
                'table_html': df.to_html(index=True, escape=False, classes='table table-striped table_data'),
                'consolidate_without_values': consolidate_without_srno.objects.all(),
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

            # target_folder = r"C:\Program Files\Gauge_Logic\pdf_files\WithoutSrNo"
            target_folder, save_location = get_save_directory("pdf_files/WithoutSrNo")

            # Ensure the target folder exists
            os.makedirs(target_folder, exist_ok=True)
            pdf_filename = f"consolidateWithoutSrNo_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.pdf"
            pdf_file_path = os.path.join(target_folder, pdf_filename)

            # Save the PDF file in the Downloads folder
            with open(pdf_file_path, 'wb') as pdf_file:
                pdf_file.write(pdf)
            print(f"PDF saved in {save_location}: {pdf_file_path}")


            if export_type == 'pdf':
                response = HttpResponse(pdf, content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'
                  # Pass success message to the context to show on the front end
                success_message = "PDF generated successfully!"
                context['success_message'] = success_message
                return render(request, 'app/reports/consolidateWithoutSrNo.html', context)

            elif export_type == 'send_mail':
                pdf_filename = f"consolidateWithoutSrNo_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.pdf"
                # Send the PDF as an email attachment
                send_mail_with_pdf(pdf, recipient_email, pdf_filename)
                success_message = "PDF generated and email sent successfully!"
                return render(request, 'app/reports/consolidateWithoutSrNo.html', {'success_message': success_message, **context})
        elif request.method == 'POST' and export_type == 'excel':

            template = get_template('app/reports/consolidateWithoutSrNo.html')
            context = {
                'table_html': df.to_html(index=True, escape=False, classes='table table-striped table_data'),
                'consolidate_values': consolidate_without_srno.objects.all(),
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
            consolidateWithoutSrNowise_values = consolidate_without_srno.objects.all()
            consolidateWithoutSrNowise_data = []

            for data in consolidateWithoutSrNowise_values:
                consolidateWithoutSrNowise_data.append({
                    'PARTMODEL': data.part_model,
                    'PARAMETERNAME': data.parameter_name,
                    'OPERATOR': data.operator,
                    'MACHINE':data.machine,
                    'VENDOR CODE': data.vendor_code,
                    'SHIFT': data.shift,
                    'FROM DATE': data.formatted_from_date,
                    'TO DATE': data.formatted_to_date,
                    'CURRENT DATE': data.current_date_time,
                    'TOTAL_COUNT': df.shape[0],  # Use DataFrame shape for total count
                    'ACCEPT_COUNT': df[df['Status'].str.contains('ACCEPT')].shape[0],
                    'REJECT_COUNT': df[df['Status'].str.contains('REJECT')].shape[0],
                    'REWORK_COUNT': df[df['Status'].str.contains('REWORK')].shape[0],
                })

            consolidateWithoutSrNowise_df = pd.DataFrame(consolidateWithoutSrNowise_data)

            # Create an Excel writer object using BytesIO as a file-like object
            excel_buffer = BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                # Write parameterwise_df to the Excel sheet first
                consolidateWithoutSrNowise_df.to_excel(writer, sheet_name='consolidateWithoutSrNo', index=False, startrow=0)

                # Write the original DataFrame to the same sheet below the parameterwise data
                df.to_excel(writer, sheet_name='consolidateWithoutSrNo', index=True, startrow=len(consolidateWithoutSrNowise_df) + 2)

                # Get access to the workbook and worksheet objects
                workbook = writer.book
                worksheet = writer.sheets['consolidateWithoutSrNo']

                # Format for multi-line header
                header_format = workbook.add_format({
                    'text_wrap': True,  # Enable text wrap
                    'valign': 'top',    # Align to top
                    'align': 'center',  # Center align the text
                    'bold': True        # Make the headers bold
                })

                # Apply formatting to the headers of the parameterwise data
                for col_num, value in enumerate(consolidateWithoutSrNowise_df.columns.values):
                    worksheet.write(0, col_num, value, header_format)

                # Apply formatting to the headers of the main DataFrame (startrow=len(parameterwise_df)+2)
                for col_num, value in enumerate(df.columns.values):
                    worksheet.write(len(consolidateWithoutSrNowise_df) + 2, col_num + 1, value, header_format)


                # ✅ Format numeric columns so Excel treats them correctly
                number_format = workbook.add_format({'num_format': '0.000'})
                for col_num, col in enumerate(df.columns):
                    if pd.api.types.is_numeric_dtype(df[col]):
                        worksheet.set_column(col_num + 1, col_num + 1, 15, number_format)    

            
            target_folder, save_location = get_save_directory("xlsx_files/WithoutSrNo")


            # Ensure the target folder exists
            os.makedirs(target_folder, exist_ok=True)
            excel_filename = f"consolidateWithoutSrNo_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.xlsx"
            excel_file_path = os.path.join(target_folder, excel_filename)

            # Save the Excel file in the Downloads folder
            with open(excel_file_path, 'wb') as excel_file:
                excel_file.write(excel_buffer.getvalue())

            # Return the Excel file for download
            response = HttpResponse(excel_buffer.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = f'attachment; filename="{excel_filename}"'
            
            success_message = "Excel file generated successfully!"
            
            # Render success message in the frontend
            return render(request, 'app/reports/consolidateWithoutSrNo.html', {'success_message': success_message ,**context})

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