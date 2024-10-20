from django.shortcuts import render, redirect, get_object_or_404
from profileapp.forms.service_provider_form import ServiceProviderForm
from profileapp.forms.service_seeker_form import ServiceSeekerForm
from profileapp.models.service_seeker_model import ServiceSeeker

def profile_view(request):
    user = request.user

    if user.user_type == "service_provider":
        service_provider = get_object_or_404(service_provider, user=user)

        # If it's a POST request, we're updating the profile
        if request.method == 'POST':
            form = ServiceProviderForm(request.POST, instance=service_provider)
            if form.is_valid():
                form.save()
                return redirect('profile_view')  # Redirect to avoid resubmission
        else:
            form = ServiceProviderForm(instance=service_provider)

        return render(request, 'profile_service_provider.html', {
            'profile': service_provider,
            'form': form,  # Pass the form to the template
        })

    elif user.user_type == "user":
        service_seeker = get_object_or_404(ServiceSeeker, user=user)

        # If it's a POST request, we're updating the profile
        if request.method == 'POST':
            form = ServiceSeekerForm(request.POST, instance=service_seeker)
            if form.is_valid():
                form.save()
                return redirect('profile_view')
        else:
            form = ServiceSeekerForm(instance=service_seeker)

        return render(request, 'profile_service_seeker.html', {
            'profile': service_seeker,
            'form': form,  # Pass the form to the template
        })
