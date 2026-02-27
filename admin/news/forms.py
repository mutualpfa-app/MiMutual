"""
Formularios del admin de News.
"""
from django import forms

from .models import News
from .widgets import ImageDropWidget


class NewsAdminForm(forms.ModelForm):
    class Meta:
        model = News
        fields = "__all__"
        widgets = {
            "image_url": ImageDropWidget(),
        }
