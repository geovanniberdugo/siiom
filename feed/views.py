from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin


class FeedView(LoginRequiredMixin, TemplateView):
    template_name = 'feed/feed.html'


