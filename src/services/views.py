import uuid
from decimal import Decimal
from datetime import datetime, timezone
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import Http404, JsonResponse, HttpResponseNotAllowed
from django.shortcuts import render, redirect

from home.repositories import HomeRepository
from public_service_finder.utils.enums.service_status import ServiceStatus
from .forms import ServiceForm, DescriptionFormSet
from .models import ServiceDTO
from .repositories import ServiceRepository
from .forms import ServiceForm, DescriptionFormSet, ReviewResponseForm
from .models import ServiceDTO, ReviewDTO
from .repositories import ServiceRepository, ReviewRepository

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
                service_status=ServiceStatus.PENDING_APPROVAL.value,
                service_created_timestamp=datetime.now(timezone.utc).isoformat(),
                service_approved_timestamp="1900-01-01T00:00:00Z",
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
                service_status=ServiceStatus.PENDING_APPROVAL.value,
                service_created_timestamp=datetime.now(timezone.utc).isoformat(),
                service_approved_timestamp="1900-01-01T00:00:00Z",
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


@login_required
def review_list(request, service_id):
    review_repo = ReviewRepository()

    service = service_repo.get_service(service_id)
    if not service:
        raise Http404("Service not found")

    reviews = review_repo.get_reviews_for_service(service_id)

    return render(request, "review_list.html", {"service": service, "reviews": reviews})


@login_required
def respond_to_review(request, service_id, review_id):
    review_repo = ReviewRepository()

    # Get the service and verify ownership
    service = service_repo.get_service(service_id)
    if not service:
        raise Http404("Service not found")

    if str(request.user.id) != service.provider_id:
        messages.error(request, "You don't have permission to respond to this review.")
        return redirect('services:review_list', service_id=service_id)

    # Get all reviews for the service
    reviews = review_repo.get_reviews_for_service(service_id)
    review = next((r for r in reviews if r.review_id == review_id), None)

    if not review:
        raise Http404("Review not found")

    if request.method == 'POST':
        form = ReviewResponseForm(request.POST)
        if form.is_valid():
            if review_repo.respond_to_review(service_id, review_id, form.cleaned_data['response']):
                messages.success(request, "Response submitted successfully!")
                return redirect('services:review_list', service_id=service_id)
            else:
                messages.error(request, "Failed to submit response. Please try again.")
    else:
        form = ReviewResponseForm()

    return render(request, 'services/respond_to_review.html', {
        'service': service,
        'review': review,
        'form': form
    })


def get_service_by_id(service_id, provider_id):
    """Utility function to retrieve a service and verify ownership."""
    service = service_repo.get_service(service_id)
    if service and service.provider_id == str(provider_id):
        return service
    return None
