from django.http import HttpResponse
from django.shortcuts import render
from app.models import MeasurementData, Pie_Chart, CustomerDetails,MailSettings
from django.utils import timezone
from datetime import datetime
import matplotlib.pyplot as plt
import io
import base64
from weasyprint import HTML, CSS
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
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

def pieChart(request):
    if request.method == 'POST':
        export_type = request.POST.get('export_type')
        recipient_email = request.POST.get('recipient_email')
        
        # Generate the same context as before
        context = generate_pieChart_context(request)
        
        # Render the HTML to a string
        html_string = render(request, 'app/spc/pieChart.html', context).content.decode('utf-8')
        
        # Define the CSS for landscape orientation
        css = CSS(string='''
            @page {
                size: A4 landscape; /* Set the page size to A4 landscape */
                margin: 1cm; /* Adjust margins as needed */
            }
            body {
                transform: scale(0.9); /* Adjust scale as needed */
                transform-origin: top left; /* Set origin for scaling */
                width: 1200px; /* Width of the content */
            }
            .no-pdf {
                display: none;
            }
        ''')
        
        # Convert HTML to PDF
        pdf_file = HTML(string=html_string).write_pdf(stylesheets=[css])
        pdf_memory = BytesIO(pdf_file)
        
        if export_type == 'pdf':
            # Define the path to save the PDF (e.g., Downloads folder)
       
            target_folder, save_location = get_save_directory("pdf_files/Piechart")

            # Ensure the target folder exists
            os.makedirs(target_folder, exist_ok=True)
            pdf_filename = f"PieChart_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.pdf"
            pdf_path = os.path.join(target_folder, pdf_filename)
            
            # Save the PDF file to the filesystem
            with open(pdf_path, 'wb') as pdf_output:
                pdf_output.write(pdf_file)

            # Return the PDF file as a download
            response = HttpResponse(pdf_file, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'
            success_message = "PDF generated successfully!"
            context['success_message'] = success_message
            return render(request, 'app/spc/pieChart.html', context)

        elif export_type == 'send_mail':
            # Send the PDF via email
            pdf_filename = f"Piechart_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.pdf"
            try:
                send_mail_with_pdf(pdf_memory.getvalue(), recipient_email, pdf_filename)
                success_message = f"PDF sent successfully to {recipient_email}!"
            except Exception as e:
                success_message = f"Error sending email: {str(e)}"
            
            context['success_message'] = success_message
            return render(request, 'app/spc/pieChart.html', context)


    
    elif request.method == 'GET':
        # Handling the case when no email exists
        email_1 = CustomerDetails.objects.values_list('primary_email', flat=True).first() or 'No primary email'
        print('your primary mail id from server to front end now:', email_1)

        email_2 = CustomerDetails.objects.values_list('secondary_email', flat=True).first() or 'No secondary email'
        print('your secondary mail id from server to front end now:', email_2)
        # Generate the context for rendering the histogram page
        context = generate_pieChart_context(request)

        if context is None:
            context = {}
            
        context['email_1'] = email_1
        context['email_2'] = email_2
        return render(request, 'app/spc/pieChart.html', context)

def generate_pieChart_context(request):
        # Fetch the x_bar_values and other fields
        pie_chart_values = Pie_Chart.objects.all()
        part_model = Pie_Chart.objects.values_list('part_model', flat=True).distinct().get()

        fromDateStr = Pie_Chart.objects.values_list('formatted_from_date', flat=True).get()
        toDateStr = Pie_Chart.objects.values_list('formatted_to_date', flat=True).get()

        parameter_name = Pie_Chart.objects.values_list('parameter_name', flat=True).get()
        operator = Pie_Chart.objects.values_list('operator', flat=True).get()
        machine = Pie_Chart.objects.values_list('machine', flat=True).get()
        shift = Pie_Chart.objects.values_list('shift', flat=True).get()

        date_format_input = '%d-%m-%Y %I:%M:%S %p'
        from_datetime = datetime.strptime(fromDateStr, date_format_input)
        to_datetime = datetime.strptime(toDateStr, date_format_input)

        # Set up filter conditions
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

        # Fetch filtered data
        filtered_readings = list(MeasurementData.objects.filter(**filter_kwargs).values_list('readings', flat=True).order_by('id'))

        if not filtered_readings:
        # Return an empty context with a no_results flag
            return {
                'no_results': True,
                'Pie_Chart': pie_chart_values,
            }

        filtered_status = list(MeasurementData.objects.filter(**filter_kwargs).values_list('status_cell', flat=True).order_by('id'))
        print("filtered_status",filtered_status)
        total_count = len(filtered_readings)
        print("Total readings count:", total_count)


        status_counts = {'ACCEPT': 0, 'REJECT': 0, 'REWORK': 0}

        # Ensure both lists have the same length
        if len(filtered_readings) == len(filtered_status):
            for status in filtered_status:
                if status == 'ACCEPT':
                    status_counts['ACCEPT'] += 1
                elif status == 'REWORK':
                    status_counts['REWORK'] += 1
                elif status == 'REJECT':
                    status_counts['REJECT'] += 1

        # Filter out statuses with zero counts for the pie chart
        labels = [label for label, count in status_counts.items() if count > 0]
        sizes = [count for count in status_counts.values() if count > 0]

        # Define colors based on available statuses
        color_map = {
            'ACCEPT': '#00ff00',  # Green
            'REWORK': 'yellow',   # Yellow
            'REJECT': 'red'       # Red
        }
        colors = [color_map[label] for label in labels]

        plt.figure(figsize=(6, 6))
        plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
        plt.axis('equal')  # Equal aspect ratio ensures that the pie chart is circular.

        # Save the chart to a BytesIO stream
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()

        # Encode the image to base64
        image_base64 = base64.b64encode(image_png).decode('utf-8')

        # Pass the base64 image data to the template
        
        return {
            'pie_chart': image_base64,
            'status_counts': status_counts,
            'pie_chart_values':pie_chart_values,
            'total_count':total_count,
            'accept_count': status_counts['ACCEPT'],
            'reject_count': status_counts['REJECT'],
            'rework_count': status_counts['REWORK'],

        }

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