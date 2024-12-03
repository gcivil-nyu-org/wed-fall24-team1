# public_service_finder/views.py
from dataclasses import asdict
from typing import Dict
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.shortcuts import render

from public_service_finder.utils.enums.service_status import ServiceStatus
from services.models import ServiceDTO
from services.repositories import ServiceRepository
from django.contrib.auth.decorators import user_passes_test


def root_redirect_view(request):
    if request.user.is_authenticated:
        if request.user.user_type == "service_provider":
            return redirect("services:list")
        else:
            return redirect("home")
    else:
        # If the user is not authenticated, redirect to home page
        return redirect("home")  # Redirect to user login if not logged in




def dict_to_dto(new_updates_requested_dict) -> ServiceDTO:
    return ServiceDTO(
                    id=new_updates_requested_dict.get("Id"),
                    name=new_updates_requested_dict.get("Name"),
                    address=new_updates_requested_dict.get("Address"),
                    ratings=new_updates_requested_dict.get("Ratings"),
                    description=new_updates_requested_dict.get("Description"),
                    category=new_updates_requested_dict.get("Category"),
                    provider_id=new_updates_requested_dict.get("ProviderId"),
                    service_status=new_updates_requested_dict.get("ServiceStatus"),
                    service_created_timestamp=new_updates_requested_dict.get("CreatedTimestamp"),
                    service_approved_timestamp=new_updates_requested_dict.get("ApprovedTimestamp"),
                    is_active=new_updates_requested_dict.get("IsActive"),
                    pending_update=new_updates_requested_dict.get("pending_update"),
                    latitude=new_updates_requested_dict.get("Latitude"),
                    longitude=new_updates_requested_dict.get("Longitude")
        )

@login_required
@user_passes_test(lambda user: user.is_superuser)
def admin_only_view_new_listings(request):
    service_repo = ServiceRepository()
    pending_services = service_repo.get_pending_approval_or_editRequested_services()
    new_value_dict: Dict[str, Dict[str, Any]] = {}
    
    services_with_changes = []
        # Iterate through each pending service
    for service in pending_services:
        if service.pending_update:
         
            new_updates_requested_dict = (service.pending_update)
         
            
            old_service_dto = service 
            
            new_updates_requested_dto = dict_to_dto(new_updates_requested_dict)
            changes = {}
            
            # compare new_updates_requested_dto with old_service_dto and populate the changes
                 # Compare fields of old_service_dto and new_updates_requested_dto
            old_service_dict = asdict(old_service_dto)
            new_service_dict = asdict(new_updates_requested_dto)

            for key in new_service_dict:
                if key in old_service_dict and old_service_dict[key] != new_service_dict[key]:
                    changes[key] = {
                    "old_value": old_service_dict[key],
                    "new_value": new_service_dict[key]
                }
            

           
                    
            if changes:
                new_value_dict[service.id] = changes
        
            changes.pop('pending_update', None)
            changes.pop('latitude', None)
            changes.pop('longitude', None)
            
            services_with_changes.append({
                "service": service,
                "changes": changes
            })
        else:
            services_with_changes.append({
                "service": service,
                "changes": {}
            })
            

    # Pass the data to the template
    context = {
        "services_with_changes": services_with_changes
    }

    
    return render(request, "admin_only.html", context)


@login_required
@user_passes_test(lambda user: user.is_superuser)
def admin_update_listing(request, service_id):
    if request.method == "POST":
        service_repo = ServiceRepository()
        new_status = request.POST.get("status")
        service_id_str = str(service_id)
        
        serviceDto  = service_repo.get_service(service_id_str ) 
        
        if serviceDto is None: 
            return Exception("Service not found")
        
        
        serviceStatusParam = ""
        if serviceDto.pending_update:
            if new_status == "approve":
                serviceStatusParam = ServiceStatus.APPROVED.value
                updatedServiceDTO  = dict_to_dto(serviceDto.pending_update)
                updatedServiceDTO.latitude= serviceDto.latitude 
                updatedServiceDTO.longitude= serviceDto.longitude 
                service_repo.update_service(updatedServiceDTO)
                
                
            elif new_status == "reject":
                serviceStatusParam = ServiceStatus.EDIT_REQUEST_REJECTED.value
                service_repo.update_service_status(service_id_str,serviceStatusParam)
        else:
            if new_status == "approve":
                serviceStatusParam = ServiceStatus.APPROVED.value
            elif new_status == "reject":
                serviceStatusParam = ServiceStatus.REJECTED.value
            else:
                print(request, "Invalid status value.")
                return redirect("admin_only_view_new_listings")
        

        
        
        
        
        try:
            service_repo.update_service_status(
                service_id,
                (
                serviceStatusParam
                ),
            )
        except Exception as e:
            print(f"Exception occurred: {e}")

        # Redirect to the listings page to see updated statuses
        return redirect("admin_only_view_new_listings")

    # If the request is not POST, redirect back to the listings page
    return redirect("admin_only_view_new_listings")
