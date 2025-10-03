from datetime import datetime
from django.db import models # type: ignore


  

class probe_calibrations(models.Model):
    probe_id = models.CharField(max_length=50, unique=True)
    low_ref = models.JSONField(null=True, blank=True)  # Storing a_values as a JSON array
    low_count = models.JSONField(null=True, blank=True)  # Storing a1_values as a JSON array
    high_ref = models.JSONField(null=True, blank=True)  # Storing b_values as a JSON array
    high_count = models.JSONField(null=True, blank=True)  # Storing b1_values as a JSON array
    coefficent = models.JSONField(null=True, blank=True)  # Storing e_values as a JSON array

class TableOneData(models.Model):
    part_model = models.CharField(max_length=100)
    customer_name = models.CharField(max_length=100)
    part_name = models.CharField(max_length=100)
    part_no = models.CharField(max_length=100)
    char_lmt = models.CharField(max_length=100)
    hide = models.BooleanField(default=False)    









class TableTwoData(models.Model):
    batch_no = models.CharField(max_length=100)

class TableThreeData(models.Model):
    machine_no = models.CharField(max_length=100)
    machine_name = models.CharField(max_length=100)

class TableFourData(models.Model):
    operator_no = models.CharField(max_length=100)
    operator_name = models.CharField(max_length=100)

class TableFiveData(models.Model):
    vendor_code = models.CharField(max_length=100)
    email = models.EmailField()











class comport_settings(models.Model):
    card = models.CharField(max_length=50)
    com_port = models.CharField(max_length=50)
    baud_rate = models.IntegerField()
    bytesize = models.IntegerField()  
    stopbits = models.IntegerField()
    parity = models.CharField(max_length=50)

    def __str__(self):
        return f"COM Port: {self.com_port}, Baud Rate: {self.baud_rate}"


class Master_settings(models.Model):
    probe_no = models.CharField(max_length=100,null=True,blank=True)
    a = models.FloatField(null=True,blank=True)
    a1 = models.IntegerField(null=True, default=0)
    b = models.FloatField(null=True,blank=True)
    b1 = models.IntegerField(null=True, default=0)
    e = models.FloatField(null=True,blank=True)
    d = models.FloatField(null=True,blank=True)
    o1 = models.FloatField(null=True,blank=True)
    parameter_name = models.CharField(max_length=100,null=True,blank=True)
    selected_value = models.CharField(max_length=100,null=True,blank=True)
    selected_mastering = models.CharField(max_length=100,null=True,blank=True)
    operator = models.CharField(max_length=100,null=True,blank=True)
    machine = models.CharField(max_length=100,null=True,blank=True)
    shift = models.CharField(max_length=100,null=True,blank=True)
    date_time = models.DateTimeField(null=True,blank=True)  # Change to CharField


    
class parameter_settings(models.Model):
    model_id = models.CharField(max_length=255)
    parameter_name = models.CharField(max_length=255)
    sr_no = models.IntegerField()
    single_radio = models.BooleanField(default=False)
    analog_zero = models.FloatField(blank=True, null=True)
    reference_value = models.FloatField(blank=True, null=True)
    double_radio = models.BooleanField(default=False)
    high_mv = models.FloatField(blank=True, null=True)
    low_mv = models.FloatField(blank=True, null=True)    
    probe_no = models.CharField(max_length=255)
    measurement_mode = models.CharField(max_length=50)
    nominal = models.FloatField(blank=True, null=True)  # Allow null
    usl = models.FloatField(blank=True, null=True)
    lsl = models.FloatField(blank=True, null=True)
    utl = models.FloatField(blank=True, null=True)
    ltl = models.FloatField(blank=True, null=True)
    job_dia = models.CharField(max_length=10)
    digits = models.IntegerField(blank=True, null=True)
    mastering = models.FloatField(blank=True, null=True)
    step_no = models.FloatField(blank=True, null=True)
    hide_checkbox = models.BooleanField(default=False)
    attribute = models.BooleanField(default=False)
    auto_man = models.BooleanField(default=False)
    timer = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f'{self.model_id} - {self.parameter_name}'


class MeasurementData(models.Model):
    parameter_name = models.CharField(max_length=100)
    readings = models.FloatField(blank=True, null=True)
    nominal = models.FloatField(blank=True, null=True)
    lsl = models.FloatField(blank=True, null=True)
    usl = models.FloatField(blank=True, null=True)
    status_cell = models.CharField(max_length=100)
    date = models.DateTimeField()
    operator = models.CharField(max_length=100)
    shift = models.CharField(max_length=100)
    machine = models.CharField(max_length=100)
    part_model = models.CharField(max_length=100)
    part_status = models.CharField(max_length=100)
    customer_name = models.CharField(max_length=100)
    comp_sr_no = models.CharField(max_length=100)
    ltl = models.FloatField(blank=True, null=True)
    utl = models.FloatField(blank=True, null=True)
    
class InterlinkData(models.Model):
    status_cell = models.CharField(max_length=100)
    date = models.DateTimeField()
    operator = models.CharField(max_length=100)
    part_model = models.CharField(max_length=100)
    part_status = models.CharField(max_length=100)
    comp_sr_no = models.CharField(max_length=100)
    shift = models.CharField(max_length=100)
    machine = models.CharField(max_length=100)

class StationOne(models.Model):
    status_cell = models.CharField(max_length=100)
    date = models.DateTimeField()
    operator = models.CharField(max_length=100)
    part_model = models.CharField(max_length=100)
    part_status = models.CharField(max_length=100)
    comp_sr_no = models.CharField(max_length=100)
    shift = models.CharField(max_length=100)
    machine = models.CharField(max_length=100)    
    
class MasterIntervalSettings(models.Model):
    timewise = models.BooleanField(default=False)
    componentwise = models.BooleanField(default=False)
    hour = models.IntegerField(null=True, blank=True)
    minute = models.IntegerField(null=True, blank=True)
    component_no = models.IntegerField(null=True, blank=True)

class ShiftSettings(models.Model):
    shift = models.CharField(max_length=50)
    shift_time = models.CharField(max_length=20) 

    def __str__(self):
        return f"{self.shift} - {self.shift_time}"

    def save(self, *args, **kwargs):
        if self.shift_time:  # Convert the string to a datetime object
            try:
                parsed_time = datetime.strptime(self.shift_time, "%I:%M:%S %p")
                self.shift_time = parsed_time.strftime(" %I:%M:%S %p")
            except ValueError:
                # Handle the case where the string is not in the expected format
                pass
        super().save(*args, **kwargs)


class TimeSetting(models.Model):
    start_time = models.CharField(max_length=100, null=False)
    stop_time = models.CharField(max_length=100, null=False)


class measure_data(models.Model):
    part_model = models.CharField(max_length=100)
    operator = models.CharField(max_length=100)
    machine = models.CharField(max_length=100)
    shift = models.CharField(max_length=100)

    def __str__(self):
        return f'Measurement: {self.part_model}, Operator: {self.operator}, Machine: {self.machine}, Shift: {self.shift}'
    

class CustomerDetails(models.Model):
    customer_name = models.CharField(max_length=100)
    
    primary_contact_person = models.CharField(max_length=100)
    secondary_contact_person = models.CharField(max_length=100, blank=True, null=True)
    
    primary_email = models.CharField(max_length=100)
    secondary_email = models.CharField(max_length=100, blank=True, null=True)
    
    primary_phone_no = models.CharField(max_length=20)
    secondary_phone_no = models.CharField(max_length=20, blank=True, null=True)
    
    primary_dept = models.CharField(max_length=100)
    secondary_dept = models.CharField(max_length=100,blank=True, null=True)
    mac_address = models.CharField(max_length=50, blank=True, null=True)
    ip_address = models.CharField(max_length=50, blank=True, null=True)
    
    address = models.TextField()

 
      
class UserLogin(models.Model):
    username = models.CharField(max_length=255)
    password = models.CharField(max_length=255)

class consolidate_with_srno(models.Model):
    part_model = models.CharField(max_length=100)
    parameter_name = models.CharField(max_length=100)
    operator = models.CharField(max_length=100)
    formatted_from_date = models.CharField(max_length=100)
    formatted_to_date = models.CharField(max_length=100)
    machine = models.CharField(max_length=100)
    vendor_code = models.CharField(max_length=100)
    job_no = models.CharField(max_length=100)
    shift = models.CharField(max_length=100)
    current_date_time = models.CharField(max_length=100)

class consolidate_without_srno(models.Model):
    part_model = models.CharField(max_length=100)
    parameter_name = models.CharField(max_length=100)
    operator = models.CharField(max_length=100)
    formatted_from_date = models.CharField(max_length=100)
    formatted_to_date = models.CharField(max_length=100)
    machine = models.CharField(max_length=100)
    vendor_code = models.CharField(max_length=100)
    shift = models.CharField(max_length=100)
    current_date_time = models.CharField(max_length=100)

class parameterwise_report(models.Model):
    part_model = models.CharField(max_length=100)
    parameter_name = models.CharField(max_length=100)
    operator = models.CharField(max_length=100)
    formatted_from_date = models.CharField(max_length=100)
    formatted_to_date = models.CharField(max_length=100)
    machine = models.CharField(max_length=100)
    vendor_code = models.CharField(max_length=100)
    job_no = models.CharField(max_length=100)
    shift = models.CharField(max_length=100)
    current_date_time = models.CharField(max_length=100)

class jobwise_report(models.Model):
    part_model = models.CharField(max_length=100)
    job_no = models.CharField(max_length=100)
    current_date_time = models.CharField(max_length=100)

class ResetCount(models.Model):
    part_model = models.CharField(max_length=100)
    date = models.CharField(max_length=100)    

class X_Bar_Chart(models.Model):
    part_model = models.CharField(max_length=100)
    parameter_name = models.CharField(max_length=100)
    operator = models.CharField(max_length=100)
    formatted_from_date = models.CharField(max_length=100)
    formatted_to_date = models.CharField(max_length=100)
    machine = models.CharField(max_length=100)
    vendor_code = models.CharField(max_length=100)
    shift = models.CharField(max_length=100)
    current_date_time = models.CharField(max_length=100)


class X_Bar_R_Chart(models.Model):
    part_model = models.CharField(max_length=100)
    parameter_name = models.CharField(max_length=100)
    operator = models.CharField(max_length=100)
    formatted_from_date = models.CharField(max_length=100)
    formatted_to_date = models.CharField(max_length=100)
    machine = models.CharField(max_length=100)
    vendor_code = models.CharField(max_length=100)
    sample_size = models.CharField(max_length=100)
    shift = models.CharField(max_length=100)
    current_date_time = models.CharField(max_length=100)

class X_Bar_S_Chart(models.Model):
    part_model = models.CharField(max_length=100)
    parameter_name = models.CharField(max_length=100)
    operator = models.CharField(max_length=100)
    formatted_from_date = models.CharField(max_length=100)
    formatted_to_date = models.CharField(max_length=100)
    machine = models.CharField(max_length=100)
    vendor_code = models.CharField(max_length=100)
    sample_size = models.CharField(max_length=100)
    shift = models.CharField(max_length=100)
    current_date_time = models.CharField(max_length=100)

class Histogram_Chart(models.Model):
    part_model = models.CharField(max_length=100)
    parameter_name = models.CharField(max_length=100)
    operator = models.CharField(max_length=100)
    formatted_from_date = models.CharField(max_length=100)
    formatted_to_date = models.CharField(max_length=100)
    machine = models.CharField(max_length=100)
    vendor_code = models.CharField(max_length=100)
    sample_size = models.CharField(max_length=100)
    shift = models.CharField(max_length=100)
    current_date_time = models.CharField(max_length=100)

class Pie_Chart(models.Model):
    part_model = models.CharField(max_length=100)
    parameter_name = models.CharField(max_length=100)
    operator = models.CharField(max_length=100)
    formatted_from_date = models.CharField(max_length=100)
    formatted_to_date = models.CharField(max_length=100)
    machine = models.CharField(max_length=100)
    vendor_code = models.CharField(max_length=100)
    sample_size = models.CharField(max_length=100)
    shift = models.CharField(max_length=100)
    current_date_time = models.CharField(max_length=100)
    

class BackupSettings(models.Model):
    backup_date = models.CharField(max_length=100)  # You can use DateTimeField if needed
    confirm_backup = models.BooleanField(default=False)  # New field to store checkbox value


    def __str__(self):
        return str(self.backup_date)
    


class master_report(models.Model):
    part_model = models.CharField(max_length=100)
    parameter_name = models.CharField(max_length=100)
    operator = models.CharField(max_length=100)
    formatted_from_date = models.CharField(max_length=100)
    formatted_to_date = models.CharField(max_length=100)
    machine = models.CharField(max_length=100)
    vendor_code = models.CharField(max_length=100)
    job_no = models.CharField(max_length=100)
    shift = models.CharField(max_length=100)
    current_date_time = models.CharField(max_length=100)    



class ParameterFactor(models.Model):
    part_model = models.CharField(max_length=255)
    parameter_name = models.CharField(max_length=255)
    method = models.CharField(max_length=10, choices=[('+', '+'), ('-', '-')])  # Choose between '+' or '-'
    value = models.CharField(max_length=255)

    # Add a unique constraint to part_model and parameter_name to ensure there is only one per combination
    class Meta:
        unique_together = ('part_model', 'parameter_name')  # Ensures unique (part_model, parameter_name) combination

    def __str__(self):
        return f"{self.part_model} - {self.parameter_name}"


class MailSettings(models.Model):
    sender_email = models.EmailField()
    sender_password = models.CharField(max_length=255)
    smtp_server = models.CharField(max_length=255, default='smtp.gmail.com')
    smtp_port = models.IntegerField(default=587)

    def __str__(self):
        return self.sender_email



        
class TableClearFlag(models.Model):
    clear_table = models.BooleanField(default=False)

    def __str__(self):
        return f"Clear Table: {self.clear_table}"