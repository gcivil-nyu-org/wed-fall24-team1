# public_service_finder/views.py
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render
from public_service_finder.utils.enums.service_status import ServiceStatus
from services.repositories import ServiceRepository
from django.contrib import messages


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
@user_passes_test(lambda user: user.is_superuser)
def admin_only_view_new_listings(request):
    service_repo = ServiceRepository()
    pending_services = service_repo.get_pending_approval_services()
    return render(request, "admin_only.html", {"pending_services": pending_services})


@login_required
@user_passes_test(lambda user: user.is_superuser)
def admin_update_listing(request, service_id):
    if request.method == "POST":
        new_status = request.POST.get("status")

        # Only allow "approve" or "reject" as valid status values
        if new_status not in ["approve", "reject"]:
            messages.error(request, "Invalid status value.")
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
            messages.success(
                request,
                f"Service ID {service_id} has been successfully updated to '{new_status}'.",
            )
        except Exception as e:
            messages.error(
                request, f"An error occurred while updating the service: {str(e)}"
            )

        # Redirect to the listings page to see updated statuses
        return redirect("admin_only_view_new_listings")

    # If the request is not POST, redirect back to the listings page
    return redirect("admin_only_view_new_listings")
