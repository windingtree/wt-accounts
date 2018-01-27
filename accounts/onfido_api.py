# -*- coding: utf-8 -*-
import datetime
import json

import onfido
from django.conf import settings
from django.core.exceptions import ValidationError
from django.forms import model_to_dict
from onfido.rest import ApiException


def get_api():
    onfido.configuration.api_key['Authorization'] = 'token=' + settings.ONFIDO_TOKEN
    onfido.configuration.api_key_prefix['Authorization'] = 'Token'
    return onfido.DefaultApi()


def handle_exception(exc):
    body = json.loads(exc.body)
    if body.get('error', {}).get('type', '') == 'validation_error':
        message = body['error']['message'] + ' ' + str(body['error'].get('fields', ''))
        raise ValidationError(message)
    raise exc
    # {"error":{"type":"validation_error","message":"There was a validation error on this request","fields":{"addresses":[{"town":["can't be blank"]}]}}}


def create_applicant(user):
    api = get_api()

    # setting applicant details
    applicant = onfido.Applicant(**model_to_dict(user, fields=(
        'first_name', 'last_name', 'email', 'mobile')))
    applicant.dob = user.birth_date
    applicant.country = user.country.alpha3

    address = onfido.Address(**model_to_dict(user, fields=(
        'street', 'building_number', 'town', 'postcode')))
    address.country = user.country.alpha3

    applicant.addresses = [address]

    # Be sure to note the applicant id from the response
    try:
        applicant_creation_response = api.create_applicant(data=applicant)
    except ApiException as e:
        handle_exception(e)
    return applicant_creation_response


def check(applicant_id):
    api = get_api()

    check = onfido.CheckCreationRequest()
    check.type = 'standard'

    report_ident = onfido.Report(name = 'identity')
    report_doc = onfido.Report(name = 'document')
    #report_street = onfido.Report(name = 'street_level')
    report_facial = onfido.Report(name = 'facial_similarity')

    check.reports = [report_ident, report_doc, report_facial]

    check_creation_response = api.create_check(applicant_id, data=check)
    return check_creation_response


def check_reload(applicant_id, check_id):
    api = get_api()
    api_response = api.find_check(applicant_id, check_id)
    return api_response
