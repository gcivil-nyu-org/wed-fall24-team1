from django.shortcuts import render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import json
from .repositories import HomeRepository
from django.http import JsonResponse
import uuid  # For generating unique Review IDs
from django.views.decorators.http import require_POST
from decimal import Decimal

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
    try:
        data = json.loads(request.body)
        service_id = data.get("service_id")
        rating = data.get("rating")
        message = data.get("message")
        user = request.user

        if not service_id or not rating or not message:
            return JsonResponse({"error": "Invalid data."}, status=400)

        repo = HomeRepository()

        # Generate a unique Review ID
        review_id = str(uuid.uuid4())

        # Add the review to the reviews table
        repo.add_review(
            review_id=review_id,
            service_id=service_id,
            user_id=str(user.id),  # Assuming user ID is a string
            rating_stars=rating,
            rating_message=message,
            username=user.username,  # To display in frontend
        )

        # Update the service's rating and rating count
        repo.update_service_rating(service_id=service_id, new_rating=rating)

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

    except Exception as e:
        print(f"Error in submit_review: {e}")
        return JsonResponse(
            {"error": "An error occurred while submitting the review."}, status=500
        )


def home_view(request):
    repo = HomeRepository()

    # Get search filters from the request
    search_query = request.GET.get("search", "").strip()
    radius = request.GET.get("radius", "")
    ulat, ulon = request.GET.get("user_lat"), request.GET.get("user_lon")
    service_type = request.GET.get("type", "")

    # Fetch items using the repository with filters
    items = repo.fetch_items_with_filter(search_query, service_type, radius, ulat, ulon)
    processed_items = HomeRepository.process_items(items)

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
                "N/A"
                if item.get("Ratings") in [0, "0", None]
                else str(item.get("Ratings"))
            ),
            "RatingCount": str(item.get("rating_count", 0)),
            "Category": item.get("Category", "N/A"),
            "MapLink": item.get("MapLink"),
            "Description": convert_decimals(item.get("Description", {})),  # Convert Decimals here
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
        },
    )


def get_reviews(request, service_id):
    try:
        page = int(request.GET.get("page", 1))  # Default to page 1
        repo = HomeRepository()

        # Fetch all reviews for the given service ID
        reviews = repo.fetch_reviews_for_service(service_id)

        # Paginate the reviews (5 reviews per page)
        paginator = Paginator(reviews, 5)  # 5 reviews per page
        page_obj = paginator.get_page(page)

        # Prepare the response
        response_data = {
            "reviews": list(page_obj.object_list),
            "has_next": page_obj.has_next(),
            "has_previous": page_obj.has_previous(),
            "current_page": page_obj.number,
        }

        return JsonResponse(response_data, status=200)

    except Exception as e:
        print(f"Error fetching reviews: {e}")
        return JsonResponse({"error": "Failed to fetch reviews."}, status=500)
