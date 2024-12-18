import decimal
import json
import uuid
from decimal import Decimal, Inexact, Rounded

from better_profanity import profanity
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST
from django.views.decorators.http import require_http_methods

from accounts.models import CustomUser
from forum.models import Notification
from services.repositories import ServiceRepository
from .repositories import HomeRepository

# TODO These constants are maintained in the JS frontend and here, we'll have to unify them
DEFAULT_LAT, DEFAULT_LON = 40.7128, -74.0060
DEFAULT_RADIUS = 5.0

decimal.getcontext().traps[decimal.Inexact] = False
decimal.getcontext().traps[decimal.Rounded] = False
profanity.load_censor_words()


def convert_decimals(obj):
    if isinstance(obj, list):
        return [convert_decimals(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: convert_decimals(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
        return str(obj)
    else:
        return obj


@require_POST
def submit_review(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Authentication required."}, status=401)

    try:
        data = json.loads(request.body)
        service_id = data.get("service_id")
        rating = data.get("rating")
        message = data.get("message")
        message = profanity.censor(message)
        user = request.user

        if not service_id or not rating or not message:
            return JsonResponse({"error": "Invalid data."}, status=400)

        repo = HomeRepository()
        service_repo = ServiceRepository()

        # Get the service to find its provider
        service = service_repo.get_service(service_id)
        if service:
            try:
                # Get the service provider user
                provider = CustomUser.objects.get(id=service.provider_id)

                # Generate a unique Review ID
                review_id = str(uuid.uuid4())

                # Add the review to the reviews table
                repo.add_review(
                    review_id=review_id,
                    service_id=service_id,
                    user_id=str(user.id),
                    rating_stars=rating,
                    rating_message=message,
                    username=user.username,
                )

                # Update the service's rating and rating count
                repo.update_service_rating(service_id=service_id, new_rating=rating)

                # Create notification for service provider
                Notification.objects.create(
                    recipient=provider,
                    sender=user,
                    post=None,
                    comment=None,
                    message=f"{user.username} left a {rating}-star review on your service: {service.name}",
                    notification_type="review",
                )

                return JsonResponse(
                    {
                        "success": True,
                        "review_id": review_id,
                        "service_id": service_id,
                        "user_id": user.id,
                        "rating": rating,
                        "message": message,
                        "username": user.username,
                    },
                    status=200,
                )
            except CustomUser.DoesNotExist:
                # Handle case where provider user doesn't exist
                return JsonResponse(
                    {"error": "Service provider not found."}, status=404
                )
        else:
            return JsonResponse({"error": "Service not found."}, status=404)

    except (Inexact, Rounded) as decimal_error:
        print(f"Decimal error in submit_review: {decimal_error}")
        return JsonResponse(
            {
                "error": "A decimal precision error occurred while submitting the review."
            },
            status=500,
        )

    except Exception as e:
        print(f"Error in submit_review: {e}")
        return JsonResponse(
            {"error": "An error occurred while submitting the review."}, status=500
        )


def home_view(request):
    if request.user.is_authenticated and request.user.user_type == "service_provider":
        return redirect("services:list")

    repo = HomeRepository()
    user = request.user if request.user.is_authenticated else None

    # Get search filters from the request
    search_query = request.GET.get("search", "").strip()
    radius = request.GET.get("radius", DEFAULT_RADIUS)
    ulat = request.GET.get("user_lat", DEFAULT_LAT)
    ulon = request.GET.get("user_lon", DEFAULT_LON)
    service_type = request.GET.get("type", "")
    sort_by = request.GET.get("sort", "distance")
    user_bookmarks = []

    if user:
        user_bookmarks_services = repo.get_user_bookmarks(str(user.id))
        user_bookmarks = [service["Id"] for service in user_bookmarks_services]

    # Validate the user location (latitude and longitude)
    if ulat and ulon:
        try:
            ulat = float(ulat)
            ulon = float(ulon)
        except ValueError:
            ulat, ulon = None, None  # Reset invalid lat/lon values

    # Fetch items using the repository with filters
    items = repo.fetch_items_with_filter(search_query, service_type, radius, ulat, ulon)
    processed_items = HomeRepository.process_items(items)

    # Sort the items before pagination

    if sort_by == "rating":

        def rating_sort_key(x):
            rating = x.get("Ratings")
            try:
                return (0, -float(rating))
            except (TypeError, ValueError):
                return (1, 0)

        processed_items.sort(key=rating_sort_key)
    else:
        processed_items.sort(key=lambda x: float(x.get("Distance", float("inf"))))

    # Paginate the results, showing 10 items per page
    paginator = Paginator(processed_items, 10)
    page_number = request.GET.get("page", 1)

    try:
        page_obj = paginator.get_page(page_number)
    except (PageNotAnInteger, EmptyPage):
        page_obj = paginator.get_page(1)

    base_index = (page_obj.number - 1) * paginator.per_page

    # Prepare data to be serialized for use in JavaScript (e.g., maps)
    serialized_items = [
        {
            "Id": item.get("Id"),
            "Name": item.get("Name", "No Name"),
            "Address": item.get("Address", "N/A"),
            "Lat": float(item.get("Lat")) if item.get("Lat") else None,
            "Log": float(item.get("Log")) if item.get("Log") else None,
            "Ratings": (
                str(item.get("Ratings"))
                if item.get("Ratings") not in [None, "N/A"]
                else "N/A"
            ),
            "RatingCount": str(item.get("rating_count", 0)),
            "Category": item.get("Category", "N/A"),
            "MapLink": item.get("MapLink"),
            "Distance": item.get("Distance", "N/A"),
            "Description": convert_decimals(item.get("Description", {})),
            "IsBookmarked": item.get("Id") in user_bookmarks,
            "IsActive": item.get("IsActive", True),
            "Announcement": item.get("Announcement", ""),
            "ImageURL": item.get("ImageURL", ""),  # Added this line
        }
        for item in page_obj
    ]

    # Render the home page with context data
    return render(
        request,
        "home.html",
        {
            "search_query": search_query,
            "service_type_dropdown": service_type,
            "radius": radius if radius else "",
            "page_obj": page_obj,
            "base_index": base_index,
            "serialized_items": json.dumps(serialized_items),
            "user_lat": ulat if ulat else "",
            "user_lon": ulon if ulon else "",
            "sort_by": sort_by,
        },
    )


def get_reviews(request, service_id):
    try:
        page = int(request.GET.get("page", 1))  # Default to page 1
        repo = HomeRepository()

        # Fetch all reviews for the given service ID
        reviews = repo.fetch_reviews_for_service(service_id)
        user = request.user

        # Paginate the reviews (5 reviews per page)
        paginator = Paginator(reviews, 5)  # 5 reviews per page
        page_obj = paginator.get_page(page)

        # Prepare the response
        response_data = {
            "reviews": list(page_obj.object_list),
            "has_next": page_obj.has_next(),
            "has_previous": page_obj.has_previous(),
            "current_page": page_obj.number,
            "username": user.username,
        }

        return JsonResponse(response_data, status=200)

    except Exception as e:
        print(f"Error fetching reviews: {e}")
        return JsonResponse({"error": "Failed to fetch reviews."}, status=500)


@require_POST
def toggle_bookmark(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Authentication required."}, status=401)

    try:
        data = json.loads(request.body)
        service_id = data.get("service_id")
        action = data.get("action")  # 'add' or 'remove'
        user = request.user

        if not service_id or not action:
            return JsonResponse({"error": "Invalid data."}, status=400)

        user_id = str(user.id)
        repo = HomeRepository()

        if action == "add":
            if not repo.is_bookmarked(user_id, service_id):
                bookmark_id = str(uuid.uuid4())
                repo.add_bookmark(bookmark_id, user_id, service_id)
                return JsonResponse({"success": True, "action": "added"})
            else:
                return JsonResponse({"success": True, "action": "already_bookmarked"})
        elif action == "remove":
            repo.remove_bookmark(user_id, service_id)
            return JsonResponse({"success": True, "action": "removed"})
        else:
            return JsonResponse({"error": "Invalid action."}, status=400)
    except Exception as e:
        print(f"Error in toggle_bookmark: {e}")
        return JsonResponse(
            {"error": "An error occurred while toggling the bookmark."}, status=500
        )


@require_http_methods(["DELETE"])
def delete_review(request, review_id):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Authentication required."}, status=401)

    try:
        repo = HomeRepository()
        data = json.loads(request.body)
        if data.get("username") != request.user.username:
            return JsonResponse(
                {"error": "You are not authorized to edit this review."}, status=403
            )
        # Delete the review
        repo.delete_review(review_id)
        return JsonResponse(
            {"success": True, "message": "Review deleted successfully."}, status=200
        )

    except Exception as e:
        print(f"Error deleting review: {e}")
        return JsonResponse({"error": "Failed to delete review."}, status=500)


@require_http_methods(["PUT"])
def edit_review(request, review_id):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Authentication required."}, status=401)

    try:
        data = json.loads(request.body)
        new_rating = data.get("rating")
        new_message = data.get("message")
        new_message = profanity.censor(new_message)
        if data.get("username") != request.user.username:
            return JsonResponse(
                {"error": "You are not authorized to edit this review."}, status=403
            )
        if not new_rating or not new_message:
            return JsonResponse(
                {"error": "Rating and message are required."}, status=400
            )

        repo = HomeRepository()

        result = repo.edit_review(
            review_id=review_id, new_rating=new_rating, new_message=new_message
        )

        # Check if there was an error in the repository response
        if "error" in result:
            return JsonResponse(result, status=404)

        return JsonResponse(result, status=200)

    except Exception as e:
        print(f"Error editing review: {e}")
        return JsonResponse({"error": "Failed to edit review."}, status=500)
