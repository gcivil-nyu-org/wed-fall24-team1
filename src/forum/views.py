from django.db.models import Q
from django.http import HttpResponseForbidden, JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Category, Post, Comment
from .forms import PostForm, CommentForm
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, get_object_or_404, redirect
from django.http import Http404

# Create your views here.


def category_list(request):
    categories = Category.objects.all().order_by("name")
    return render(request, "category_list.html", {"categories": categories})


def category_detail(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    search_query = request.GET.get("search", "")

    posts = Post.objects.filter(category=category)

    if search_query:
        posts = posts.filter(
            Q(title__icontains=search_query)
            | Q(content__icontains=search_query)
            | Q(author__username__icontains=search_query)
        )

    posts = posts.order_by("-created_at")

    # Pagination for posts
    paginator = Paginator(posts, 10)  # Show 10 posts per page
    page = request.GET.get("page")
    try:
        posts = paginator.page(page)
    except PageNotAnInteger:
        posts = paginator.page(1)
    except EmptyPage:
        posts = paginator.page(paginator.num_pages)

    return render(
        request,
        "category_detail.html",
        {"category": category, "posts": posts, "search_query": search_query},
    )


def post_detail(request, post_id):
    try:
        post = get_object_or_404(Post, id=post_id)
    except Http404:
        # First try to get any post with this ID to find its category
        try:
            category = Post.objects.get(id=post_id).category
        except Post.DoesNotExist:
            # If no post exists with this ID, redirect to forum home
            return redirect("forum:category_list")
        return redirect("forum:category_detail", category_id=category.id)

    comments_list = post.comments.all().order_by("-created_at")

    # Pagination for comments
    paginator = Paginator(comments_list, 5)  # Show 5 comments per page
    page = request.GET.get("page")
    try:
        comments = paginator.page(page)
    except PageNotAnInteger:
        comments = paginator.page(1)
    except EmptyPage:
        comments = paginator.page(paginator.num_pages)

    if request.method == "POST":
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
            return redirect("forum:post_detail", post_id=post.id)
    else:
        comment_form = CommentForm()

    return render(
        request,
        "post_detail.html",
        {
            "post": post,
            "comments": comments,
            "comment_form": comment_form,
        },
    )


@login_required
def edit_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    if post.author != request.user:
        return HttpResponseForbidden("You don't have permission to edit this post.")

    if request.method == "GET":
        return JsonResponse({"title": post.title, "content": post.content})

    if request.method == "POST":
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            form.save()
            return redirect("forum:post_detail", post_id=post.id)

    return HttpResponseForbidden("Invalid request method.")


@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    if post.author != request.user:
        return HttpResponseForbidden("You don't have permission to delete this post.")

    if request.method == "POST":
        category_id = post.category.id
        post.delete()
        return redirect("forum:category_detail", category_id=category_id)

    return HttpResponseForbidden("Invalid request method.")


@login_required
def edit_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)

    if comment.author != request.user:
        return HttpResponseForbidden("You don't have permission to edit this comment.")

    if request.method == "GET":
        return JsonResponse({"content": comment.content})

    if request.method == "POST":
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            return redirect("forum:post_detail", post_id=comment.post.id)

    return HttpResponseForbidden("Invalid request method.")


@login_required
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)

    if comment.author != request.user:
        return HttpResponseForbidden(
            "You don't have permission to delete this comment."
        )

    if request.method == "POST":
        post_id = comment.post.id
        comment.delete()
        return redirect("forum:post_detail", post_id=post_id)

    return HttpResponseForbidden("Invalid request method.")


@login_required
def create_post(request, category_id):
    category = get_object_or_404(Category, id=category_id)

    if request.method == "POST":
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.category = category
            post.save()
            return redirect("forum:category_detail", category_id=category.id)
    else:
        form = PostForm()

    return render(request, "create_post.html", {"form": form, "category": category})
