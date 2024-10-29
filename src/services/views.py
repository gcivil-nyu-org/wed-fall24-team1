# from django.shortcuts import render
import uuid
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import Http404, JsonResponse, HttpResponseNotAllowed

# Create your views here.
# services/views.py
from django.shortcuts import render, redirect

from home.repositories import HomeRepository
from .forms import ServiceForm, DescriptionFormSet
from .models import ServiceDTO
from .repositories import ServiceRepository

service_repo = ServiceRepository()


@login_required
def service_list(request):
    if request.user.user_type != "service_provider":
        raise PermissionDenied

    services = service_repo.get_services_by_provider(request.user.id)

    # Filter out services without an ID
    valid_services = [service for service in services if service.id]

    if len(valid_services) != len(services):
        messages.warning(
            request,
            f"{len(services) - len(valid_services)} service(s) were found without a valid ID and have been omitted from the list.",
        )

    # Get all messages
    storage = messages.get_messages(request)
    message_list = list(storage)
    # Clear the messages
    storage.used = True

    return render(
        request,
        "service_list.html",
        {"services": valid_services, "messages": message_list},
    )


@login_required
def service_create(request):
    if request.user.user_type != "service_provider":
        raise PermissionDenied

    if request.method == "POST":
        form = ServiceForm(request.POST)
        description_formset = DescriptionFormSet(request.POST, prefix="description")

        if form.is_valid() and description_formset.is_valid():
            # Process the main form data
            service_data = form.cleaned_data

            # Process the description formset
            description_data = {}
            for description_form in description_formset:
                if (
                    description_form.cleaned_data
                    and not description_form.cleaned_data.get("DELETE", False)
                ):
                    key = description_form.cleaned_data["key"]
                    value = description_form.cleaned_data["value"]
                    description_data[key] = value
            # Create ServiceDTO with processed data

            service_dto = ServiceDTO(
                id=str(uuid.uuid4()),
                name=service_data["name"],
                address=service_data["address"],
                latitude=service_data["latitude"],
                longitude=service_data["longitude"],
                ratings=Decimal("0"),
                description=description_data,
                category=service_data["category"],
                provider_id=str(request.user.id),
            )

            if service_repo.create_service(service_dto):
                messages.success(request, "Service created successfully!")
                return redirect("services:list")
            messages.error(request, "Error creating service.")
    else:
        form = ServiceForm()
        description_formset = DescriptionFormSet(prefix="description")

    return render(
        request,
        "service_form.html",
        {"form": form, "description_formset": description_formset, "action": "Create"},
    )


@login_required
def service_edit(request, service_id):
    try:
        _ = uuid.UUID(service_id)
    except ValueError:
        raise Http404("Invalid service_id")

    if request.user.user_type != "service_provider":
        raise PermissionDenied

    service = service_repo.get_service(service_id)
    if not service or service.provider_id != str(request.user.id):
        raise PermissionDenied

    # Reverse translation for category
    category_reverse_translation = {
        "MENTAL": "Mental Health Center",
        "SHELTER": "Homeless Shelter",
        "FOOD": "Food Pantry",
        "RESTROOM": "Restroom",
    }

    if request.method == "POST":
        form = ServiceForm(request.POST)
        description_formset = DescriptionFormSet(request.POST, prefix="description")

        if form.is_valid() and description_formset.is_valid():
            service_data = form.cleaned_data

            description_data = {}
            for description_form in description_formset:
                if (
                    description_form.cleaned_data
                    and not description_form.cleaned_data.get("DELETE", False)
                ):
                    key = description_form.cleaned_data["key"]
                    value = description_form.cleaned_data["value"]
                    description_data[key] = value

            updated_service = ServiceDTO(
                id=service_id,
                name=service_data["name"],
                address=service_data["address"],
                latitude=service_data["latitude"],
                longitude=service_data["longitude"],
                ratings=service.ratings,
                description=description_data,
                category=service_data[
                    "category"
                ],  # This is already translated in the form's clean method
                provider_id=str(request.user.id),
            )

            if service_repo.update_service(updated_service):
                messages.success(request, "Service updated successfully!")
                return redirect("services:list")
            messages.error(request, "Error updating service.")
    else:
        initial_data = {
            "name": service.name,
            "address": service.address,
            "category": category_reverse_translation.get(
                service.category, service.category
            ),
        }
        form = ServiceForm(initial=initial_data)

        # Prepare initial data for description formset
        description_initial = [
            {"key": k, "value": v} for k, v in service.description.items()
        ]
        description_formset = DescriptionFormSet(
            initial=description_initial, prefix="description"
        )

    return render(
        request,
        "service_form.html",
        {
            "form": form,
            "description_formset": description_formset,
            "action": "Edit",
            "service": service,
        },
    )


@login_required
def service_details(request, service_id):
    service = service_repo.get_service(service_id)
    home_repo = HomeRepository()
    reviews = home_repo.fetch_reviews_for_service(service_id)
    data = {
        "id": service.id,
        "name": service.name,
        "category": service.category,
        "address": service.address,
        "latitude": float(service.latitude),
        "longitude": float(service.longitude),
        "description": service.description,
        "reviews": reviews,
    }

    return JsonResponse(data)


@login_required
def service_delete(request, service_id):
    try:
        _ = uuid.UUID(service_id)
    except ValueError:
        raise Http404("Invalid service ID")

    if request.user.user_type != "service_provider":
        raise PermissionDenied

    service = service_repo.get_service(service_id)
    if not service or service.provider_id != str(request.user.id):
        raise PermissionDenied

    if request.method == "POST":
        if service_repo.delete_service(service_id):
            messages.success(request, "Service deleted successfully!")
        else:
            messages.error(request, "Error deleting service.")
        return redirect("services:list")

    # If it's not a POST request, return a 405 Method Not Allowed
    return HttpResponseNotAllowed(["POST"])
