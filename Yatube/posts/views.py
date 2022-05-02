from contextvars import Context
from multiprocessing import context
from django.http import HttpResponse
from .models import Post, Group
from django.shortcuts import render, get_object_or_404

def index(request):    
    posts = Post.objects.order_by('-pub_date')[:10]
    context = {
        'posts': posts,
    }
    return render(request, 'posts/index.html', context)
       
def group_posts(request, slug):
    template = 'posts/group_list.html'
    title = 'Yatube groups'
    group = get_object_or_404(Group, slug=slug)
    posts = Post.objects.filter(group=group).order_by('-pub_date')[:10]
    context = {
        'group': group,
        'posts': posts,
    }
    return render(request, 'posts/group_list.html', context) 
