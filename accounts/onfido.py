# -*- coding: utf-8 -*-
import datetime
import onfido
from django.conf import settings
from onfido.rest import ApiException


def create_applicant():
    # Configure API key authorization: Token
    onfido.configuration.api_key['Authorization'] = 'token=' + settings.ONFIDO_TOKEN
    onfido.configuration.api_key_prefix['Authorization'] = 'Token'
    # create an instance of the API class
    api = onfido.DefaultApi()

    # setting applicant details
    applicant = onfido.Applicant()
    applicant.first_name = 'John'
    applicant.last_name = 'Smith'
    applicant.email = 'johnsmith@fakegmail.com'
    applicant.dob = datetime.date(1980, 1, 22)
    applicant.country = 'GBR'

    address = onfido.Address()
    address.building_number = '100'
    address.street = 'Main Street'
    address.town = 'London'
    address.postcode = 'SW4 6EH'
    address.country = 'GBR'

    applicant.addresses = [address]

    # Be sure to note the applicant id from the response
    applicant_creation_response = api.Applicants.create(data=applicant)
    return applicant_creation_response


def check(applicant_id):
    onfido.configuration.api_key['Authorization'] = 'token=' + settings.ONFIDO_TOKEN
    onfido.configuration.api_key_prefix['Authorization'] = 'Token'
    # create an instance of the API class
    api = onfido.DefaultApi()

    check = onfido.CheckCreationRequest()
    check.type = 'express'

    report = onfido.Report()
    report.name = 'identity'

    check.reports = [report];

    check_creation_response = api.create_check(applicant_id, data=check)
    return check_creation_response
