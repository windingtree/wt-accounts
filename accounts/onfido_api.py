# -*- coding: utf-8 -*-
import datetime
import onfido
from django.conf import settings
from onfido.rest import ApiException


def get_api():
    onfido.configuration.api_key['Authorization'] = 'token=' + settings.ONFIDO_TOKEN
    onfido.configuration.api_key_prefix['Authorization'] = 'Token'
    return onfido.DefaultApi()


def create_applicant(user):
    api = get_api()

    # setting applicant details
    applicant = onfido.Applicant()
    applicant.first_name = user.first_name
    applicant.last_name = user.last_name
    applicant.email = user.email
    applicant.dob = user.birth_date
    applicant.country = user.country

    address = onfido.Address()
    address.building_number = user.building_number
    address.street = user.street
    address.town = user.town
    address.postcode = user.postcode
    address.country = user.country

    applicant.addresses = [address]

    # Be sure to note the applicant id from the response
    applicant_creation_response = api.create_applicant(data=applicant)
    return applicant_creation_response


def check(applicant_id):
    api = get_api()

    check = onfido.CheckCreationRequest()
    check.type = 'express'

    report = onfido.Report()
    report.name = 'identity'

    check.reports = [report]

    check_creation_response = api.create_check(applicant_id, data=check)
    return check_creation_response
