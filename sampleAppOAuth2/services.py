from django.conf import settings
from sampleAppOAuth2.models import Bearer
from datetime import datetime
import requests
import base64
import json
import random
from jose import jws, jwk
from sampleAppOAuth2 import getDiscoveryDocument
import uuid
# from base64 import urlsafe_b64decode, b64decode


# token can either be an accessToken or a refreshToken
def revokeToken(token):
    revoke_endpoint = getDiscoveryDocument.revoke_endpoint
    auth_header = 'Basic ' + stringToBase64(settings.CLIENT_ID + ':' + settings.CLIENT_SECRET)
    headers = {'Accept': 'application/json', 'content-type': 'application/json', 'Authorization': auth_header}
    payload = {'token': token}
    r = requests.post(revoke_endpoint, json=payload, headers=headers)

    if r.status_code >= 500:
        return 'internal_server_error'
    elif r.status_code >= 400:
        return 'Token is incorrect.'
    else:
        return 'Revoke successful'


def getBearerToken(auth_code):
    token_endpoint = getDiscoveryDocument.token_endpoint
    auth_header = 'Basic ' + stringToBase64(settings.CLIENT_ID + ':' + settings.CLIENT_SECRET)
    headers = {'Accept': 'application/json', 'content-type': 'application/x-www-form-urlencoded',
               'Authorization': auth_header}
    payload = {
        'code': auth_code,
        'redirect_uri': settings.REDIRECT_URI,
        'grant_type': 'authorization_code'
    }
    r = requests.post(token_endpoint, data=payload, headers=headers)
    if r.status_code != 200:
        return r.text
    bearer_raw = json.loads(r.text)

    if 'id_token' in bearer_raw:
        idToken = idToken = bearer_raw['id_token']
    else:
        idToken = None

    return Bearer(bearer_raw['x_refresh_token_expires_in'], bearer_raw['access_token'], bearer_raw['token_type'],
                  bearer_raw['refresh_token'], bearer_raw['expires_in'], idToken=idToken)


def getBearerTokenFromRefreshToken(refresh_token):
    token_endpoint = getDiscoveryDocument.token_endpoint
    auth_header = 'Basic ' + stringToBase64(settings.CLIENT_ID + ':' + settings.CLIENT_SECRET)
    headers = {'Accept': 'application/json', 'content-type': 'application/x-www-form-urlencoded',
               'Authorization': auth_header}
    payload = {
        'refresh_token': refresh_token,
        'grant_type': 'refresh_token'
    }
    r = requests.post(token_endpoint, data=payload, headers=headers)
    bearer_raw = json.loads(r.text)

    if 'id_token' in bearer_raw:
        idToken = idToken = bearer_raw['id_token']
    else:
        idToken = None

    return Bearer(bearer_raw['x_refresh_token_expires_in'], bearer_raw['access_token'], bearer_raw['token_type'],
                  bearer_raw['refresh_token'], bearer_raw['expires_in'], idToken=idToken)


def getUserProfile(access_token):
    auth_header = 'Bearer ' + access_token
    headers = {'Accept': 'application/json', 'Authorization': auth_header,
               'accept': 'application/json'}
    r = requests.get(settings.SANDBOX_PROFILE_URL, headers=headers)
    status_code = r.status_code
    response = json.loads(r.text)
    return response, status_code


def createCharge(access_token):
    route = '/quickbooks/v4/payments/charges'
    auth_header = 'Bearer ' + access_token
    headers = {'Authorization': auth_header,
               'Accept': 'application/json',
               'Content-Type': 'application/json',
               'Request-Id': str(uuid.uuid4())}
    payload = {
        "amount": "500.00",
        "capture": True,
        "card": {
            "expYear": "2020",
            "expMonth": "02",
            "address": {
                "region": "VA",
                "postalCode": "20147",
                "streetAddress": "45805 University Drive",
                "country": "US",
                "city": "Ashburn"
            },
            "name": "emulate=0",
            "cvc": "123",
            "number": "5555555555554444"
        },
        "context": {
            "mobile": False,
            "isEcommerce": True
        },
        "currency": "USD"
    }
    json_str = json.dumps(payload)
    json_obj = json.loads(json_str)
    print(json_obj)
    r = requests.post(settings.SANDBOX_PAYMENT_BASEURL + route, headers=headers, json=json_obj)
    status_code = r.status_code
    response = json.loads(r.text)
    return response, status_code


def createInvoice(access_token, companyid):
    route = '/company/' + companyid + '/invoice'
    auth_header = 'Bearer ' + access_token
    headers = {'Authorization': auth_header,
               'Accept': 'application/json',
               'Content-Type': 'application/json',
               'Request-Id': str(uuid.uuid4())}
    invoice = {
        "Line": [
            {
                "Amount": 999.00,
                "DetailType": "SalesItemLineDetail",
                "SalesItemLineDetail": {
                    "ItemRef": {
                        "value": "1",
                        "name": "Services"
                    }
                }
            }
        ],
        "CustomerRef": {
            "value": "60"
        }
    }
    json_str = json.dumps(invoice)
    json_obj = json.loads(json_str)
    print(json_obj)
    r = requests.post(settings.SANDBOX_ACCOUNTING_BASEURL + route, headers=headers, json=json_obj)
    status_code = r.status_code
    response = json.loads(r.text)
    return response, status_code


def showInvoice(access_token, companyid, invoiceid):
    route = '/company/' + companyid + "/invoice/" + invoiceid
    auth_header = 'Bearer ' + access_token
    headers = {'Authorization': auth_header,
               'Accept': 'application/json',
               'Content-Type': 'application/json',
               'Request-Id': str(uuid.uuid4())}
    r = requests.get(settings.SANDBOX_ACCOUNTING_BASEURL + route, headers=headers)
    status_code = r.status_code
    response = json.loads(r.text)
    return response, status_code


def createCustomer(access_token, companyid):
    route = '/company/' + companyid + '/customer'
    auth_header = 'Bearer ' + access_token
    headers = {'Authorization': auth_header,
               'Accept': 'application/json',
               'Content-Type': 'application/json',
               'Request-Id': str(uuid.uuid4())}
    customer = {
        "BillAddr": {
            "Line1": "100 Washington Ave",
            "City": "Rockville",
            "Country": "USA",
            "CountrySubDivisionCode": "MD",
            "PostalCode": "20850"
        },
        "Notes": "Here are other details.",
        "Title": "Mr",
        "GivenName": "Benjamin",
        "MiddleName": "",
        "FamilyName": "Franklin",
        "Suffix": "",
        "FullyQualifiedName": "",
        "CompanyName": "",
        "DisplayName": "",
        "PrimaryPhone": {
            "FreeFormNumber": "(301)585-2018"
        },
        "PrimaryEmailAddr": {
            "Address": "bfranklin@usa.com"
        }
    }
    json_str = json.dumps(customer)
    json_obj = json.loads(json_str)
    print(json_obj)
    r = requests.post(settings.SANDBOX_ACCOUNTING_BASEURL + route, headers=headers, json=json_obj)
    status_code = r.status_code
    response = json.loads(r.text)
    return response, status_code


def showCustomer(access_token, companyid, customerid):
    route = '/company/' + companyid + "/customer/" + customerid
    auth_header = 'Bearer ' + access_token
    headers = {'Authorization': auth_header,
               'Accept': 'application/json',
               'Content-Type': 'application/json',
               'Request-Id': str(uuid.uuid4())}
    r = requests.get(settings.SANDBOX_ACCOUNTING_BASEURL + route, headers=headers)
    status_code = r.status_code
    response = json.loads(r.text)
    return response, status_code


def showAllCustomer(access_token, companyid):
    route = '/company/' + companyid + "/query?query=SELECT * FROM Customer"
    auth_header = 'Bearer ' + access_token
    headers = {'Authorization': auth_header,
               'Accept': 'application/json',
               'Content-Type': 'application/json',
               'Request-Id': str(uuid.uuid4())}
    r = requests.get(settings.SANDBOX_ACCOUNTING_BASEURL + route, headers=headers)
    status_code = r.status_code
    response = json.loads(r.text)
    return response, status_code


def createItem(access_token, companyid):
    route = '/company/' + companyid + '/item'
    auth_header = 'Bearer ' + access_token
    headers = {'Authorization': auth_header,
               'Accept': 'application/json',
               'Content-Type': 'application/json',
               'Request-Id': str(uuid.uuid4())}
    item = {
            "Name": "RNA Sequencing Service",
            "UnitPrice": 1000,
            "IncomeAccountRef": {
                "value": "79",
                "name": "Sales of Product Income"
            },
            "ExpenseAccountRef": {
                "value": "80",
                "name": "Cost of Goods Sold"
            },
            "AssetAccountRef": {
                "value": "81",
                "name": "Inventory Asset"
            },
            "Type": "Inventory",
            "TrackQtyOnHand": True,
            "QtyOnHand": 10,
            "InvStartDate": "2015-01-01"
        }
    json_str = json.dumps(item)
    json_obj = json.loads(json_str)
    print(json_obj)
    r = requests.post(settings.SANDBOX_ACCOUNTING_BASEURL + route, headers=headers, json=json_obj)
    status_code = r.status_code
    response = json.loads(r.text)
    return response, status_code


def showItem(access_token, companyid, itemid):
    route = '/company/' + companyid + "/item/" + itemid
    auth_header = 'Bearer ' + access_token
    headers = {'Authorization': auth_header,
               'Accept': 'application/json',
               'Content-Type': 'application/json',
               'Request-Id': str(uuid.uuid4())}
    r = requests.get(settings.SANDBOX_ACCOUNTING_BASEURL + route, headers=headers)
    status_code = r.status_code
    response = json.loads(r.text)
    return response, status_code


def showAllItem(access_token, companyid):
    route = '/company/' + companyid + "/query?query=SELECT * FROM Item"
    auth_header = 'Bearer ' + access_token
    headers = {'Authorization': auth_header,
               'Accept': 'application/json',
               'Content-Type': 'application/json',
               'Request-Id': str(uuid.uuid4())}
    r = requests.get(settings.SANDBOX_ACCOUNTING_BASEURL + route, headers=headers)
    status_code = r.status_code
    response = json.loads(r.text)
    return response, status_code





"""
    The validation steps can be found at ours docs at developer.intuit.com
"""


def validateJWTToken(token):
    is_valid = True
    current_time = (datetime.utcnow() - datetime(1970, 1, 1)).total_seconds()
    token_parts = token.split('.')
    idTokenHeader = json.loads(base64.b64decode(token_parts[0]).decode('ascii'))
    idTokenPayload = json.loads(base64.b64decode(incorrect_padding(token_parts[1])).decode('ascii'))

    if idTokenPayload['iss'] != settings.ID_TOKEN_ISSUER:
        return False
    elif idTokenPayload['aud'][0] != settings.CLIENT_ID:
        return False
    elif idTokenPayload['exp'] < current_time:
        return False

    token = token.encode()
    token_to_verify = token.decode("ascii").split('.')
    message = token_to_verify[0] + '.' + token_to_verify[1]
    idTokenSignature = base64.urlsafe_b64decode(incorrect_padding(token_to_verify[2]))

    keys = getKeyFromJWKUrl(idTokenHeader['kid'])

    publicKey = jwk.construct(keys)
    return publicKey.verify(message.encode('utf-8'), idTokenSignature)


def getKeyFromJWKUrl(kid):
    jwk_uri = getDiscoveryDocument.jwks_uri
    r = requests.get(jwk_uri)
    if r.status_code >= 400:
        return ''
    data = json.loads(r.text)

    key = next(ele for ele in data["keys"] if ele['kid'] == kid)
    return key


# for decoding ID Token
def incorrect_padding(s):
    return (s + '=' * (4 - len(s) % 4))


def stringToBase64(s):
    return base64.b64encode(bytes(s, 'utf-8')).decode()


"""
    Returns a securely generated random string.
    Source from the django.utils.crypto module.
"""


def getRandomString(length,
                    allowed_chars='abcdefghijklmnopqrstuvwxyz'
                                  'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'):
    return ''.join(random.choice(allowed_chars) for i in range(length))


"""
    Create a random secret key.
    Source from the django.utils.crypto module.
"""


def getSecretKey():
    chars = 'abcdefghijklmnopqrstuvwxyz0123456789'
    return getRandomString(40, chars)
