from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import User

INPUT_CLASSES = (
    "mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm "
    "shadow-sm focus:border-gray-500 focus:outline-none"
)


class StyledFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", INPUT_CLASSES)


class SignupForm(StyledFormMixin, UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")


class LoginForm(StyledFormMixin, AuthenticationForm):
    pass
