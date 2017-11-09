"""
Definition of views.
"""

from django.shortcuts import render, redirect, render_to_response
from django.template.context_processors import csrf
from django.http import HttpRequest
from django.template import RequestContext
from django.views.generic.base import TemplateView
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q
import json
from datetime import datetime, time
import insights_etl.settings
import app.elastic as elastic
import app.load as load
import app.survey as survey
import app.facts as facts
import app.fmi_admin as fmi_admin
import app.azure as azure
import app.models as models
import app.survey
from .forms import *

def home(request):
    """Renders the home page."""
    assert isinstance(request, HttpRequest)
    return render(
        request,
        'app/index.html',
        context_instance = RequestContext(request,
        {
            'title':'Home Page',
            'year':datetime.now().year,
        })
    )


def load_view(request):
    """Renders the load page."""
    if request.method == 'POST':
        form = load_form(request.POST)
        form.is_valid()
        ci_filename = form.cleaned_data['ci_filename_field']
        cimap_filename = form.cleaned_data['cimap_filename_field']
        # called form loadresults.html
        if 'load_survey' in form.data:
            load.load_survey(request, ci_filename, cimap_filename)
        # called from load.html
        if form.is_valid():
            cft_filename = form.cleaned_data['cft_filename_field']
            excel_choices = form.cleaned_data['excel_choices_field']
            excel_filename = form.cleaned_data['excel_filename_field']
            indexname = form.cleaned_data['indexname_field']
            ci_filename = form.cleaned_data['ci_filename_field']
            cimap_filename = form.cleaned_data['cimap_filename_field']
            if 'load_scentemotion' in form.data:
                load.load_scentemotion(cft_filename)
            if 'load_excel' in form.data:
                if not load.load_excel(excel_filename, excel_choices, indexname):
                    form.add_form_error("Could not retrieve or index excel file")
            if 'map_survey' in form.data:
                field_map, col_map, header_map = load.map_survey(ci_filename, cimap_filename)
                qa = {}
                for question, answers in survey.qa.items():
                    qa[question] = list(answers.keys())
                context = {
                    'form'          : form,
                    'col_map'       : col_map,
                    'header_map'    : header_map,
                    'qa'            : qa,
                    }
                return render(request, 'app/loadresults.html', context )
            if 'return_survey' in form.data:
                pass
            return render(request, 'app/load.html', {'form': form, 'es_hosts' : insights_etl.settings.ES_HOSTS } )
    else:
        form = load_form(initial={'excel_choices_field':['recreate']})

    return render(request, 'app/load.html', {'form': form, 'es_hosts' : insights_etl.settings.ES_HOSTS },
                  context_instance = RequestContext(request, {'message':'IFF - Insight Platform', 'year':datetime.now().year,} ))



def fmi_admin_view(request):
    """Renders the Admin Index page."""
    if request.method == 'POST':
        form = fmi_admin_form(request.POST)
        if form.is_valid():
            index_choices = form.cleaned_data['index_choices_field']
            opml_filename = form.cleaned_data['opml_filename_field']
            keyword_filename = form.cleaned_data['keyword_filename_field']
            if 'index_elastic' in form.data:
                fmi_admin.create_index_elastic(index_choices)
            elif 'analyzer' in form.data:
                fmi_admin.create_analyzer(index_choices)
            if 'index_azure' in form.data:
                azure.create_index_azure(index_choices)
            elif 'export_opml' in form.data:
                if not fmi_admin.export_opml(index_choices, opml_filename):
                    form.add_form_error("Could not export OPML")
            elif 'import_opml' in form.data:
                if not fmi_admin.import_opml(index_choices, opml_filename):
                    form.add_form_error("Could not import OPML")
            elif 'keywords' in form.data:
                if not fmi_admin.read_keywords(index_choices, keyword_filename):
                    form.add_form_error("Could not read keywords file")
            return render(request, 'app/fmi_admin.html', {'form': form })
    else:
        form = fmi_admin_form(initial={'index_choices_field':['cosmetic']})

    return render(request, 'app/fmi_admin.html', {'form': form },
                  context_instance = RequestContext(request, {'message':'IFF - Insight Platform', 'year':datetime.now().year,} ))


def contact(request):
    """Renders the contact page."""
    assert isinstance(request, HttpRequest)
    return render(
        request,
        'app/contact.html',
        context_instance = RequestContext(request,
        {
            'title':'Contact',
            'message':'Your contact page.',
            'year':datetime.now().year,
        })
    )

def about(request):
    """Renders the about page."""
    assert isinstance(request, HttpRequest)
    return render(
        request,
        'app/about.html',
        context_instance = RequestContext(request,
        {
            'title':'About',
            'message':'Your application description page.',
            'year':datetime.now().year,
        })
    )

def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('/accounts/register_complete')

    else:
        form = RegistrationForm()
    token = {}
    token.update(csrf(request))
    token['form'] = form

    return render_to_response('registration/register.html', token)

def registrer_complete(request):
    return render_to_response('registration/registrer_complete.html')