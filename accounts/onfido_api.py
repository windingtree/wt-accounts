# -*- coding: utf-8 -*-
import datetime
import onfido
from django.conf import settings
from django.forms import model_to_dict
from onfido.rest import ApiException


def get_api():
    onfido.configuration.api_key['Authorization'] = 'token=' + settings.ONFIDO_TOKEN
    onfido.configuration.api_key_prefix['Authorization'] = 'Token'
    return onfido.DefaultApi()


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
    applicant_creation_response = api.create_applicant(data=applicant)
    return applicant_creation_response


def check(applicant_id):
    api = get_api()

    check = onfido.CheckCreationRequest()
    check.type = 'standard'

    report_ident = onfido.Report(name = 'identity')
    report_doc = onfido.Report(name = 'document')

    check.reports = [report_ident, report_doc]

    check_creation_response = api.create_check(applicant_id, data=check)
    return check_creation_response


def check_reload(applicant_id, check_id):
    api = get_api()
    api_response = api.find_check(applicant_id, check_id)
    return api_response
