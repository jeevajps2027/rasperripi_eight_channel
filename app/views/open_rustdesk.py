from django.http import JsonResponse
import subprocess

def open_rustdesk(request):
    try:
        # Run RustDesk as a background process
        subprocess.Popen(["rustdesk"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return JsonResponse({"status": "success", "message": "RustDesk opened"})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)})
