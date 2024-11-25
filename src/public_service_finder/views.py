# public_service_finder/views.py
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render
from public_service_finder.utils.enums.service_status import ServiceStatus
from services.repositories import ServiceRepository


def root_redirect_view(request):
    if request.user.is_authenticated:
        return (
            redirect("services:list")
            if request.user.user_type == "service_provider"
            else redirect("home")
        )
    else:
        return redirect("user_login")  # Redirect to user login if not logged in


@login_required
def admin_only_view_new_listings(request):
    if not request.user.is_superuser:
        return render(request, "403.html", status=403)
    service_repo = ServiceRepository()
    pending_services = service_repo.get_pending_approval_services()
    return render(request, "admin_only.html", {"pending_services": pending_services})


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
