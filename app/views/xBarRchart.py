import base64
import plotly.io as pio
import plotly.graph_objs as go
import plotly.offline as pyo
from django.shortcuts import render
import numpy as np
import pandas as pd
from app.models import MeasurementData, X_Bar_R_Chart,CustomerDetails,MailSettings
from django.utils import timezone
from datetime import datetime
from django.db.models import Q
from weasyprint import HTML, CSS
from django.http import HttpResponse
import os
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

def calculate_control_limits(x_bars, ranges, sample_size):
    # Define constants for different sample sizes
    control_chart_constants = {
        2: {"A2": 1.880, "D3": 0, "D4": 3.267},
        3: {"A2": 1.023, "D3": 0, "D4": 2.574},
        4: {"A2": 0.729, "D3": 0, "D4": 2.282},
        5: {"A2": 0.577, "D3": 0, "D4": 2.114},
    }
    
    # Fetch the constants for the given sample size
    if sample_size not in control_chart_constants:
        raise ValueError(f"Sample size {sample_size} is not supported.")
    
    A2 = control_chart_constants[sample_size]["A2"]
    D3 = control_chart_constants[sample_size]["D3"]
    D4 = control_chart_constants[sample_size]["D4"]
    
    # Mean of X-bars and Ranges
    x_bar = np.mean(x_bars)
    r_bar = np.mean(ranges)

    # Control Limits for X-bar and Range
    UCLx = x_bar + A2 * r_bar
    LCLx = x_bar - A2 * r_bar
    UCLr = D4 * r_bar
    LCLr = D3 * r_bar

    return x_bar, r_bar, UCLx, LCLx, UCLr, LCLr

def calculate_cp_cpk(x_bars,ranges, usl, lsl):
    x_bar = np.mean(x_bars)
    r_bar = np.mean(ranges)
    d2=2.325
    # sigma = np.std(x_bars, ddof=1)  # Standard deviation of the sample
    sigma = r_bar/d2  # Standard deviation of the sample
    print("sigma",sigma)
    
    cp = (usl - lsl) / (6 * sigma)
    print("the calculation of cp",cp)
    cpu = (usl - x_bar) / (3 * sigma)
    print ("cpu",cpu)
    cpl = (x_bar - lsl) / (3 * sigma)
    print("cpl",cpl)
    cpk = min((usl - x_bar) / (3 * sigma), (x_bar - lsl) / (3 * sigma))
    
    return cp, cpk


def xBarRchart(request): 
    if request.method == 'POST':
        export_type = request.POST.get('export_type')
        recipient_email = request.POST.get('recipient_email')
        
        # Generate the same context as before
        context = generate_xBarRchart_context(request, pdf=True)
        
        # Render the HTML to a string
        html_string = render(request, 'app/spc/xBarRchart.html', context).content.decode('utf-8')
        
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
            
            target_folder, save_location = get_save_directory("pdf_files/XbarRchart")

            # Ensure the target folder exists
            os.makedirs(target_folder, exist_ok=True)
            pdf_filename = f"XbarRchart_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.pdf"
            pdf_path = os.path.join(target_folder, pdf_filename)
            
            # Save the PDF file to the filesystem
            with open(pdf_path, 'wb') as pdf_output:
                pdf_output.write(pdf_file)

            # Return the PDF file as a download
            response = HttpResponse(pdf_file, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'
            success_message = "PDF generated successfully!"
            context['success_message'] = success_message
            return render(request, 'app/spc/xBarRchart.html', context)
        
        elif export_type == 'send_mail':
            # Send the PDF via email
            pdf_filename = f"xBarRchart_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.pdf"
            try:
                send_mail_with_pdf(pdf_memory.getvalue(), recipient_email, pdf_filename)
                success_message = f"PDF sent successfully to {recipient_email}!"
            except Exception as e:
                success_message = f"Error sending email: {str(e)}"
            
            context['success_message'] = success_message
            return render(request, 'app/spc/xBarRchart.html', context)


    elif request.method == 'GET':
        # Generate the context for rendering the histogram page
        email_1 = CustomerDetails.objects.values_list('primary_email', flat=True).first() or 'No primary email'
        print('your primary mail id from server to front end now:', email_1)

        email_2 = CustomerDetails.objects.values_list('secondary_email', flat=True).first() or 'No secondary email'
        print('your secondary mail id from server to front end now:', email_2)

        context = generate_xBarRchart_context(request, pdf=False)
        if context is None:
            context = {}
    
        context['email_1'] = email_1
        context['email_2'] = email_2

        return render(request, 'app/spc/xBarRchart.html', context)

def generate_xBarRchart_context(request, pdf=False):
        # Fetch the x_bar_values and other fields
        x_bar_R_values = X_Bar_R_Chart.objects.all()
        part_model = X_Bar_R_Chart.objects.values_list('part_model', flat=True).distinct().get()

        fromDateStr = X_Bar_R_Chart.objects.values_list('formatted_from_date', flat=True).get()
        toDateStr = X_Bar_R_Chart.objects.values_list('formatted_to_date', flat=True).get()

        parameter_name = X_Bar_R_Chart.objects.values_list('parameter_name', flat=True).get()
        operator = X_Bar_R_Chart.objects.values_list('operator', flat=True).get()
        machine = X_Bar_R_Chart.objects.values_list('machine', flat=True).get()
        shift = X_Bar_R_Chart.objects.values_list('shift', flat=True).get()

        # Convert sample_size to an integer
        sample_size = int(X_Bar_R_Chart.objects.values_list('sample_size', flat=True).get())

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
        print("filtered_readings",filtered_readings)

        if not filtered_readings:
            return {
                'no_results': True
            }



        total_count = len(filtered_readings)
        print("Total readings count:", total_count)

          # Retrieve distinct usl and lsl values from MeasurementData
        usl_values = MeasurementData.objects.filter(**filter_kwargs).values_list('usl', flat=True).distinct()
        lsl_values = MeasurementData.objects.filter(**filter_kwargs).values_list('lsl', flat=True).distinct()

        # Convert the querysets to single values
        usl = usl_values.first() if usl_values else None
        lsl = lsl_values.first() if lsl_values else None

        print("usl",usl)
        print("lsl",lsl)

        # Divide readings into subgroups based on sample_size (converted to integer)
        subgroups = [filtered_readings[i:i + sample_size] for i in range(0, len(filtered_readings), sample_size)]
        subgroups_length = len(subgroups)
        print("sub group length:",subgroups_length)

        # Calculate X-bar and Range (R) for each subgroup
        x_bars = [np.mean(group) for group in subgroups]
        print("x_bars",x_bars)
        ranges = [max(group) - min(group) for group in subgroups]

        # Calculate control limits
        x_bar, r_bar, UCLx, LCLx, UCLr, LCLr = calculate_control_limits(x_bars, ranges, sample_size)
        cp, cpk = calculate_cp_cpk(x_bars,ranges, usl, lsl)

        # Print the calculated values in the terminal
        print(f"X-bar: {x_bar:.5f}, R-bar: {r_bar:.5f}")
        print(f"UCLx: {UCLx:.5f}, LCLx: {LCLx:.5f}")
        print(f"UCLr: {UCLr:.5f}, LCLr: {LCLr:.5f}")
        print(f"cp: {cp}, cpk: {cpk}")

      # Divide readings into subgroups based on sample_size (converted to integer)
        subgroups = [filtered_readings[i:i + sample_size] for i in range(0, len(filtered_readings), sample_size)]

        # Calculate X-bar and Range (R) for each subgroup
        x_bars = [np.mean(group) for group in subgroups]
        ranges = [max(group) - min(group) for group in subgroups]





        # Create a DataFrame for the readings
        df = pd.DataFrame(subgroups).transpose()  # Transpose to have rows for readings and columns for samples
       # Renaming columns to X1, X2, ..., X20 (or fewer if there are fewer subgroups)
        max_columns = 20
        df.columns = [f'X{i+1}' for i in range(min(len(df.columns), max_columns))]

        # If there are more than 20 columns, you may want to handle them appropriately
        if len(df.columns) > max_columns:
            print("Warning: More than 20 columns present. Additional columns will not be displayed.")


        # Calculate Sum, Mean, and Range
        df.loc['Sum'] = df.sum()


        df.loc['X̄ (Mean)'] = x_bars  # Use pre-calculated means
        df.loc['R̄ (Range)'] = ranges  # Use pre-calculated ranges

        # Create row labels dynamically
        row_labels = [f'Row {i+1}' for i in range(len(subgroups))] + ['Sum', 'X̄ (Mean)', 'R̄ (Range)']

        # Set the index to the created row labels
        if len(row_labels) == len(df.index):
            df.index = row_labels  # Set the index if lengths match
        else:
            print("Mismatch in length between row labels and DataFrame index.")
            

        # Convert the DataFrame to HTML for rendering in the template
        table_html = df.to_html(classes="table table-striped", index=True, header=True)

        # Inline CSS styles for table formatting
        style = """
        <style>
            table.table {
                font-size: 10px; /* Decrease font size */
                width: 100%; /* Set table width to fit the container */
                max-height : 20%;
            }
            table.table th, table.table td {
                padding: 2px; /* Adjust padding for smaller row height */
                max-width: 50px; /* Set a max column width */
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
            }
            table.table th {
                background-color: #f2f2f2; /* Optional: Light gray background for headers */
            }
        </style>
        """

        # Combine the style and table HTML
        table_html = style + table_html


        # Create X-bar chart
        xbar_trace = go.Scatter(
            x=list(range(1, len(x_bars) + 1)),
            y=x_bars,
            mode='lines+markers',
            name='X-bar'
        )

        # Add UCL and LCL lines to X-bar chart
        UCLx_trace = go.Scatter(x=list(range(1, len(x_bars) + 1)), y=[UCLx] * len(x_bars), mode='lines', name='UCLx', line=dict(color='red', dash='dash'))
        LCLx_trace = go.Scatter(x=list(range(1, len(x_bars) + 1)), y=[LCLx] * len(x_bars), mode='lines', name='LCLx', line=dict(color='red', dash='dash'))
        x_bar_trace = go.Scatter(x=list(range(1, len(x_bars) + 1)), y=[x_bar] * len(x_bars), mode='lines', name='X-bar Line', line=dict(color='green', width=2))

        # Create R chart
        r_trace = go.Scatter(
            x=list(range(1, len(ranges) + 1)),
            y=ranges,
            mode='lines+markers',
            name='Range (R)'
        )

        # Add UCL and LCL lines to R chart
        UCLr_trace = go.Scatter(x=list(range(1, len(ranges) + 1)), y=[UCLr] * len(ranges), mode='lines', name='UCLr', line=dict(color='red', dash='dash'))
        LCLr_trace = go.Scatter(x=list(range(1, len(ranges) + 1)), y=[LCLr] * len(ranges), mode='lines', name='LCLr', line=dict(color='red', dash='dash'))
        r_bar_trace = go.Scatter(x=list(range(1, len(ranges) + 1)), y=[r_bar] * len(ranges), mode='lines', name='R-bar Line', line=dict(color='purple', width=2))

        # Layout for X-bar chart with reduced height and minimal margins
        xbar_layout = go.Layout(
            title='X-bar Chart',
            xaxis=dict(title='Subgroup'),
            yaxis=dict(title='Value'),
            height=220,  # Set height to 250px to fit within 500px total
            margin=dict(l=10, r=20, t=40, b=20),  # Reduce margins to minimize white space
        )

        # Layout for R chart with reduced height and minimal margins
        r_layout = go.Layout(
            title='R Chart',
            xaxis=dict(title='Subgroup'),
            yaxis=dict(title='Value'),
            height=220,  # Set height to 250px to fit within 500px total
            margin=dict(l=10, r=20, t=40, b=20),  # Reduce margins to minimize white space
        )


        # Create the figures with the respective layouts and traces
        xbar_chart = go.Figure(data=[xbar_trace, UCLx_trace, LCLx_trace, x_bar_trace], layout=xbar_layout)
        r_chart = go.Figure(data=[r_trace, UCLr_trace, LCLr_trace, r_bar_trace], layout=r_layout)


      # Assuming you have xbar_chart and r_chart defined
        if pdf:
            # Save the X-bar chart as a PNG image for the PDF
            xbar_img_bytes = pio.to_image(xbar_chart, format='png')  # Use plotly.io to convert to image bytes
            xbar_img_base64 = base64.b64encode(xbar_img_bytes).decode('utf-8')
            xbar_chart_html = f'<img src="data:image/png;base64,{xbar_img_base64}" alt="X-bar Chart">'

            # Save the R chart as a PNG image for the PDF
            r_img_bytes = pio.to_image(r_chart, format='png')  # Use plotly.io to convert to image bytes
            r_img_base64 = base64.b64encode(r_img_bytes).decode('utf-8')
            r_chart_html = f'<img src="data:image/png;base64,{r_img_base64}" alt="R Chart">'
        else:
            # Render the X-bar chart as an interactive HTML component for normal requests
            xbar_chart_html = pyo.plot(xbar_chart, include_plotlyjs=False, output_type='div')
            
            # Render the R chart as an interactive HTML component for normal requests
            r_chart_html = pyo.plot(r_chart, include_plotlyjs=False, output_type='div')
        # Pass the chart HTML and table HTML to the template
        return {
            'xbar_chart': xbar_chart_html,
            'r_chart': r_chart_html,
            'table_html': table_html,  # Pass the Pandas table HTML
            'x_bar_R_values':x_bar_R_values,
            'subgroups_length': subgroups_length,
            'x_bar':x_bar,
            'r_bar':r_bar,
            'UCLx':UCLx,
            'LCLx':LCLx,
             'UCLr':UCLr,
            'LCLr':LCLr,
            'cp':cp,
            'cpk':cpk
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

"""
1.df = pd.DataFrame(subgroups).transpose()  # Transpose to have rows for readings and columns for samples

        pd.DataFrame(subgroups): This creates a DataFrame from the list of subgroups. Each subgroup corresponds to a set of readings (e.g., a sample of data points).
        .transpose(): This method transposes the DataFrame, switching rows and columns. After this step, each row represents a sample (or reading) while each column represents a specific subgroup (e.g., X1, X2, ...).


2.df.columns = [f'X{i+1}' for i in range(len(df.columns))]  # Renaming columns to X1, X2, ...
        This line dynamically creates new column names for the DataFrame, assigning them labels like X1, X2, etc. This is useful for easily identifying each subgroup's data in the DataFrame.

"""