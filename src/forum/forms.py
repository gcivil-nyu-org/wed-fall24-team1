from django import forms
from .models import Post, Comment
from better_profanity import profanity


class ProfanityFilteredFormMixin:
    def clean(self):
        cleaned_data = super().clean()
        profanity.load_censor_words()

        # Filter profanity from all text fields
        for field_name, value in cleaned_data.items():
            if isinstance(value, str):
                cleaned_data[field_name] = profanity.censor(value)

        return cleaned_data


class PostForm(ProfanityFilteredFormMixin, forms.ModelForm):
    class Meta:
        model = Post
        fields = ["title", "content"]
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "w-full p-2 rounded bg-gray-700 text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 h-12 border border-gray-600"
                }
            ),
            "content": forms.Textarea(
                attrs={
                    "rows": 5,
                    "class": "w-full p-2 rounded bg-gray-700 text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 border border-gray-600"
                }),
        }

    def clean(self):
        cleaned_data = super().clean()
        # Additional specific filtering for post title if needed
        if "title" in cleaned_data:
            profanity.load_censor_words()
            cleaned_data["title"] = profanity.censor(cleaned_data["title"])
        return cleaned_data


class CommentForm(ProfanityFilteredFormMixin, forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["content"]
        widgets = {
            "content": forms.Textarea(
                attrs={
                    "rows": 3,
                    "class": "w-full p-2 rounded bg-gray-700 text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 border border-gray-600",
                }),
        }
