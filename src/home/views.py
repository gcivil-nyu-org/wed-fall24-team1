from django.shortcuts import render
from django.core.paginator import Paginator
import json
from .repositories import (
    HomeRepository,
)

from django.http import JsonResponse
import uuid  # For generating unique Review IDs
from django.views.decorators.http import require_POST

@require_POST
def submit_review(request):
    try:
        data = json.loads(request.body)
        service_id = data.get('service_id')
        rating = data.get('rating')
        message = data.get('message')
        user = request.user

        if not service_id or not rating or not message:
            return JsonResponse({'error': 'Invalid data.'}, status=400)

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

        return JsonResponse({
            'success': True,
            'review_id': review_id,
            'service_id': service_id,
            'user_id': user.id,
            'rating': rating,
            'message': message,
            'username': user.username,
        }, status=200)

    except Exception as e:
        print(f"Error in submit_review: {e}")
        return JsonResponse({'error': 'An error occurred while submitting the review.'}, status=500)



def home_view(request):
    # Initialize the repository
    repo = HomeRepository()

    search_query = request.GET.get("search", "").strip()

    radius = request.GET.get("radius")
    ulat, ulon = request.GET.get("user_lat"), request.GET.get("user_lon")

    # Get search query from request
    service_type_dropdown = request.GET.get("type", "")

    # Fetch and process items using the repository
    items = repo.fetch_items_with_filter(
        search_query, service_type_dropdown, radius, ulat, ulon
    )
    processed_items = HomeRepository.process_items(items)

    # Paginate the items (10 items per page)
    paginator = Paginator(processed_items, 10)  # Show 10 items per page
    page_number = request.GET.get("page", 1)  # Get the page number from the request
    page_obj = paginator.get_page(page_number)

    # Calculate the base index for the current page
    base_index = paginator.per_page * (page_obj.number - 1)

    # Serialize current page's items to JSON for the map
    serialized_items = [
        {
            "Id": item.get("Id"),
            "Name": item.get("Name", "No Name"),
            "Address": item.get("Address", "N/A"),
            "Lat": float(item.get("Lat")) if item.get("Lat") else None,
            "Log": float(item.get("Log")) if item.get("Log") else None,
            "Ratings": (
                "N/A" if item.get("Ratings") in [0, "0", None] else str(item.get("Ratings"))
            ),
            "RatingCount": str(item.get("rating_count", 0)),  # Add the rating_count field
            "Category": str(item.get("Category")),
            "MapLink": item.get("MapLink"),
        }
        for item in page_obj
    ]

    return render(
        request,
        "home.html",
        {
            "search_query": search_query,
            "service_type_dropdown": service_type_dropdown,
            "radius": radius if radius else "",
            "page_obj": page_obj,
            "base_index": base_index,
            "serialized_items": json.dumps(serialized_items),  # Pass serialized data
        },
    )
