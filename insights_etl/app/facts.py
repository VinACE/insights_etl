from datetime import datetime
from datetime import time
from datetime import timedelta
import re
from pandas import Series, DataFrame
import pandas as pd
import collections

import app.models as models
import app.survey as survey

fct2qst = {
    "emotion"           : ["emotion"],
    "suitable_stage"    : ["suitable_stage"],
    "hedonics"          : ["liking.keyword"],
    "freshness"         : ["freshness"],
    }

facts_conf = {
    "emotion"           : {"type" : "boolean"},
    "suitable_stage"    : {"type" : "boolean"},
    "hedonics"          : {"type" : "ordinal"},
    "freshness"         : {"type" : "ordinal"},
    }

def fct_map_qst(question):
    global fct2qst

    for fact, questions in fct2qst.items():
        if question in questions:
            return fact
    return None

def get_values_respondents(fqav_df, question, answer, facet):
    values = []
    nr_respondents = 0
    for column in fqav_df.columns:
        if column[0] == question and column[1] == answer:
            values.append(column[2])
            nr_respondents = nr_respondents + fqav_df[column][facet]
    return values, nr_respondents


def facts_survey(survey_field, facts_choices, norms_choices):
    facts_dashboard = {
        "liking_col" : {
            'chart_type': "Table",
            'chart_title' : "Liking/Hedonics Count",
            'chart_data'  : "facet",
            'X_facet'     : {
                'field'   : "liking.keyword",
                'label'   : "Liking/Hedonics" },
            },
        "freshness_col" : {
            'chart_type': "Table",
            'chart_title' : "Freshness Count",
            'chart_data'  : "facet",
            'X_facet'     : {
                'field'   : "freshness",
                'label'   : "Freshness" },
            },
        "emotion_col" : {
            'chart_type': "ColumnChart",
            'chart_title' : "Emotion Count",
            'chart_data'  : "facet",
            'X_facet'     : {
                'field'   : "emotion",
                'total'   : False,
                'label'   : "Emotion" },
            'Y_facet'     : {
                'field'   : "answer",
                "axis"    : 0,
                'label'   : "Answer" },
            },
        "suitable_stage_col" : {
            'chart_type': "ColumnChart",
            'chart_title' : "Suitable Stage Count",
            'chart_data'  : "facet",
            'X_facet'     : {
                'field'   : "suitable_stage",
                'total'   : False,
                'label'   : "Suitable Stage" },
            'Y_facet'     : {
                'field'   : "answer",
                "axis"    : 0,
                'label'   : "Answer" },
            },
        }

    #facets = collections.OrderedDict()
    #for facet in models.SurveySeekerView.facets:
    #    if facet.field == 'blindcode.keyword':
    #        facet_tile = facet
    #    if facet.field == 'survey.keyword':
    #        facet_survey = facet
    #    for chart_name, chart in facts_dashboard.items():
    #        if facet.field == chart['X_facet']['field']:
    #            facets[facet] = []

    #search_tile = models.SurveySeekerView.get_empty_search(models.SurveySeekerView)
    ##search_tile = facet_survey.filter(search_tile, survey_field)
    #search_tile = models.SurveySeekerView.get_tile_aggr(models.SurveySeekerView, search_tile, facet_tile,
    #                                                    facets=facets, dashboard=facts_dashboard, aggregate=True)
    ##search_tite = search_tile.from_dict(body)
    #body = search_tile.to_dict()
    #results_tile = search_tile.execute(ignore_cache=True)
    #tile_df, tiles_select = seeker.dashboard.tile(models.SurveySeekerView, [facet_tile], facts_dashboard, results_tile)
    #seeker.models.stats_df, seeker.models.corr_df = seeker.dashboard.stats(tile_df)

    #facts = {}
    #fqav_df = seeker.models.fqav_df
    #for column in fqav_df.columns:
    #    question = column[0]
    #    answer = column[1]
    #    fact = fct_map_qst(question)
    #    if question in facts_choices and fact:
    #        for facet in fqav_df.index:
    #            if facts_conf[fact]['type'] == 'boolean':
    #                values, nr_respondents = get_values_respondents(fqav_df, question, answer, facet)
    #                percentile = 0
    #                for value in values:
    #                    # convert the aggr field name to the Survey answer (i.e. intensity.keyword -> Intensity
    #                    if survey.aggr_map_ans(answer):
    #                        answer = survey.aggr_map_ans(answer)
    #                    value_code = survey.answer_value_decode(answer, value)
    #                    if value_code == "Yes":
    #                        value_code = 1
    #                    elif value_code == "No":
    #                        value_code = 0
    #                    if nr_respondents > 0:
    #                        percentile = (fqav_df[column][facet] * value_code) / nr_respondents
    #                    else:
    #                        percentile = (fqav_df[column][facet] * value_code)
    #                facts[(facet, fact, answer)] = percentile
    #            elif facts_conf[fact]['type'] == 'ordinal':
    #                values, nr_respondents = get_values_respondents(fqav_df, question, answer, facet)
    #                percentile = 0
    #                total = 0
    #                for value in values:
    #                    # convert the aggr field name to the Survey answer (i.e. intensity.keyword -> Intensity
    #                    if survey.aggr_map_ans(answer):
    #                        value_code = survey.answer_value_decode(survey.aggr_map_ans(answer), value)
    #                    else:
    #                        value_code = survey.answer_value_decode(answer, value)
    #                    if type(value_code) == str:
    #                        try:
    #                            value_code = int(float(value_code))
    #                        except:
    #                            value_code = 0
    #                    total = total + value_code * fqav_df[column][facet]
    #                    if nr_respondents > 0:
    #                        percentile = fqav_df[column][facet] / nr_respondents
    #                    else:
    #                        percentile = fqav_df[column][facet]
    #                    facts[(facet, fact, value)] = percentile
    #                mean = total / nr_respondents
    #                facts[(facet, fact, 'mean')] = mean

    return facts



