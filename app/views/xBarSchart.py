import matplotlib.pyplot as plt
import io
import urllib, base64
from django.shortcuts import render
import numpy as np

def xBarSchart(request):
    # Data points (you may have multiple samples, grouped into subgroups)
    data = [
        [14.9833, 15.0017, 15.00],    # Sample 1
        [15.02, 15.0017, 14.999],     # Sample 2
        [14.985, 15.005, 14.995],     # Sample 3
        [15.005, 14.995, 15.000],     # Sample 4
    ]

    # Control limits and nominal values
    nominal = 15.00
    usl = 15.01  # Upper Specification Limit (USL)
    lsl = 14.99  # Lower Specification Limit (LSL)

    # Calculate X-bar (means) and S (standard deviations) for each sample
    x_bars = [np.mean(sample) for sample in data]
    s_values = [np.std(sample, ddof=1) for sample in data]  # ddof=1 for sample std deviation

    # Calculate overall X-bar and S-bar (mean of sample means and std deviations)
    overall_x_bar = np.mean(x_bars)
    overall_s_bar = np.mean(s_values)

    # Control limits for S chart (using control constants for 3 samples)
    B3 = 0  # For n=3
    B4 = 2.568  # For n=3
    s_ucl = B4 * overall_s_bar  # Upper Control Limit for S chart
    s_lcl = B3 * overall_s_bar  # Lower Control Limit for S chart (will be 0 due to B3=0)

    # Generate the X-bar chart
    plt.figure(figsize=(10, 12))

    # X-bar chart
    plt.subplot(2, 1, 1)
    plt.plot(x_bars, marker='o', color='blue', linestyle='-', label='X-bar (Sample Mean)')
    plt.axhline(y=usl, color='red', linestyle='--', label='USL (15.01)')
    plt.axhline(y=lsl, color='red', linestyle='--', label='LSL (14.99)')
    plt.axhline(y=nominal, color='green', linestyle='-', label='Nominal (15.00)')
    plt.axhline(y=overall_x_bar, color='purple', linestyle='-', label=f'Overall X-bar (Mean: {overall_x_bar:.5f})')
    plt.title('X-bar Control Chart')
    plt.xlabel('Sample Number')
    plt.ylabel('Measurement')
    plt.legend(loc='upper right')

    # S chart
    plt.subplot(2, 1, 2)
    plt.plot(s_values, marker='o', color='blue', linestyle='-', label='S (Sample Std. Dev.)')
    plt.axhline(y=s_ucl, color='red', linestyle='--', label=f'UCL (S) = {s_ucl:.5f}')
    plt.axhline(y=s_lcl, color='red', linestyle='--', label=f'LCL (S) = {s_lcl:.5f}')
    plt.axhline(y=overall_s_bar, color='purple', linestyle='-', label=f'S-bar (Mean: {overall_s_bar:.5f})')
    plt.title('S Control Chart')
    plt.xlabel('Sample Number')
    plt.ylabel('Standard Deviation')
    plt.legend(loc='upper right')

    # Save the plot to a bytes buffer instead of a file
    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format='png')
    buf.seek(0)

    # Encode the image to base64 so that it can be embedded in the HTML
    string = base64.b64encode(buf.read())
    uri = urllib.parse.quote(string)

    # Pass the image URI to the template
    context = {'chart': uri}
    return render(request, 'app/spc/xBarSchart.html', context)
