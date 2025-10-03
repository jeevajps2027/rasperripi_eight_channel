from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from app.models import ParameterFactor, parameter_settings
from django.db.models import Q

# Fetch parameter names based on selected part_model
def get_parameters(request):
    part_model = request.GET.get('part_model')

    if part_model:
        parameter_names = parameter_settings.objects.filter(
            model_id=part_model
        ).exclude(Q(attribute=True)).values_list('parameter_name', flat=True).order_by('id')

        return JsonResponse({'parameter_names': list(parameter_names)})

    return JsonResponse({'parameter_names': []})


# Fetch parameter value based on selected part_model and parameter_name
def get_parameter_value(request):
    part_model = request.GET.get('part_model')
    parameter_name = request.GET.get('parameter_name')

    if part_model and parameter_name:
        parameter_factor = ParameterFactor.objects.filter(
            part_model=part_model, parameter_name=parameter_name
        ).first()

        if parameter_factor:
            return JsonResponse({
                'value': parameter_factor.value or '',
                'method': parameter_factor.method or ''  # Fetch method value
            })

    return JsonResponse({'value': '', 'method': ''})
