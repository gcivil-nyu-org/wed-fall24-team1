from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.models import CustomUser
from forum.models import Post, Comment, Notification
from home.repositories import HomeRepository
from services.models import ReviewDTO
from services.repositories import ReviewRepository
from .models import Flag


def is_admin(user):
    return user.is_superuser


@require_POST
@login_required
def create_flag(request):
    try:
        content_type = request.POST.get("content_type")
        object_id = request.POST.get("object_id")
        reason = request.POST.get("reason")
        explanation = request.POST.get("explanation", "")

        if content_type not in dict(Flag.CONTENT_TYPES):
            return JsonResponse({"error": "Invalid content type"}, status=400)

        # Get the flagged object based on content type
        if content_type == "FORUM POST":
            try:
                Post.objects.get(id=object_id)
            except Post.DoesNotExist:
                return JsonResponse({"error": "Post not found"}, status=404)

        elif content_type == "FORUM COMMENT":
            try:
                Comment.objects.get(id=object_id)
            except Comment.DoesNotExist:
                return JsonResponse({"error": "Comment not found"}, status=404)

        elif content_type == "REVIEW":
            # For NoSQL reviews, verify the review exists
            repo = ReviewRepository()
            flagged_object = repo.get_review(object_id)
            if not flagged_object:
                return JsonResponse({"error": "Review not found"}, status=404)
            # Get the review author's user ID from the review data

        # Check if user has already flagged this content
        if Flag.objects.filter(
            content_type=content_type, object_id=object_id, flagger=request.user
        ).exists():
            return JsonResponse(
                {"error": "You have already flagged this content"}, status=400
            )

        with transaction.atomic():
            # Create the flag with the string content type
            _ = Flag.objects.create(
                content_type=content_type,
                object_id=str(object_id),
                flagger=request.user,
                reason=reason,
                explanation=explanation,
            )

            # Notify admins (only if they haven't been notified about pending flags)
            admin_users = CustomUser.objects.filter(is_superuser=True)
            for admin in admin_users:
                # Check if admin already has an unread flag notification
                if not Notification.objects.filter(
                    recipient=admin, notification_type="flag_admin", is_read=False
                ).exists():
                    Notification.objects.create(
                        recipient=admin,
                        sender=request.user,
                        message="New flagged content requires review",
                        notification_type="flag_admin",
                    )

        return JsonResponse(
            {"success": True, "message": "Content has been flagged for review"}
        )

    except Exception as e:
        # Log the error for debugging
        print(f"Error in create_flag: {str(e)}")
        return JsonResponse(
            {"error": "An error occurred while processing your request"}, status=500
        )


@require_POST
@login_required
@user_passes_test(is_admin)
def review_flag(request, flag_id):
    """Handle admin review of flagged content"""
    flag = get_object_or_404(Flag, id=flag_id)
    action = request.POST.get("action")

    if action not in ["dismiss", "revoke"]:
        return JsonResponse({"error": "Invalid action"}, status=400)

    try:
        with transaction.atomic():
            flag.status = "DISMISSED" if action == "dismiss" else "REVOKED"
            flag.reviewed_by = request.user
            flag.reviewed_at = timezone.now()
            flag.save()

            if action == "revoke":
                flagged_object = flag.get_content_object()

                if isinstance(flagged_object, (Post, Comment)):
                    flagged_object.delete()
                elif isinstance(flagged_object, ReviewDTO):
                    home_repo = HomeRepository()
                    home_repo.delete_review(flagged_object.review_id)

            Notification.objects.create(
                recipient=flag.flagger,
                sender=request.user,
                message=f"Your flag has been reviewed and {flag.status.lower()}",
                notification_type="flag_reviewed",
            )

            content_author = getattr(flag.get_content_object(), "author", None)
            if content_author:
                Notification.objects.create(
                    recipient=content_author,
                    sender=request.user,
                    message=f"Your flagged content has been {flag.status.lower()}",
                    notification_type="flag_reviewed",
                )

        return JsonResponse({"success": True, "status": flag.status})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@login_required
def check_flag_status(request, content_type, object_id):
    """
    Check the flag status of a piece of content for the current user.
    Returns:
    - userHasFlagged: Whether the current user has flagged this content
    - hasPendingFlags: Whether there are any pending flags on this content
    This allows the frontend to show different UI states:
    - Clock icon for content the user has personally flagged
    - Flag icon for content they haven't flagged yet
    """
    try:
        # Check if the current user has flagged this content
        user_flag = Flag.objects.filter(
            content_type=content_type,
            object_id=object_id,
            flagger=request.user,
            status="PENDING",
        ).exists()

        # Check if there are any pending flags (used for admin purposes)
        total_pending_flags = Flag.objects.filter(
            content_type=content_type, object_id=object_id, status="PENDING"
        ).count()

        return JsonResponse(
            {
                "userHasFlagged": user_flag,
                "hasPendingFlags": total_pending_flags > 0,
                "pendingFlagsCount": total_pending_flags,  # This might be useful for admins
            }
        )
    except Exception as e:
        # Log the error for debugging
        print(f"Error checking flag status: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)
