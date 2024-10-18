from django.shortcuts import render
from django.core.paginator import Paginator
import json
from .repositories import (
    HomeRepository,
)


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
    page_number = request.GET.get(
        "page", 1
    )  # Get the page number from the request (default to 1)
    page_obj = paginator.get_page(page_number)

    # Calculate the base index for the current page
    base_index = paginator.per_page * (page_obj.number - 1)

    # Serialize current page's items to JSON for the map
    serialized_items = [
        {
            "Name": item.get("Name", "No Name"),
            "Address": item.get("Address", "N/A"),
            "Lat": float(item.get("Lat")) if item.get("Lat") else None,
            "Log": float(item.get("Log")) if item.get("Log") else None,
            "Ratings": (
                str(item.get("Ratings")) if item.get("Ratings") else "No ratings"
            ),
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
