# yourapp/views.py

from django.http import JsonResponse
from app.models import TableClearFlag

def set_clear_flag(request):
    flag, created = TableClearFlag.objects.get_or_create(id=1)
    flag.clear_table = True
    flag.save()
    return JsonResponse({"status": "ok", "clear_table": flag.clear_table})
