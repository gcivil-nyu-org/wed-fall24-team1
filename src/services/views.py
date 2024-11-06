import uuid
from decimal import Decimal
from datetime import datetime, timezone
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import Http404, JsonResponse, HttpResponseNotAllowed
from django.shortcuts import render, redirect, get_object_or_404
from home.repositories import HomeRepository
from public_service_finder.utils.enums.service_status import ServiceStatus
from .forms import ServiceForm, DescriptionFormSet, ReviewResponseForm
from .models import ServiceDTO
from .repositories import ServiceRepository, ReviewRepository

service_repo = ServiceRepository()
review_repo = ReviewRepository()


@login_required
def service_list(request):
    if request.user.user_type != "service_provider":
        raise PermissionDenied

    services = service_repo.get_services_by_provider(request.user.id)

    # Filter out services without an ID
    valid_services = [service for service in services if service.id]

    return render(
        request,
        "service_list.html",
        {"services": valid_services},
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
                return redirect("services:list")
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
                return redirect("services:list")
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
        return redirect("services:list")

    # If it's not a POST request, return a 405 Method Not Allowed
    return HttpResponseNotAllowed(["POST"])


@login_required
def review_list(request, service_id):
    service = get_object_or_404(ServiceDTO, id=service_id)

    # Fetch all reviews for the service
    reviews = review_repo.get_reviews_for_service(service_id)
    print(reviews)

    # Debug log to verify retrieved data
    for review in reviews:
        print(f"Review ID {review.review_id} has responseText: {review.responseText}")

    # Pass the reviews and service to the template
    return render(request, "review_html.html", {"service": service, "reviews": reviews})


@login_required
def respond_to_review(request, service_id, review_id):
    # Check if the user is authenticated
    if not request.user.is_authenticated:
        return JsonResponse(
            {"status": "error", "message": "User not authenticated"}, status=403
        )

    # Fetch the service and review data
    service = service_repo.get_service(service_id)
    if not service:
        raise Http404("Service does not exist")

    if service.provider_id != str(request.user.id):
        return JsonResponse(
            {"status": "error", "message": "Permission denied"}, status=403
        )

    review = review_repo.get_review(review_id)
    if not review or review.service_id != service_id:
        raise Http404("Review does not exist or does not belong to this service")

    if request.method == "POST":
        form = ReviewResponseForm(request.POST)
        if form.is_valid():
            response_text = form.cleaned_data["responseText"]

            # Attempt to update the review response in DynamoDB
            success = review_repo.respond_to_review(review_id, response_text)
            if success:
                return JsonResponse(
                    {"status": "success", "message": "Response saved"}, status=200
                )
            else:
                return JsonResponse(
                    {"status": "error", "message": "Database update failed"}, status=500
                )
        else:
            return JsonResponse(
                {"status": "error", "message": "Invalid form data"}, status=400
            )

    # If GET request, render the response form template
    else:
        form = ReviewResponseForm()
        context = {
            "service": service,
            "review": review,
            "form": form,
        }
        return render(request, "respond_to_review.html", context)


def get_service_by_id(service_id, provider_id):
    """Utility function to retrieve a service and verify ownership."""
    service = service_repo.get_service(service_id)
    if service and service.provider_id == str(provider_id):
        return service
    return None
