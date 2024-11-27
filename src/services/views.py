import uuid
from decimal import Decimal
from datetime import datetime, timedelta, timezone
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import (
    Http404,
    JsonResponse,
    HttpResponse,
    HttpResponseNotAllowed,
)
from django.shortcuts import render, redirect
from django.utils import timezone as timezone2  # Ensure this is imported
from forum.models import Notification
from home.repositories import HomeRepository
from public_service_finder.utils.enums.service_status import ServiceStatus
from .forms import ServiceForm, DescriptionFormSet, ReviewResponseForm
from .models import ServiceDTO
from .repositories import ServiceRepository, ReviewRepository
from collections import Counter
import re
from accounts.models import CustomUser

service_repo = ServiceRepository()
review_repo = ReviewRepository()
home_repo = HomeRepository()


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
            is_active = service_data.get("is_active", True)

            # Process the description formset
            description_data = {}
            for description_form in description_formset:
                if (
                    description_form.cleaned_data
                    and not description_form.cleaned_data.get("DELETE", False)
                ):
                    key = description_form.cleaned_data["key"]
                    value = description_form.cleaned_data["value"]
                    if key in description_data:
                        if isinstance(description_data[key], list):
                            description_data[key].append(value)
                        else:
                            description_data[key] = [description_data[key], value]
                    else:
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
                is_active=is_active,
                announcement=service_data.get("announcement")
            )
            if service_repo.create_service(service_dto):
                return redirect("services:list")
        else:
            return render(
                request,
                "service_form.html",
                {
                    "form": form,
                    "description_formset": description_formset,
                    "action": "Create",
                },
            )
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
    service = verify_service(request, service_id)

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
            new_is_active = service_data.get("is_active", True)

            # Collect new description data
            new_description_data = {}
            for description_form in description_formset:
                if (
                    description_form.cleaned_data
                    and not description_form.cleaned_data.get("DELETE", False)
                ):
                    key = description_form.cleaned_data.get("key")
                    value = description_form.cleaned_data.get("value")
                    if key and value:  # Only add if both key and value are present
                        new_description_data[key] = value
                if (
                    description_form.cleaned_data
                    and not description_form.cleaned_data.get("DELETE", False)
                ):
                    key = description_form.cleaned_data["key"]
                    value = description_form.cleaned_data["value"]
                    new_description_data[key] = value

            # Determine if any fields other than `is_active` have changed
            fields_changed = (
                service.name != service_data["name"]
                or service.address != service_data["address"]
                or service.latitude != service_data["latitude"]
                or service.longitude != service_data["longitude"]
                or service.category != service_data["category"]
                or service.description != new_description_data
            )

            # Check if `is_active` was toggled
            is_active_toggled = service.is_active != new_is_active

            new_announcement = service_data.get("announcement", "")
            announcement_changed = service.announcement != new_announcement

            # Decide the `service_status` based on changes
            if not fields_changed and is_active_toggled:
                # Retain the approved status if previously approved
                new_service_status = (
                    ServiceStatus.APPROVED.value
                    if service.service_status == ServiceStatus.APPROVED.value
                    else ServiceStatus.PENDING_APPROVAL.value
                )
            elif fields_changed:
                new_service_status = ServiceStatus.PENDING_APPROVAL.value
            else:
                # Default to pending approval if any other field changes
                new_service_status = service.service_status

            # Prepare updated service DTO
            updated_service = ServiceDTO(
                id=service_id,
                name=service_data["name"],
                address=service_data["address"],
                latitude=service_data["latitude"],
                longitude=service_data["longitude"],
                ratings=service.ratings,
                description=new_description_data,
                category=service_data["category"],
                provider_id=str(request.user.id),
                service_status=new_service_status,
                service_created_timestamp=service.service_created_timestamp,
                service_approved_timestamp=service.service_approved_timestamp,
                is_active=new_is_active,
                announcement=service_data.get("announcement"),
            )

            if announcement_changed and new_announcement.strip():
                # Get all bookmarks for this service
                bookmarks = home_repo.get_bookmarks_for_service(service_id)

                # Create notifications for each user who bookmarked the service
                for bookmark in bookmarks:
                    try:
                        user = CustomUser.objects.get(id=bookmark['UserId'])
                        Notification.objects.create(
                            recipient=user,
                            sender=request.user,
                            post=None,
                            comment=None,
                            message=f"New announcement from {service.name}: {new_announcement[:50]}{'...' if len(new_announcement) > 50 else ''}",
                            notification_type="announcement"
                        )
                    except CustomUser.DoesNotExist:
                        continue

            if service_repo.update_service(updated_service):
                return redirect("services:list")

        else:
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

    else:
        initial_data = {
            "name": service.name,
            "address": service.address,
            "category": category_reverse_translation.get(
                service.category, service.category
            ),
            "is_active": service.is_active,
            "announcement": service.announcement
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
    reviews = home_repo.fetch_reviews_for_service(service_id)
    data = {
        "id": service.id,
        "name": service.name,
        "category": service.category,
        "address": service.address,
        "latitude": float(service.latitude),
        "longitude": float(service.longitude),
        "description": service.description,
        "is_active": service.is_active,
        "reviews": reviews,
        "announcement": service.announcement,
    }

    return JsonResponse(data)


def service_delete(request, service_id):
    _ = verify_service(request, service_id)

    if request.method == "POST":
        if service_repo.delete_service(service_id):
            return redirect("services:list")
        else:
            return HttpResponse("Failed to delete service.", status=500)

    # If it's not a POST request, return a 405 Method Not Allowed
    return HttpResponseNotAllowed(["POST"])


def verify_service(request, service_id):
    try:
        _ = uuid.UUID(service_id)
    except ValueError:
        raise Http404("Invalid service ID")
    if request.user.user_type != "service_provider":
        raise PermissionDenied
    service = service_repo.get_service(service_id)
    if not service or service.provider_id != str(request.user.id):
        raise PermissionDenied
    return service

@login_required
def review_list(request, service_id):
    service = service_repo.get_service(service_id)
    if not service:
        raise Http404("Service does not exist")

    # Fetch all reviews for the service
    reviews = review_repo.get_reviews_for_service(service_id)

    # Pass the reviews and service to the template
    return render(request, "review_list.html", {"service": service, "reviews": reviews})


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
                reviewer_id = (
                    review.user_id
                )  # Assuming this is how you store the reviewer's ID
                try:
                    reviewer = CustomUser.objects.get(id=reviewer_id)
                    # In services/views.py, in the respond_to_review view:
                    Notification.objects.create(
                        recipient=reviewer,
                        sender=request.user,
                        post=None,
                        comment=None,
                        message=f"Service provider responded to your review of {service.name}",
                        notification_type="review_response",  # Add this line
                    )
                except CustomUser.DoesNotExist:
                    pass  # Handle the case where the user doesn't exist

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


@login_required
def dashboard(request):
    if request.user.user_type != "service_provider":
        raise PermissionDenied

    return render(request, "dashboard.html")


@login_required
def bookmarks_over_time(request):
    if request.user.user_type != "service_provider":
        return JsonResponse({"error": "Unauthorized"}, status=403)

    services = service_repo.get_services_by_provider(request.user.id)
    service_ids = [service.id for service in services]

    bookmarks = home_repo.get_bookmarks_for_services(service_ids)

    # Process bookmarks to get counts over the last 30 days
    today = timezone2.now().date()
    dates = [today - timedelta(days=i) for i in range(29, -1, -1)]
    date_strs = [date.isoformat() for date in dates]
    bookmarks_over_time = {date_str: 0 for date_str in date_strs}

    for bookmark in bookmarks:
        timestamp = datetime.fromisoformat(bookmark["timestamp"]).date().isoformat()
        if timestamp in bookmarks_over_time:
            bookmarks_over_time[timestamp] += 1

    data = {
        "dates": date_strs,
        "counts": [bookmarks_over_time[date_str] for date_str in date_strs],
    }
    return JsonResponse(data)


@login_required
def reviews_over_time(request):
    if request.user.user_type != "service_provider":
        return JsonResponse({"error": "Unauthorized"}, status=403)

    services = service_repo.get_services_by_provider(request.user.id)
    service_ids = [service.id for service in services]

    reviews = home_repo.get_reviews_for_services(service_ids)

    # Process reviews to get counts over the last 30 days
    today = timezone2.now().date()
    dates = [today - timedelta(days=i) for i in range(29, -1, -1)]
    date_strs = [date.isoformat() for date in dates]
    reviews_over_time = {date_str: 0 for date_str in date_strs}

    for review in reviews:
        timestamp = datetime.fromisoformat(review["Timestamp"]).date().isoformat()
        if timestamp in reviews_over_time:
            reviews_over_time[timestamp] += 1

    data = {
        "dates": date_strs,
        "counts": [reviews_over_time[date_str] for date_str in date_strs],
    }

    return JsonResponse(data)


@login_required
def average_rating_over_time(request):
    if request.user.user_type != "service_provider":
        return JsonResponse({"error": "Unauthorized"}, status=403)

    services = service_repo.get_services_by_provider(request.user.id)
    service_ids = [service.id for service in services]

    reviews = home_repo.get_reviews_for_services(service_ids)

    # Process reviews to get average rating over the last 30 days
    today = timezone2.now().date()
    dates = [today - timedelta(days=i) for i in range(29, -1, -1)]
    date_strs = [date.isoformat() for date in dates]
    rating_over_time = {
        date_str: {"total_rating": 0, "count": 0} for date_str in date_strs
    }

    for review in reviews:
        timestamp = datetime.fromisoformat(review["Timestamp"]).date().isoformat()
        if timestamp in rating_over_time:
            rating_over_time[timestamp]["total_rating"] += int(review["RatingStars"])
            rating_over_time[timestamp]["count"] += 1

    avg_ratings = []
    for date_str in date_strs:
        data_point = rating_over_time[date_str]
        if data_point["count"] > 0:
            avg_rating = data_point["total_rating"] / data_point["count"]
        else:
            avg_rating = None  # Use None to represent missing data
        avg_ratings.append(avg_rating)

    data = {"dates": date_strs, "avg_ratings": avg_ratings}

    return JsonResponse(data)


@login_required
def rating_distribution(request):
    if request.user.user_type != "service_provider":
        return JsonResponse({"error": "Unauthorized"}, status=403)

    services = service_repo.get_services_by_provider(request.user.id)
    service_ids = [service.id for service in services]

    reviews = home_repo.get_reviews_for_services(service_ids)

    # Calculate rating distribution
    rating_counts = {str(i): 0 for i in range(1, 6)}
    for review in reviews:
        rating = str(review["RatingStars"])
        rating_counts[rating] += 1

    data = {
        "ratings": list(rating_counts.keys()),
        "counts": list(rating_counts.values()),
    }

    return JsonResponse(data)


@login_required
def recent_reviews(request):
    if request.user.user_type != "service_provider":
        return JsonResponse({"error": "Unauthorized"}, status=403)

    services = service_repo.get_services_by_provider(request.user.id)
    service_ids = [service.id for service in services]

    reviews = home_repo.get_reviews_for_services(service_ids)

    # Sort reviews by timestamp descending
    reviews.sort(key=lambda x: x["Timestamp"], reverse=True)

    # Take the top 5 recent reviews
    recent_reviews = reviews[:5]

    # Prepare data
    data = {"reviews": recent_reviews}

    return JsonResponse(data)


@login_required
def response_rate(request):
    if request.user.user_type != "service_provider":
        return JsonResponse({"error": "Unauthorized"}, status=403)

    services = service_repo.get_services_by_provider(request.user.id)
    service_ids = [service.id for service in services]

    reviews = home_repo.get_reviews_for_services(service_ids)

    total_reviews = len(reviews)
    responded_reviews = sum(1 for review in reviews if review.get("ResponseText"))

    response_rate = (
        (responded_reviews / total_reviews) * 100 if total_reviews > 0 else 0
    )

    data = {
        "total_reviews": total_reviews,
        "responded_reviews": responded_reviews,
        "response_rate": round(response_rate, 2),
    }

    return JsonResponse(data)


@login_required
def review_word_cloud(request):
    if request.user.user_type != "service_provider":
        return JsonResponse({"error": "Unauthorized"}, status=403)

    services = service_repo.get_services_by_provider(request.user.id)
    service_ids = [service.id for service in services]

    reviews = home_repo.get_reviews_for_services(service_ids)

    # Combine all review texts
    text = " ".join(review["RatingMessage"] for review in reviews)

    # Simple text processing
    words = re.findall(r"\w+", text.lower())
    stopwords = {"the", "and", "is", "in", "it", "of", "to", "a", "i", "for", "this", "that", "with"}
    words = [word for word in words if word not in stopwords and len(word) > 2]

    # Count word frequencies
    word_counts = Counter(words)
    most_common = word_counts.most_common(50)

    # Prepare data
    data = [{"text": word, "size": count} for word, count in most_common]

    return JsonResponse({"words": data})


@login_required
def service_category_distribution(request):
    if request.user.user_type != "service_provider":
        return JsonResponse({"error": "Unauthorized"}, status=403)

    services = service_repo.get_services_by_provider(request.user.id)

    # Count services per category
    category_counts = {}
    for service in services:
        category = service.category
        category_counts[category] = category_counts.get(category, 0) + 1

    data = {
        "categories": list(category_counts.keys()),
        "counts": list(category_counts.values()),
    }

    return JsonResponse(data)


@login_required
def user_analytics(request):
    if request.user.user_type != "service_provider":
        return JsonResponse({"error": "Unauthorized"}, status=403)

    user_id = str(request.user.id)

    # Compute user's metrics
    user_metrics = home_repo.compute_user_metrics(user_id)

    data = {
        "user_metrics": user_metrics,
    }
    return JsonResponse(data)
