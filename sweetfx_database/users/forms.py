from django.forms import ModelForm
from . import models as M

class RequiredForm(ModelForm):
    required_css_class = "formrequired"
    
class ProfileForm(RequiredForm):
    class Meta:
        model = M.UserProfile
        fields = ("description", "theme", "css")
