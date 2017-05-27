from django.forms import ModelForm
import models as M

class RequiredForm(ModelForm):
    required_css_class = "formrequired"

class PresetForm(RequiredForm):
    class Meta:
        model = M.Preset
        fields = ("title", "shader", "description", "settings_text", "visible")

class GameForm(RequiredForm):
    class Meta:
        model = M.Game
        fields = ("title", "url", "exename", "sweetfx_notes")

class PresetScreenshotForm(RequiredForm):
    class Meta:
        model = M.PresetScreenshot
        fields = ("image", "sweetfx_state", "description", "comparison_image", "visible")
