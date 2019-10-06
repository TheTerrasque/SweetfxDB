from django.forms import ModelForm, CharField, Textarea
from . import models as M

class RequiredForm(ModelForm):
    required_css_class = "formrequired"
    
class NewThreadForm(RequiredForm):
    text = CharField(widget=Textarea)
    
    class Meta:
        model = M.ForumThread
        fields = ("title",)
        
class NewPostForm(RequiredForm):
    class Meta:
        model = M.ForumPost
        fields = ("text", )
