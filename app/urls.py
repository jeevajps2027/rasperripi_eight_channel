from django.conf import settings
from django.urls import path
from django.conf.urls.static import static
from .views import home,index,comport,probe,trace,parameter,master,measurebox,measurement,backup
from .views import utility,report,spc,srno,withoutsrno,paraReport,jobReport,xBar,xBarRchart,xBarSchart,reset_clear_flag,measurement_data_retrive
from .views import histogram,pieChart,measure,masterReport,measurement_count,shift_report,get_parameters, get_parameter_value,set_clear_flag
urlpatterns = [
    path('',home,name="home"),
    path('index/',index,name="index"),
    path('comport/',comport,name="comport"),
    path('probe/',probe,name="probe"),
    path('trace/',trace,name="trace"),
    path('parameter/',parameter,name="parameter"),
    path('master/',master,name="master"),
    path('measurebox/',measurebox,name="measurebox"),
    path('measurement/',measurement,name="measurement"),
    path('utility/',utility,name="utility"),
    path('report/',report,name="report"),
    path('spc/',spc,name="spc"),
    path('srno/',srno,name="srno"),
    path('withoutsrno/',withoutsrno,name="withoutsrno"),
    path('paraReport/',paraReport,name="paraReport"),
    path('jobReport/',jobReport,name="jobReport"),
    path('xBar/',xBar,name="xBar"),
    path('xBarRchart/',xBarRchart,name="xBarRchart"),
    path('xBarSchart/',xBarSchart,name="xBarSchart"),
    path('histogram/',histogram,name="histogram"),
    path('pieChart/',pieChart,name="pieChart"),
    path('measure/',measure,name="measure"),
    path('masterReport/',masterReport,name="masterReport"),
    path('measurement_count/',measurement_count,name="measurement_count"),
    path('shift_report/',shift_report,name="shift_report"), 
    path('get_parameters/', get_parameters, name='get_parameters'),
    path('get_parameter_value/', get_parameter_value, name='get_parameter_value'),
    path("set-clear-flag/", set_clear_flag, name="set_clear_flag"),
    path("reset-clear-flag/",reset_clear_flag, name="reset_clear_flag"),
    path("measurement_data_retrive/",measurement_data_retrive,name="measurement_data_retrive"),
    path('backup/',backup,name="backup"),
    ]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL,document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)