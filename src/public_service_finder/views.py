# public_service_finder/views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.shortcuts import render

from moderation.models import Flag
from public_service_finder.utils.enums.service_status import ServiceStatus
from services.repositories import ServiceRepository


def root_redirect_view(request):
    if request.user.is_authenticated:
        if request.user.user_type == "service_provider":
            return redirect("services:list")
        else:
            return redirect("home")
    else:
        # If the user is not authenticated, redirect to home page
        return redirect("home")  # Redirect to user login if not logged in


@login_required
def admin_only_view_new_listings(request):
    if not request.user.is_superuser:
        return render(request, "403.html", status=403)

    service_repo = ServiceRepository()
    pending_services = service_repo.get_pending_approval_services()

    # First, get all pending flags
    flags = Flag.objects.filter(status="PENDING").select_related("flagger")

    # Create a dictionary to group flags by content
    grouped_flags = {}
    for flag in flags:
        content_key = f"{flag.content_type}:{flag.object_id}"
        if content_key not in grouped_flags:
            grouped_flags[content_key] = {
                "content_type": flag.content_type,
                "object_id": flag.object_id,
                "content_preview": flag.content_preview,
                "content_title": flag.content_title,
                "content_rating": flag.content_rating,
                "content_author": flag.content_author,
                "created_at": flag.created_at,  # First flag date
                "flags": [],
                "flag_count": 0,
                "first_flag_id": flag.id,
            }

        # Add this flag's information
        grouped_flags[content_key]["flags"].append(
            {
                "flagger": flag.flagger.username,
                "reason": flag.reason,
                "explanation": flag.explanation,
                "created_at": flag.created_at,
                "flag_id": flag.id,
            }
        )
        grouped_flags[content_key]["flag_count"] += 1

    # Convert the dictionary to a list and sort by number of flags (most flags first)
    grouped_flags_list = sorted(
        grouped_flags.values(),
        key=lambda x: (x["flag_count"], x["created_at"]),
        reverse=True,
    )

    return render(
        request,
        "admin_only.html",
        {
            "pending_services": pending_services,
            "flags": grouped_flags_list,
        },
    )


@login_required
def admin_update_listing(request, service_id):
    if not request.user.is_superuser:
        return render(request, "403.html", status=403)

    if request.method == "POST":
        new_status = request.POST.get("status")

        # Only allow "approve" or "reject" as valid status values
        if new_status not in ["approve", "reject"]:
            print(request, "Invalid status value.")
            return redirect("admin_only_view_new_listings")

        service_repo = ServiceRepository()
        try:
            service_repo.update_service_status(
                service_id,
                (
                    ServiceStatus.APPROVED.value
                    if new_status == "approve"
                    else ServiceStatus.REJECTED.value
                ),
            )
        except Exception as e:
            print(f"Exception occurred: {e}")

        # Redirect to the listings page to see updated statuses
        return redirect("admin_only_view_new_listings")

    # If the request is not POST, redirect back to the listings page
    return redirect("admin_only_view_new_listings")
