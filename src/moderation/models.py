from django.contrib.contenttypes.models import ContentType
from django.db import models

from accounts.models import CustomUser
from forum.models import Post, Comment
from services.models import ReviewDTO
from services.repositories import ReviewRepository


class Flag(models.Model):
    CONTENT_TYPES = [
        ('FORUM POST', 'Post'),
        ('FORUM COMMENT', 'Comment'),
        ('REVIEW', 'Review')
    ]    # Standard flag reasons that cover most common scenarios

    FLAG_REASONS = [
        ('SPAM', 'Spam or advertising'),
        ('OFFENSIVE', 'Offensive or inappropriate content'),
        ('HARASSMENT', 'Harassment or hate speech'),
        ('MISINFORMATION', 'False or misleading information'),
        ('OTHER', 'Other reason')
    ]

    # Flag status choices to track moderation state
    FLAG_STATUS = [
        ('PENDING', 'Pending Review'),
        ('DISMISSED', 'Dismissed'),
        ('REVOKED', 'Content Revoked')
    ]

    # Content type and object id for generic relation
    content_type = models.CharField(
        max_length=20,
        choices=CONTENT_TYPES,
        help_text="The type of content being flagged"
    )
    object_id = models.CharField(
        max_length=255,  # Using CharField to accommodate UUID fields
        help_text="The ID of the flagged content"
    )

    # Flag details
    flagger = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='flags_created',
        help_text="User who created this flag"
    )
    reason = models.CharField(
        max_length=20,
        choices=FLAG_REASONS,
        help_text="Primary reason for flagging"
    )
    explanation = models.CharField(
        max_length=256,
        blank=True,
        help_text="Additional details about why this content was flagged"
    )
    status = models.CharField(
        max_length=20,
        choices=FLAG_STATUS,
        default='PENDING',
        help_text="Current status of the flag"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When an admin reviewed this flag"
    )
    reviewed_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='flags_reviewed',
        help_text="Admin who reviewed this flag"
    )

    content_title = models.CharField(
        max_length=255,
        blank=True,
        help_text="Title of the content (if applicable, like for posts)"
    )
    content_preview = models.TextField(
        help_text="Preview/snippet of the flagged content"
    )
    content_rating = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        null=True,
        blank=True,
        help_text="Rating value for reviews"
    )
    content_author = models.CharField(
        max_length=255,
        help_text="Username of the content author"
    )

    def get_content_object(self):
        try:
            if self.content_type == 'FORUM POST':
                return Post.objects.get(id=self.object_id)

            elif self.content_type == 'FORUM COMMENT':
                return Comment.objects.get(id=self.object_id)

            elif self.content_type == 'REVIEW':
                # Reviews are stored in NoSQL, so we use the repository
                repo = ReviewRepository()
                return repo.get_review(self.object_id)

            return None

        except (Post.DoesNotExist, Comment.DoesNotExist, Exception) as e:
            # Log the error if needed
            print(f"Error fetching content object: {str(e)}")
            return None

    def save(self, *args, **kwargs):
        # Ensure object_id is a string
        if self.object_id:
            self.object_id = str(self.object_id)

        # Populate content preview fields before saving
        if not self.content_preview:  # Only populate if not already set
            content_object = self.get_content_object()
            if content_object:
                if isinstance(content_object, Post):
                    self.content_title = content_object.title
                    self.content_preview = content_object.content
                    self.content_author = content_object.author.username
                elif isinstance(content_object, Comment):
                    self.content_preview = content_object.content
                    self.content_author = content_object.author.username
                elif isinstance(content_object, ReviewDTO):
                    self.content_rating = content_object.rating_stars
                    self.content_preview = content_object.rating_message
                    self.content_author = content_object.username

        super().clean()
        super().save(*args, **kwargs)

    def clean(self):
        """
        Ensure the object_id is stored as a string regardless of input type
        """
        if self.object_id:
            self.object_id = str(self.object_id)
        super().clean()

    class Meta:
        # Ensure a user can only flag a specific piece of content once
        unique_together = ['content_type', 'object_id', 'flagger']
        # Order flags by creation date, newest first
        ordering = ['-created_at']

    def __str__(self):
        return f"Flag by {self.flagger.username} on {self.content_type} ({self.status})"