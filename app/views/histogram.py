from django.shortcuts import render
import numpy as np
from app.models import MeasurementData, Histogram_Chart, CustomerDetails,MailSettings
from django.utils import timezone
from datetime import datetime
import matplotlib.pyplot as plt
import io
import base64
from weasyprint import HTML, CSS
from django.http import HttpResponse
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

def histogram(request):
    if request.method == 'POST':
        export_type = request.POST.get('export_type')
        recipient_email = request.POST.get('recipient_email')
        
        # Generate the same context as before
        context = generate_histogram_context(request)
        
        # Render the HTML to a string
        html_string = render(request, 'app/spc/histogram.html', context).content.decode('utf-8')

        # Define the CSS for landscape orientation
        css = CSS(string='''
            @page {
                size: A4 landscape;
                margin: 1cm;
            }
            body {
                transform: scale(0.9);
                transform-origin: top left;
                width: 1200px;
            }
            .no-pdf {
                display: none;
            }
        ''')

        # Convert HTML to PDF
        pdf_file = HTML(string=html_string).write_pdf(stylesheets=[css])
        pdf_memory = BytesIO(pdf_file)

        if export_type == 'pdf':
           
            target_folder, save_location = get_save_directory("pdf_files/Histogram")

            # Ensure the target folder exists
            os.makedirs(target_folder, exist_ok=True)

            pdf_filename = f"Histogram_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.pdf"
            pdf_path = os.path.join(target_folder, pdf_filename)

            # Save the PDF to the filesystem
            with open(pdf_path, 'wb') as pdf_output:
                pdf_output.write(pdf_file)

            # Return the PDF file as a download
            response = HttpResponse(pdf_file, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'
            success_message = "PDF generated successfully!"
            context['success_message'] = success_message
            return render(request, 'app/spc/histogram.html', context)

        elif export_type == 'send_mail':
            # Send the PDF via email
            pdf_filename = f"Histogram_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.pdf"
            try:
                send_mail_with_pdf(pdf_memory.getvalue(), recipient_email, pdf_filename)
                success_message = f"PDF sent successfully to {recipient_email}!"
            except Exception as e:
                success_message = f"Error sending email: {str(e)}"
            
            context['success_message'] = success_message
            return render(request, 'app/spc/histogram.html', context)

    
    elif request.method == 'GET':

        # Handling the case when no email exists
        email_1 = CustomerDetails.objects.values_list('primary_email', flat=True).first() or 'No primary email'
        print('your primary mail id from server to front end now:', email_1)

        email_2 = CustomerDetails.objects.values_list('secondary_email', flat=True).first() or 'No secondary email'
        print('your secondary mail id from server to front end now:', email_2)
        # Generate the context for rendering the histogram page
        context = generate_histogram_context(request)

        if context is None:
            context = {}

        context['email_1'] = email_1
        context['email_2'] = email_2
        return render(request, 'app/spc/histogram.html', context)

def generate_histogram_context(request):
    # Fetch the Histogram_Chart values and other fields
    Histogram_Chart_values = Histogram_Chart.objects.all()
    part_model = Histogram_Chart.objects.values_list('part_model', flat=True).distinct().get()

    fromDateStr = Histogram_Chart.objects.values_list('formatted_from_date', flat=True).get()
    toDateStr = Histogram_Chart.objects.values_list('formatted_to_date', flat=True).get()

    parameter_name = Histogram_Chart.objects.values_list('parameter_name', flat=True).get()
    operator = Histogram_Chart.objects.values_list('operator', flat=True).get()
    machine = Histogram_Chart.objects.values_list('machine', flat=True).get()
    shift = Histogram_Chart.objects.values_list('shift', flat=True).get()

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
    filtered_data = MeasurementData.objects.filter(**filter_kwargs).values_list(
        'readings', 'usl', 'lsl', 'ltl', 'utl').order_by('id')

    ltl_values = [data[3] for data in filtered_data]  # List of all LTL values
    utl_values = [data[4] for data in filtered_data]  # List of all UTL values

    ltl = list(set(ltl_values))
    utl = list(set(utl_values))

    filtered_readings = list(MeasurementData.objects.filter(**filter_kwargs).values_list('readings', flat=True).order_by('id'))

    if not filtered_readings:
        return {
            'no_results': True
        }

    readings = [float(reading) for reading in filtered_readings if reading is not None]

    ltl_min = min(ltl) if ltl else None
    utl_max = max(utl) if utl else None

    bins = np.linspace(min(readings), max(readings), 30)

    plt.figure(figsize=(7, 5))
    counts, edges, patches = plt.hist(readings, bins=bins, alpha=0.7)

    for count, edge_left, edge_right, patch in zip(counts, edges[:-1], edges[1:], patches):
        if ltl_min <= edge_left and edge_right <= utl_max:
            patch.set_facecolor('green')
        else:
            patch.set_facecolor('red')

    plt.title('Histogram of Readings with Tolerance Limits')
    plt.xlabel('Readings')
    plt.ylabel('Frequency')
    plt.grid(axis='y', alpha=0.75)

    for value in ltl:
        plt.axvline(x=value, color='red', linestyle='--', linewidth=2, label=f'LTL: {value}')

    for value in utl:
        plt.axvline(x=value, color='red', linestyle='--', linewidth=2, label=f'UTL: {value}')

    plt.legend()

    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()

    image_base64 = base64.b64encode(image_png).decode('utf-8')

    return {
        'histogram_chart': image_base64,
        'Histogram_Chart_values': Histogram_Chart_values,
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