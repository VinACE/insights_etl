"""
Definition of forms.
"""

from django import forms
from django.forms.utils import ErrorList
from django.forms.utils import ErrorDict
from django.forms.forms import NON_FIELD_ERRORS
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import ugettext_lazy as _

from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

class BootstrapAuthenticationForm(AuthenticationForm):
    """Authentication form which uses boostrap CSS."""
    username = forms.CharField(max_length=254,
                               widget=forms.TextInput({
                                   'class': 'form-control',
                                   'placeholder': 'User name'}))
    password = forms.CharField(label=_("Password"),
                               widget=forms.PasswordInput({
                                   'class': 'form-control',
                                   'placeholder':'Password'}))

class load_form(forms.Form):
    cft_filename_field = forms.CharField(label='CFT file', max_length=80, required = False, initial = 'CFT Ing.csv')
    ci_filename_field = forms.CharField(label='CI file', max_length=80, required = False, initial = 'fresh and clean - test.csv')
    cimap_filename_field = forms.CharField(label='CI Map file', max_length=80, required = False, initial = 'fresh and clean - Map.csv')
    excel_choices = (('recreate', 'Re-Create'), ('reload', 'Re-Load'), ('incrload', 'Incremental-Load'))
    excel_choices_field = forms.MultipleChoiceField(label='Load Mode', choices=excel_choices, required=False)
    excel_filename_field = forms.CharField(label='Excel file (xlsx)', max_length=80, required = False, initial = 'patents.xlsx')
    indexname_field = forms.CharField(label='Index name', max_length=80, required = False, initial = '')
    #ci_filename_field = forms.CharField(label='CI file', max_length=40, required = False, initial = 'ChoiceModel FF USA.csv')
    def add_form_error(self, message):
        if not self._errors:
            self._errors = ErrorDict()
        if not NON_FIELD_ERRORS in self._errors:
            self._errors[NON_FIELD_ERRORS] = self.error_class()
        self._errors[NON_FIELD_ERRORS].append(message)

class fmi_admin_form(forms.Form):
    index_choices = (('pi', 'Product Intelligence'), ('mi', 'MI - Market Intelligence'), ('si_sites', 'SI - Sites'),
                     ('feedly', 'Feedly'), ('scentemotion', 'Scent Emotion'), ('studies', 'CI/SE Studies'), ('survey', 'CI Survey'))
    index_choices_field = forms.MultipleChoiceField(label='Web Site', choices=index_choices, widget=forms.CheckboxSelectMultiple, required=True)
    opml_filename_field = forms.CharField(label='OPML file', max_length=40, required = False, initial = '')
    keyword_filename_field = forms.CharField(label='Keyword file', max_length=40, required = False, initial = '')
    def add_form_error(self, message):
        if not self._errors:
            self._errors = ErrorDict()
        if not NON_FIELD_ERRORS in self._errors:
            self._errors[NON_FIELD_ERRORS] = self.error_class()
        self._errors[NON_FIELD_ERRORS].append(message)


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')
        
    def save(self, commit=True):
        user = super(RegistrationForm, self).save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        
        if commit:
            user.save()
            
        return user
