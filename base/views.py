from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib.auth import authenticate, login, logout
from .models import Room, Topic, Message, User
from django.shortcuts import get_object_or_404
from .forms import RoomForm, UserForm, MyUserCreationForm
from django.http import HttpResponseForbidden
import re

# Utility function to convert plain-text URLs to clickable links
def linkify(text):
    url_pattern = re.compile(r'(https?://[^\s]+)')
    return url_pattern.sub(r'<a href="\1" target="_blank">\1</a>', text)

# Utility function to render centralized messages

def render_center_message(request, message, redirect_url):
    """
    Render a simple centered message box inline without a separate template.
    """
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Message</title>
        <style>
            html, body {{
                height: 100%;
                margin: 0;
                font-family: Arial, sans-serif;
                background-image: url('/static/images/bg.jpg');
                background-size: cover;
                background-position: center;
                display: flex;
                align-items: center;
                justify-content: center;
            }}
            .message-container {{
                text-align: center;
                padding: 40px;
                background: rgba(255, 255, 255, 0.9);
                border: 1px solid #ddd;
                box-shadow: 0 6px 12px rgba(0, 0, 0, 0.6);
                border-radius: 15px;
                width: 80%; /* Increased width */
                max-width: 600px; /* Increased maximum width */
            }}
            .message-container h2 {{
                margin-bottom: 20px;
                font-size: 22px; /* Increased font size */
                color: #333;
            }}
            .message-container button {{
                padding: 12px 25px;
                background-color: #000;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 16px;
                cursor: pointer;
            }}
            .message-container button:hover {{
                background-color: #444;
            }}
        </style>
    </head>
    <body>
        <div class="message-container">
            <h2>{message}</h2>
            <form action="{redirect_url}">
                <button type="submit">OK</button>
            </form>
        </div>
    </body>
    </html>
    """
    return HttpResponse(html)


# Login page
def loginPage(request):
    page = 'login'
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        email = request.POST.get('email').lower()
        password = request.POST.get('password')

        try:
            user = User.objects.get(email=email)
        except:
            return render_center_message(request, 'User does not exist', reverse('login'))

        user = authenticate(request, email=email, password=password)

        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            return render_center_message(request, 'Username OR password does not exist', reverse('login'))

    context = {'page': page}
    return render(request, 'base/login_register.html', context)

def logoutUser(request):
    logout(request)
    return render_center_message(request, 'You have been logged out successfully.',  reverse('home'))

def registerPage(request):
    form = MyUserCreationForm()

    if request.method == 'POST':
        form = MyUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()
            login(request, user)
            return render_center_message(request, 'Registration successful! Welcome to the platform.',  reverse('home'))
        else:
            return render_center_message(request, 'An error occurred during registration. Please try again.', reverse('register'))

    return render(request, 'base/login_register.html', {'form': form})

def home(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''

    rooms = Room.objects.filter(
        Q(topic__name__icontains=q) |
        Q(name__icontains=q) |
        Q(description__icontains=q)
    )

    topics = Topic.objects.all()[0:5]
    room_count = rooms.count()
    room_messages = Message.objects.filter(
        Q(room__topic__name__icontains=q))[0:3]

    context = {'rooms': rooms, 'topics': topics,
               'room_count': room_count, 'room_messages': room_messages}
    return render(request, 'base/home.html', context)

def room(request, pk):
    room = Room.objects.get(id=pk)
    room_messages = room.message_set.all()
    participants = room.participants.all()

    if request.method == 'POST':
        # Handle text submission
        message_body = request.POST.get('body')
        file = request.FILES.get('file')

        # Convert plain-text URLs to clickable links
        linked_body = linkify(message_body)

        # Create the message object
        message = Message.objects.create(
            user=request.user,
            room=room,
            body=linked_body,
            file=file
        )
        room.participants.add(request.user)
        return redirect('room', pk=room.id)

    context = {'room': room, 'room_messages': room_messages,
               'participants': participants}
    return render(request, 'base/room.html', context)

def userProfile(request, pk):
    user = User.objects.get(id=pk)
    rooms = user.room_set.all()
    room_messages = user.message_set.all()
    topics = Topic.objects.all()
    context = {'user': user, 'rooms': rooms,
               'room_messages': room_messages, 'topics': topics}
    return render(request, 'base/profile.html', context)

@login_required(login_url='login')
def createRoom(request):
    form = RoomForm()
    topics = Topic.objects.all()
    if request.method == 'POST':
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name=topic_name)

        Room.objects.create(
            host=request.user,
            topic=topic,
            name=request.POST.get('name'),
            description=request.POST.get('description'),
        )
        return render_center_message(request, 'Room created successfully.', reverse('home'))

    context = {'form': form, 'topics': topics}
    return render(request, 'base/room_form.html', context)

@login_required(login_url='login')
def updateRoom(request, pk):
    room = Room.objects.get(id=pk)
    form = RoomForm(instance=room)
    topics = Topic.objects.all()
    if request.user != room.host:
        return HttpResponse('You are not allowed here!!')

    if request.method == 'POST':
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name=topic_name)
        room.name = request.POST.get('name')
        room.topic = topic
        room.description = request.POST.get('description')
        room.save()
        return redirect('home')

    context = {'form': form, 'topics': topics, 'room': room}
    return render(request, 'base/room_form.html', context)

@login_required
def delete_message(request, pk):
    message = get_object_or_404(Message, id=pk)
    if request.user == message.user or request.user == message.room.host:
        message.delete()
        return render_center_message(request, "Message deleted successfully!", reverse('room', kwargs={'pk': message.room.id}))
    else:
        return render_center_message(request, "You are not authorized to delete this message.", reverse('room', kwargs={'pk': message.room.id}))

@login_required(login_url='login')
def updateUser(request):
    user = request.user
    form = UserForm(instance=user)

    if request.method == 'POST':
        form = UserForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            return render_center_message(request, 'Your profile has been updated successfully.', reverse('user-profile', args=[user.id]))
        else:
            return render_center_message(request, 'There was an error updating your profile. Please try again.', reverse('update-user'))

    return render(request, 'base/update-user.html', {'form': form})

def topicsPage(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    topics = Topic.objects.filter(name__icontains=q)
    return render(request, 'base/topics.html', {'topics': topics})

def activityPage(request):
    room_messages = Message.objects.all()
    return render(request, 'base/activity.html', {'room_messages': room_messages})

@login_required
def delete_room(request, pk):
    room = get_object_or_404(Room, id=pk)

    if request.user == room.host:
        if request.method == 'POST':
            room.delete()
            return render_center_message(request, f'Room "{room.name}" deleted successfully.', reverse('home'))


        return render(request, 'base/delete_confirm.html', {'room': room})

    return render_center_message(request, 'You are not the host of this room and cannot delete it.', reverse('home'))

