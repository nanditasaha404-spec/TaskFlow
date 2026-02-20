from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.db import models
from .models import Task
from .forms import RegisterForm, TaskForm


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome, {user.username}!')
            return redirect('dashboard')
    else:
        form = RegisterForm()
    return render(request, 'tasks/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    for field in form.fields.values():
        field.widget.attrs['class'] = 'form-control'
    return render(request, 'tasks/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('login')


@login_required
def dashboard(request):
    filter_status = request.GET.get('status', 'all')
    filter_priority = request.GET.get('priority', 'all')
    search = request.GET.get('search', '')
    sort = request.GET.get('sort', 'newest')

    tasks = Task.objects.filter(user=request.user)

    if search:
        tasks = tasks.filter(title__icontains=search)

    if filter_status == 'active':
        tasks = tasks.filter(completed=False)
    elif filter_status == 'completed':
        tasks = tasks.filter(completed=True)

    if filter_priority != 'all':
        tasks = tasks.filter(priority=filter_priority)

    if sort == 'newest':
        tasks = tasks.order_by('-created_at')
    elif sort == 'oldest':
        tasks = tasks.order_by('created_at')
    elif sort == 'due_date':
        tasks = tasks.order_by('due_date')
    elif sort == 'az':
        tasks = tasks.order_by('title')
    elif sort == 'priority':
        tasks = tasks.order_by(
            models.Case(
                models.When(priority='urgent', then=0),
                models.When(priority='high', then=1),
                models.When(priority='medium', then=2),
                models.When(priority='low', then=3),
                default=4,
                output_field=models.IntegerField(),
            )
        )

    today = timezone.now().date()
    total = Task.objects.filter(user=request.user).count()
    completed = Task.objects.filter(user=request.user, completed=True).count()
    pending = Task.objects.filter(user=request.user, completed=False).count()
    overdue = Task.objects.filter(user=request.user, completed=False, due_date__lt=today).count()
    percentage = round((completed / total * 100)) if total > 0 else 0

    context = {
        'tasks': tasks,
        'total': total,
        'completed': completed,
        'pending': pending,
        'overdue': overdue,
        'filter_status': filter_status,
        'filter_priority': filter_priority,
        'today': today,
        'percentage': percentage,
        'search': search,
        'sort': sort,
    }
    return render(request, 'tasks/dashboard.html', context)


@login_required
def task_create(request):
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.user = request.user
            task.save()
            messages.success(request, f'Task "{task.title}" created!')
            return redirect('dashboard')
    else:
        form = TaskForm()
    return render(request, 'tasks/task_form.html', {'form': form, 'action': 'Create'})


@login_required
def task_edit(request, pk):
    task = get_object_or_404(Task, pk=pk, user=request.user)
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, f'Task "{task.title}" updated!')
            return redirect('dashboard')
    else:
        form = TaskForm(instance=task)
    return render(request, 'tasks/task_form.html', {'form': form, 'action': 'Edit', 'task': task})


@login_required
def task_delete(request, pk):
    task = get_object_or_404(Task, pk=pk, user=request.user)
    if request.method == 'POST':
        title = task.title
        task.delete()
        messages.success(request, f'Task "{title}" deleted.')
        return redirect('dashboard')
    return render(request, 'tasks/task_confirm_delete.html', {'task': task})


@login_required
def task_toggle(request, pk):
    task = get_object_or_404(Task, pk=pk, user=request.user)
    task.completed = not task.completed
    task.save()
    return redirect('dashboard')


@login_required
def task_toggle_ajax(request, pk):
    if request.method == 'POST':
        task = get_object_or_404(Task, pk=pk, user=request.user)
        task.completed = not task.completed
        task.save()
        return JsonResponse({'completed': task.completed})