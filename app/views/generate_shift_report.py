from datetime import datetime
from io import BytesIO
from django.core.mail import EmailMessage
from django.http import JsonResponse
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from app.models import MeasurementData, CustomerDetails
from django.views.decorators.csrf import csrf_exempt
import json

from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML

@csrf_exempt
def shift_report(request):
    if request.method == 'POST':
        try:
            # Parse JSON data from request body
            data = json.loads(request.body)
            shift_name = data.get('shift_name')
            from_date_str = data.get('from_date')  # Received from client (formatted)
            end_date_str = data.get('end_date')    # Received from client (formatted)

            print("Received Shift Name:", shift_name)
            print("Received From Date:", from_date_str)
            print("Received End Date:", end_date_str)

            # Convert string dates to datetime objects
            try:
                from_date_obj = datetime.strptime(from_date_str, '%Y-%m-%d %I:%M:%S %p')  # '2025-02-18 8:00:00 AM'
                end_date_obj = datetime.strptime(end_date_str, '%Y-%m-%d %I:%M:%S %p')    # '2025-02-18 12:47:00 PM'
            except ValueError:
                return JsonResponse({'error': 'Invalid date format for from_date or end_date'}, status=400)

            print("Parsed From Date:", from_date_obj)
            print("Parsed End Date:", end_date_obj)

            # Fetch filtered data based on shift_name and date range
            data = MeasurementData.objects.filter(
                shift=shift_name,
                date__range=[from_date_obj, end_date_obj]
            )

            print('your data to send this is :::::::::::::',data)


             # Render the template with filtered data
            
            if not data.exists():
                return JsonResponse({'error': 'No data found for the given shift and date range'}, status=404)

            # Generate PDF
            pdf_buffer = BytesIO()
            p = canvas.Canvas(pdf_buffer, pagesize=(letter[1], letter[0]))
            width, height = letter
            y_position = height - 50
            p.setFont("Helvetica-Bold", 14)
            p.drawString(50, y_position, f"Shift Report - {shift_name} ({from_date_str} to {end_date_str})")
            p.setFont("Helvetica", 12)
            y_position -= 30

            # Headers
            headers = [
                "Operator", "Machine", "Part Model", "Part Status",
                "Customer Name", "Comp. SR No.", "Parameter", "Reading",
            ]
            x_positions = [50, 150, 250, 350, 450, 550, 650, 750, 850]

            for i, header in enumerate(headers):
                p.rect(x_positions[i], y_position, 100, 20)
                p.drawString(x_positions[i] + 5, y_position + 5, header)
            y_position -= 20

            # Data rows
            for obj in data:
                for i in range(len(headers)):
                    p.rect(x_positions[i], y_position, 100, 20)

                p.drawString(x_positions[0] + 5, y_position + 5, obj.parameter_name)
                p.drawString(x_positions[1] + 5, y_position + 5, str(obj.readings or ""))
                p.drawString(x_positions[2] + 5, y_position + 5, obj.status_cell)
                p.drawString(x_positions[3] + 5, y_position + 5, obj.operator)
                p.drawString(x_positions[4] + 5, y_position + 5, obj.machine)
                p.drawString(x_positions[5] + 5, y_position + 5, obj.part_model)
                p.drawString(x_positions[6] + 5, y_position + 5, obj.part_status)
                p.drawString(x_positions[7] + 5, y_position + 5, obj.customer_name)
                p.drawString(x_positions[8] + 5, y_position + 5, obj.comp_sr_no)

                y_position -= 20
                if y_position < 50:
                    p.showPage()
                    p.setFont("Helvetica", 12)
                    y_position = height - 50

            p.showPage()
            p.save()
            pdf_buffer.seek(0)

            # Retrieve recipient email from CustomerDetails model
            email_1 = CustomerDetails.objects.values_list('primary_email', flat=True).first()
            if not email_1:
                return JsonResponse({'error': 'No primary email found'}, status=400)

            current_datetime = datetime.now().strftime('%Y-%m-%d %I:%M:%S %p')

            # Send email with PDF attachment
            email = EmailMessage(
                subject=f"Shift Report - {shift_name} ({from_date_str} to {end_date_str})",
                body="Please find the attached shift report.",
                from_email="gaugelogic.report@gmail.com",
                to=[email_1]
            )
            email.attach(f"Shift_Report_{shift_name}_{from_date_str}.pdf", pdf_buffer.getvalue(), "application/pdf")
            email.send()

            return JsonResponse({'message': f'Shift report sent to {email_1}'})

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON format'}, status=400)

    return JsonResponse({'error': 'Invalid request'}, status=400)
