import plotly.graph_objs as go
import plotly.io as pio
from plotly.offline import plot
from django.shortcuts import render
import numpy as np
from app.models import MeasurementData, X_Bar_Chart, CustomerDetails,MailSettings
from django.utils import timezone
from datetime import datetime
from django.db.models import Q
from weasyprint import HTML, CSS
from django.http import HttpResponse
import os
import io
import base64
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

def xBar(request):
    if request.method == 'POST':
        export_type = request.POST.get('export_type')
        recipient_email = request.POST.get('recipient_email')
        
        # Generate the same context as before
        context = generate_xBar_context(request, pdf=True)
        
        # Render the HTML to a string
        html_string = render(request, 'app/spc/xBar.html', context).content.decode('utf-8')
        
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
          
            target_folder, save_location = get_save_directory("pdf_files/Xbar")


            # Ensure the target folder exists
            os.makedirs(target_folder, exist_ok=True)
            pdf_filename = f"Xbar_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.pdf"
            pdf_path = os.path.join(target_folder, pdf_filename)
            
            # Save the PDF file to the filesystem
            with open(pdf_path, 'wb') as pdf_output:
                pdf_output.write(pdf_file)

            # Return the PDF file as a download
            response = HttpResponse(pdf_file, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'
            success_message = "PDF generated successfully!"
            context['success_message'] = success_message
            return render(request, 'app/spc/xBar.html', context)
        
        elif export_type == 'send_mail':
            # Send the PDF via email
            pdf_filename = f"xBar_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.pdf"
            try:
                send_mail_with_pdf(pdf_memory.getvalue(), recipient_email, pdf_filename)
                success_message = f"PDF sent successfully to {recipient_email}!"
            except Exception as e:
                success_message = f"Error sending email: {str(e)}"
            
            context['success_message'] = success_message
            return render(request, 'app/spc/xBar.html', context)


    elif request.method == 'GET':
        # Handling the case when no email exists
        email_1 = CustomerDetails.objects.values_list('primary_email', flat=True).first() or 'No primary email'
        print('your primary mail id from server to front end now:', email_1)

        email_2 = CustomerDetails.objects.values_list('secondary_email', flat=True).first() or 'No secondary email'
        print('your secondary mail id from server to front end now:', email_2)
        # Generate the context for rendering the histogram page
        context = generate_xBar_context(request, pdf=False)
        if context is None:
            context = {}
    
        context['email_1'] = email_1
        context['email_2'] = email_2
        
        return render(request, 'app/spc/xBar.html', context)

def generate_xBar_context(request, pdf=False):
    # Fetch the x_bar_values and other fields
    x_bar_values = X_Bar_Chart.objects.all()
    part_model = X_Bar_Chart.objects.values_list('part_model', flat=True).distinct().get()

    fromDateStr = X_Bar_Chart.objects.values_list('formatted_from_date', flat=True).get()
    toDateStr = X_Bar_Chart.objects.values_list('formatted_to_date', flat=True).get()

    parameter_name = X_Bar_Chart.objects.values_list('parameter_name', flat=True).get()
    operator = X_Bar_Chart.objects.values_list('operator', flat=True).get()
    machine = X_Bar_Chart.objects.values_list('machine', flat=True).get()
    shift = X_Bar_Chart.objects.values_list('shift', flat=True).get()

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
        'readings', 'usl', 'lsl', 'nominal', 'ltl', 'utl').order_by('id')
    
    if not filtered_data:
        context = {
            'no_results': True
        }
        return context

    filtered_readings = MeasurementData.objects.filter(**filter_kwargs).values_list('readings', flat=True).order_by('id')

    total_count = len(filtered_readings)
    readings = [float(r) for r in filtered_readings]  # Convert readings to floats

    usl = filtered_data[0][1] if filtered_data else None
    lsl = filtered_data[0][2] if filtered_data else None
    nominal = filtered_data[0][3] if filtered_data else None
    ltl = filtered_data[0][4] if filtered_data else None
    utl = filtered_data[0][5] if filtered_data else None

    if readings and usl and lsl and nominal and ltl and utl:
        x_bar = np.mean(readings)

        trace_readings = go.Scatter(
            x=list(range(len(readings))),
            y=readings,
            mode='lines+markers',
            name='Readings',
            marker=dict(color='blue')
        )
        trace_usl = go.Scatter(
            x=list(range(len(readings))),
            y=[usl] * len(readings),
            mode='lines',
            name=f'USL ({usl})',
            line=dict(color='red', dash='dash')
        )
        trace_lsl = go.Scatter(
            x=list(range(len(readings))),
            y=[lsl] * len(readings),
            mode='lines',
            name=f'LSL ({lsl})',
            line=dict(color='red', dash='dash')
        )
        trace_nominal = go.Scatter(
            x=list(range(len(readings))),
            y=[nominal] * len(readings),
            mode='lines',
            name=f'Nominal ({nominal})',
            line=dict(color='green', dash='solid')
        )
        trace_ltl = go.Scatter(
            x=list(range(len(readings))),
            y=[ltl] * len(readings),
            mode='lines',
            name=f'LTL ({ltl})',
            line=dict(color='orange', dash='dot')
        )
        trace_utl = go.Scatter(
            x=list(range(len(readings))),
            y=[utl] * len(readings),
            mode='lines',
            name=f'UTL ({utl})',
            line=dict(color='purple', dash='dot')
        )
        trace_xbar = go.Scatter(
            x=list(range(len(readings))),
            y=[x_bar] * len(readings),
            mode='lines',
            name=f'X-bar (Mean: {x_bar:.5f})',
            line=dict(color='purple', dash='solid')
        )

        data = [trace_readings, trace_usl, trace_lsl, trace_nominal, trace_ltl, trace_utl, trace_xbar]

        layout = go.Layout(
            title='X-bar Control Chart',
            xaxis_title='Sample Number',
            yaxis_title='Measurement',
            hovermode='closest',
            width=1100  # Set the chart width to 900px
        )

        fig = go.Figure(data=data, layout=layout)

        if pdf:
            # Save the chart as a PNG image for the PDF
            img_bytes = fig.to_image(format="png")
            img_base64 = base64.b64encode(img_bytes).decode('utf-8')
            chart_html = f'<img src="data:image/png;base64,{img_base64}" alt="X-bar Chart">'
        else:
            # Render the chart as an interactive HTML component for normal requests
            chart_html = plot(fig, output_type='div')

        return {
            'chart': chart_html,
            'x_bar_values': x_bar_values,
            'total_count': total_count,
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