﻿from datetime import datetime
from datetime import time
from datetime import timedelta
from django.core.files import File
import glob, os
import sys
import pickle
import urllib
import requests
import json
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
import re
from requests_ntlm import HttpNtlmAuth
from pandas import Series, DataFrame
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup

from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q
from elasticsearch_dsl.connections import connections
from elasticsearch.client import IndicesClient
from elasticsearch.helpers import bulk
import app.models as models
import app.elastic as elastic
import app.survey as survey
from insights_etl.settings import BASE_DIR, ES_HOSTS


def load_studies_facts(survey_field, facts_d):
    es_host = ES_HOSTS[0]
    headers = {}
    if 'http_auth' in es_host:
        headers['http_auth'] = es_host['http_auth']
    host = es_host['host']
    index = 'studies'
    doc_type = 'studies'
    url = "http://" + host + ":9200/" + index

    bulk_data = []
    count = 0
    total_count = 0
    facts_df = DataFrame.from_dict(facts_d, orient='index')
    facts_df['blindcode'] = [ix[0] for ix in facts_df.index]
    facts_df['fact'] = [ix[1] for ix in facts_df.index]
    facts_df['answer'] = [ix[2] for ix in facts_df.index]

    for blindcode, facts_blindcode_df in facts_df.groupby(facts_df['blindcode']):
        se = models.StudiesMap()
        se.cft_id = blindcode.split('-')[0]
        se.survey = survey_field
        se.blindcode = blindcode
        percentile = {}
        doc = None
        doc = {}
        doc['_id'] = blindcode.split('-')[0]
        doc['cft_id'] = blindcode.split('-')[0]
        doc['survey'] = survey_field
        doc['blindcode'] = blindcode

        for idx, fact_s in facts_blindcode_df.iterrows():
            fact = fact_s['fact']
            answer = fact_s['answer']
            #se.supplier = "CI"
            #se.olfactive = cft_s.olfactive
            #se.region = cft_s.region
            #se.review = cft_s.review
            #se.dilution = cft_s.dilution
            #se.intensity = cft_s.intensity

            if fact not in percentile.keys():
                percentile[fact] = []
            val = str(answer)
            prc = fact_s[0]
            if prc > 0 and val != 'Total':
                #percentile[fact].append((val, prc))
                percentile[fact].append({'val':val, 'prc':prc})

        for fact in percentile.keys():
            if fact == 'emotion':
                se.emotion = percentile[fact]
                doc['emotion'] = percentile[fact]
            if fact == 'suitable_stage':
                se.suitable_stage = percentile[fact]
            if fact == 'liking.keyword':
                se.liking = percentile[fact]
                se.hedonics = percentile[fact]
                doc['liking'] = percentile[fact]
                doc['hedonics'] = percentile[fact]
            if fact == 'freshness':
                se.freshness = percentile[fact]
                doc['freshness'] = percentile[fact]
        count = count + 1
        #data = elastic.convert_for_bulk(se, 'update')
        data = elastic.add_to_bulk(index, doc_type, doc, 'update')
        bulk_data.append(data)
        if count > 100:
            bulk(models.client, actions=bulk_data, stats_only=True)
            total_count = total_count + count
            print("load_studies_facts: written another batch, total written {0:d}".format(total_count))
            bulk_data = []
            count = 1

        #if '_id' in doc:
        #    id = doc['_id']
        #    doc.pop("_id", None)
        #else:
        #    id = str(count)
        #data = json.dumps(doc)
        #print("load_studies_facts: write fact line with id", id)
        #r = requests.put(url + "/" + doc_type + "/" + id, headers=headers, data=data)
        #print("load_excel: written excel line with id", id)

    bulk(models.client, actions=bulk_data, stats_only=True)
    pass


def abstract(map_s, row_s):
    global driver

    if driver == None:
        options = []
        options.append('--load-images=false')
        options.append('--ignore-ssl-errors=true')
        options.append('--ssl-protocol=any')
        #driver = webdriver.PhantomJS(executable_path='C:/Python34/phantomjs.exe', service_args=options)
        #driver = webdriver.PhantomJS(service_args=options)
        driver = webdriver.Chrome()
        driver.set_window_size(1120, 550)
        driver.set_page_load_timeout(3) # seconds
        driver.implicitly_wait(30) # seconds
    publication = row_s['Publication Number']
    url = row_s['url']
    try:
        #print("read_page: scraping url ", url)
        #html = urllib.request.urlopen(url)
        #bs = BeautifulSoup(html.read(), "lxml")
        #[script.decompose() for script in bs("script")]
        print("abstract: scraping publication", publication)
        driver.get(url)
        print("abstract: driver.get", publication)
    except:
        print("abstract: could not open url ", url)
    try:
        #time.sleep(3)
        abstract_tag = driver.find_element_by_id("PAT.ABE")
        print("abstract: driver.find_element_by_id", publication)
        print("abstract: abstract_tag.text", abstract_tag.text)
        tries = 0
        abstract_text = abstract_tag.text
        while len(abstract_text) == 0 and tries < 10000:
            abstract_text = abstract_tag.text
            tries = tries + 1
        print("abstract: abstract_text", abstract_text)
        print("abstract: TRIES", tries)
        #delay = 3 # seconds
        #abstract_tag = WebDriverWait(driver, delay).until(EC.presence_of_element_located((By.ID, "PAT.ABE")))
    except:
        print("abstact: loading took too much time!")
        abstract_text = ""

    return abstract_text
        
def blindcode(map_s, row_s):
    blindcode_text = row_s['blindcode']
    if len(blindcode_text) and len(row_s['fragr_name']) > 0:
        blindcode_text = blindcode_text + '-' + row_s['fragr_name'][0:3]
    return blindcode_text
    

def load_excel(excel_filename, excel_choices, indexname):
    global driver

    converters={}
    converters['column'] = str
    excel_file = os.path.join(BASE_DIR, 'data/' + excel_filename)
    try:
        mapping_df = pd.read_excel(excel_file, sheetname="mapping", header=0, converters=converters)
    except:
        cwd = os.getcwd()
        print("load_excel: working dirtory is: ", cwd)
        print("load_excel: excel_file: ", excel_file)
        return False

    mapping_df.fillna("", inplace=True)

    es_host = ES_HOSTS[0]
    headers = {}
    if 'http_auth' in es_host:
        headers['http_auth'] = es_host['http_auth']
    host = es_host['host']
    doc_type = os.path.splitext(excel_filename)[0]
    if indexname == '':
        index = "excel_" + doc_type
    else:
        index = indexname
        doc_type = indexname
    url = "http://" + host + ":9200/" + index

    # The idea is that each excel file ends up in its own mapping (doc_type).
    # (re-)loading a workbook means deleting the existing content and mapping and
    # (re-)create the new mapping with loading the content. However it is not
    # possible anymore to delete a doc_type. For the time being the whole index will
    # be deleted.


    # create mapping in excel index
    properties = {
        'subset' : {'type' : 'string', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}}
        }
    converters={}
    for map_key, map_s in mapping_df.iterrows():
        column = map_s['column']
        field = map_s['field']
        if field == "":
            continue
        format = map_s['format']
        type = map_s['type']
        if type == 'string':
            properties[field] = {'type' : 'string', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}}
            converters[column] = str
        elif type == 'date':
            properties[field] = {'type' : 'date'}
        elif type == 'integer':
            properties[field] = {'type' : 'integer'}
            converters[column] = int
        elif type == 'float':
            properties[field] = {'type' : 'float'}
            converters[column] = float
        elif type == 'text':
            properties[field] = {'type' : 'text'}
            converters[column] = str
        elif type == 'list':
            pass
        elif type == 'nested':
            properties[field] =  {'type' : 'nested', 
                                    'properties' : 
                                    {'val' : {'type' : 'string', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}},
                                        'prc' : {'type' : 'float'}}}
            pass
            #properties[field] = {'type' : 'string', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}}
            #properties[field] = { 'properties' :
            #                     { field : {'type' : 'string', 'fields' : {'keyword' : {'type' : 'keyword', 'ignore_above' : 256}}}}
            #                    }

    mapping = json.dumps({'properties' : properties})

    # delete and re-create excel index
    if 'recreate' in excel_choices:
        # first delete
        r = requests.delete(url, headers=headers)
        r = requests.put(url, headers=headers)
        # next create
        r = requests.put(url + "/_mapping/" + doc_type, headers=headers, data=mapping)

    ## store document
    #data = json.dumps({
    #    "aop" : ["Creative"],
    #    "role" : "Creative Incubators",
    #    "name" : "113Industries, US   Razi Imam",
    #    "link" : "http://113industries.com/",
    #    "why"  : "A scientific research and innovation company made up of scientists and entrepreneurs, who works with leading Fortune 500 companies to help them invent their next generation products based on Social Design-Driven Innovation process and ensure their economic viability by rapidly innovating new products",
    #    "how"  : "Use the power of Big Data to analyze over 200,000 consumer conversations related to product consumption to generate an accurate profile of the consumers, their compensating behaviors and most of all their unarticulated needs.",
    #    "what" : "Social Design-Driven Innovation project to Discover insights, compensating behaviors and unarticulated needs of consumers in relation to air care in the home and auto space in the United States and United Kingdom Open new markets with innovative new products, solutions, and services or business model improvements that will create differentiation to IFF current and potential customers",
    #    "who" : "Razi Imam  razii@113industries.com",
    #    "country" : "USA",
    #    "contacts" : ["Razi Imam"],
    #    "company" : "113 Industries"
    #    })
    #r = requests.put(url + "/" + doc_type + "/1", headers=headers, data=data)
    # query excel
    query = json.dumps({
        "query": {
            "match_all": {}
            }
        })
    r = requests.get(url + "/" + doc_type + "/_search", headers=headers, data=query)
    results = json.loads(r.text)

    data_df = pd.read_excel(excel_file, sheetname="data", header=0, converters=converters)
    data_df.fillna("", inplace=True)
    bulk_data = []
    count = 1
    total_count = 0
    for key, row_s in data_df.iterrows():
        doc = None
        doc = {}
        doc['subset'] = doc_type
        for map_key, map_s in mapping_df.iterrows():
            field = map_s['field']
            if field == "":
                continue
            format = map_s['format']
            column = map_s['column']
            initial = getattr(map_s, 'initial', '')
            if column in row_s:
                cell = row_s[column]
            else:
                if len(initial) > 0:
                    cell = initial
                else:
                    cell = None
            type = map_s['type']
            if format == 'script':
                module = sys.modules[__name__]
                if hasattr(module, field):
                    doc[field] = getattr(module, field)(map_s, row_s)
            else:
                # incase no cell defined, doc[field] will not be populated
                if cell is not None:
                    if type == 'list':
                        if field not in doc:
                            doc[field] = []
                        if cell != "":
                            if len(format) > 0:
                                delimiter = format
                                if delimiter == '\\n':
                                    items = cell.splitlines()
                                else:
                                    items = cell.split(delimiter)
                                for item in items:
                                    doc[field].append(item)
                            else:
                                doc[field].append(cell)
                    elif type == 'nested':
                        if cell == '':
                            doc[field] = []
                        else:
                            nested_value = cell.split(',')
                            doc[field] = {'val': nested_value[0], 'prc': float(nested_value[1])}
                    else:
                        doc[field] = cell

        if 'id' in doc:
            id = doc['id']
        else:
            id = str(count)
        data = json.dumps(doc)
        print("load_excel: write excel line with id", id)
        r = requests.put(url + "/" + doc_type + "/" + id, headers=headers, data=data)
        print("load_excel: written excel line with id", id)
        count = count + 1

    #if driver != None:
    #    driver.quit()
    return True


def load_scentemotion(cft_filename):
    ml_file = 'data/' + cft_filename
    cft_df = pd.read_csv(ml_file, sep=';', encoding='ISO-8859-1', low_memory=False)
    cft_df.fillna(0, inplace=True)
    cft_df.index = cft_df['cft_id']
    bulk_data = []
    count = 0
    total_count = 0
    for cft_id, cft_s in cft_df.iterrows():
        se = models.ScentemotionMap()
        se.cft_id = cft_id
        se.dataset = "ingredients"
        se.ingr_name = cft_s.ingr_name
        se.IPC = cft_s.IPC
        se.supplier = cft_s.supplier
        se.olfactive = cft_s.olfactive
        se.region = cft_s.region
        se.review = cft_s.review
        se.dilution = cft_s.dilution
        se.intensity = cft_s.intensity

        percentile = {}
        for col in cft_s.index:
            col_l = col.split("_", 1)
            fct = col_l[0]
            if fct not in ["mood", "smell", "negative", "descriptor", "color", "texture"]:
                continue
            if fct not in percentile.keys():
                percentile[fct] = []
            val = col_l[1]
            prc = cft_s[col]
            if prc > 0:
                #percentile[fct].append((val, "{0:4.2f}".format(prc)))
                percentile[fct].append((val, prc))

        se.mood = percentile["mood"]
        se.smell = percentile["smell"]
        se.negative = percentile["negative"]
        se.descriptor = percentile["descriptor"]
        se.color = percentile["color"]
        se.texture = percentile["texture"]

        data = elastic.convert_for_bulk(se, 'update')
        bulk_data.append(data)
        count = count + 1
        if count > 100:
            bulk(models.client, actions=bulk_data, stats_only=True)
            total_count = total_count + count
            print("load_scentemotion: written another batch, total written {0:d}".format(total_count))
            bulk_data = []
            count = 1

    bulk(models.client, actions=bulk_data, stats_only=True)
    pass

def map_survey(survey_filename, map_filename):
    if map_filename != '':
        survey.qa = survey.qa_map(map_filename)
    survey_name = os.path.splitext(survey_filename)[0].split('-', 1)[0].strip()
    ml_file = 'data/' + survey_filename
    survey_df = pd.read_csv(ml_file, sep=';', encoding='ISO-8859-1', low_memory=False)
    survey_df.fillna(0, inplace=True)
    field_map, col_map, header_map = survey.map_columns(survey_name, survey_df.columns)
    return field_map, col_map, header_map

def load_survey1(request, survey_filename, map_filename):
    if map_filename != '':
        survey.qa = survey.qa_map(map_filename)
    survey_name = os.path.splitext(survey_filename)[0].split('-', 1)[0].strip()
    ml_file = 'data/' + survey_filename
    survey_df = pd.read_csv(ml_file, sep=';', encoding='ISO-8859-1', low_memory=False)
    survey_df.fillna(0, inplace=True)
    # col_map[column]: (field, question, answer, dashboard)
    # field_map[field]: [question=0, answer=1, column=2, field_type=3)]
    field_map , col_map, header_map = survey.map_columns(survey_name, survey_df.columns)
    survey_df.index = survey_df[field_map['resp_id'][0][2]]
    bulk_data = []
    count = 0
    total_count = 0
    for resp_id, survey_s in survey_df.iterrows():
        resp_id = survey.answer_value_to_string(survey_s[field_map['resp_id'][0][2]])
        blindcode = survey.answer_value_to_string(survey_s[field_map['blindcode'][0][2]])
        #sl = models.SurveyMap()
        #sl.resp_id = resp_id+"_"+blindcode
        #sl.survey  = survey_name
        data = {}
        #data['_id'] = resp_id+"_"+blindcode
        #data['resp_id'] = resp_id+"_"+blindcode
        #data['survey'] = survey_name
        for field, maps in field_map.items():
            # resp_id is the unique id of the record, this is already set above
            #if field == 'resp_id':
            #    continue
            # map: 0=question, 1=answer, 2=column, 3=field_type
            map = maps[0]
            answer_value = survey_s[map[2]]
            answer_value = survey.answer_value_to_string(answer_value)
            answer_value = survey.answer_value_encode(map[0], map[1], field, answer_value)
            # column mapping, no question
            if map[0] == None:
                # in case of multiple mapping search for the column that has a value
                for ix in range(1, len(maps)):
                    map = maps[ix]
                    answer_value_2 = survey_s[map[2]]
                    answer_value_2 = survey.answer_value_to_string(answer_value_2)
                    if (field == 'blindcode'):
                        answer_value = answer_value + '-' + answer_value_2[:3]
                    else:
                        if len(answer_value_2) > len(answer_value):
                            answer_value = answer_value_2
                #setattr(sl, field, answer_value)
                elastic.convert_field(data, field, map, answer_value)
            # question mapping, no answer
            elif map[1][0] == '_':
                #setattr(sl, field, answer_value)
                elastic.convert_field(data, field, map, answer_value)
            # answer mapping
            else:
                #setattr(sl, field, {map[1]: answer_value})
                #attr = getattr(sl, field)
                for ix in range(0, len(maps)):
                    map = maps[ix]
                    answer_value = survey_s[map[2]]
                    answer_value = survey.answer_value_to_string(answer_value)
                    answer_value = survey.answer_value_encode(map[0], map[1], field, answer_value)
                    #attr[map[1]] = answer_value
                    ##attr.append({map[1]: answer_value})
                    elastic.convert_field(data, field, map, answer_value)
        #data = elastic.convert_for_bulk(sl, 'update')
        survey.map_header(request, survey_name, data)
        data['_id'] = survey.map_id(survey_name, data)
        data = elastic.convert_data_for_bulk(data, 'survey', 'survey', 'update')
        bulk_data.append(data)
        count = count + 1
        if count > 100:
            bulk(models.client, actions=bulk_data, stats_only=True)
            total_count = total_count + count
            print("crawl_survey: written another batch, total written {0:d}".format(total_count))
            bulk_data = []
            count = 1
            #break

    bulk(models.client, actions=bulk_data, stats_only=True)
    pass


def load_survey(request, survey_filename, map_filename):
    survey_name = os.path.splitext(survey_filename)[0].split('-', 1)[0].strip()
    if survey_name == 'fresh and clean':
         load_survey1(request, survey_filename, map_filename)
    elif survey_name == 'orange beverages':
         load_survey1(request, survey_filename, map_filename)
    elif survey_name == 'global panels':
         load_survey1(request, survey_filename, map_filename)
