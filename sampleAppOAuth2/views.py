from django.shortcuts import render
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseServerError
from django.shortcuts import redirect
from sampleAppOAuth2.services import *
from sampleAppOAuth2 import getDiscoveryDocument
import urllib
# from django.template import Context, Template
# from django.apps import apps


# Create your views here.
def index(request):
    return render(request, 'index.html')


def connectToQuickbooks(request):
    url = getDiscoveryDocument.auth_endpoint
    scope = ' '.join(settings.PAYMENTS_SCOPE)
    params = {'scope': scope, 'redirect_uri': settings.REDIRECT_URI,
              'response_type': 'code', 'state': get_CSRF_token(request), 'client_id': settings.CLIENT_ID}
    url += '?' + urllib.parse.urlencode(params)
    return redirect(url)


def signInWithIntuit(request):
    url = getDiscoveryDocument.auth_endpoint
    scope = ' '.join(settings.OPENID_SCOPES)  # Scopes are required to be sent delimited by a space
    params = {'scope': scope, 'redirect_uri': settings.REDIRECT_URI,
              'response_type': 'code', 'state': get_CSRF_token(request), 'client_id': settings.CLIENT_ID}
    url += '?' + urllib.parse.urlencode(params)
    return redirect(url)


def getAppNow(request):
    url = getDiscoveryDocument.auth_endpoint
    scope = ' '.join(settings.GET_APP_SCOPES)  # Scopes are required to be sent delimited by a space
    params = {'scope': scope, 'redirect_uri': settings.REDIRECT_URI,
              'response_type': 'code', 'state': get_CSRF_token(request), 'client_id': settings.CLIENT_ID}
    url += '?' + urllib.parse.urlencode(params)
    return redirect(url)


def authCodeHandler(request):
    print("here!")
    state = request.GET.get('state', None)
    error = request.GET.get('error', None)
    if error == 'access_denied':
        return redirect('index')
    if state is None:
        return HttpResponseBadRequest()
    # elif state != get_CSRF_token(request):  # validate against CSRF attacks
    #     print("here 2 ......!")
    #     return HttpResponse('unauthorized', status=401)

    auth_code = request.GET.get('code', None)
    if auth_code is None:
        return HttpResponseBadRequest()

    bearer = getBearerToken(auth_code)
    realmId = request.GET.get('realmId', None)
    updateSession(request, bearer.accessToken, bearer.refreshToken, realmId)

    # Validate JWT tokens only for OpenID scope
    if bearer.idToken is not None:
        if not validateJWTToken(bearer.idToken):
            return HttpResponse('JWT Validation failed. Please try signing in again.')
        else:
            return redirect('connected')
    else:
        return redirect('connected')


def connected(request):
    access_token = request.session.get('accessToken', None)
    if access_token is None:
        return HttpResponse('Your Bearer token has expired, please initiate Sign In With Intuit flow again')

    refresh_token = request.session.get('refreshToken', None)
    realmId = request.session['realmId']
    if realmId is None:
        user_profile_response, status_code = getUserProfile(access_token)

        if status_code >= 400:
            # if call to User Profile Service doesn't succeed then get a new bearer token from
            # refresh token and try again
            bearer = getBearerTokenFromRefreshToken(refresh_token)
            user_profile_response, status_code = getUserProfile(bearer.accessToken)
            updateSession(request, bearer.accessToken, bearer.refreshToken, request.session.get('realmId', None),
                          name=user_profile_response.get('givenName', None))

            if status_code >= 400:
                return HttpResponseServerError()
        c = {
            'first_name': user_profile_response.get('givenName', ' '),
        }
    else:
        if request.session.get('name') is None:
            name = ''
        else:
            name = request.session.get('name')
        c = {
            'first_name': name,
        }

    return render(request, 'connected.html', context=c)


def disconnect(request):
    access_token = request.session.get('accessToken', None)
    refresh_token = request.session.get('refreshToken', None)

    revoke_response = ''
    if access_token is not None:
        revoke_response = revokeToken(access_token)
    elif refresh_token is not None:
        revoke_response = revokeToken(refresh_token)
    else:
        return HttpResponse('No accessToken or refreshToken found, Please connect again')

    request.session.flush()
    return HttpResponse(revoke_response)


def refreshTokenCall(request):
    refresh_token = request.session.get('refreshToken', None)
    if refresh_token is None:
        return HttpResponse('Not authorized')
    first_name = request.session.get('name', None)
    bearer = getBearerTokenFromRefreshToken(refresh_token)

    if isinstance(bearer, str):
        return HttpResponse(bearer)
    else:
        return HttpResponse('Access Token: ' + bearer.accessToken + ', Refresh Token: ' + bearer.refreshToken)


def apiCall(request):
    access_token = request.session.get('accessToken', None)
    if access_token is None:
        return HttpResponse('Your Bearer token has expired, please initiate C2QB flow again')

    realmId = request.session['realmId']
    if realmId is None:
        return HttpResponse('No realm ID. QBO calls only work if the payment scope was passed!')

    refresh_token = request.session['refreshToken']
    create_charge_response, status_code = createCharge(access_token)
    print(create_charge_response)
    print(status_code)

    if status_code >= 400:
        # if call to QBO doesn't succeed then get a new bearer token from refresh token and try again
        bearer = getBearerTokenFromRefreshToken(refresh_token)
        updateSession(request, bearer.accessToken, bearer.refreshToken, realmId)
        create_charge_response, status_code = createCharge(bearer.accessToken)
        if status_code >= 400:
            return HttpResponseServerError()
    return HttpResponse('Charge create response: ' + str(create_charge_response))


# Invoice CRUD

def newInvoice(request):
    access_token = request.session.get('accessToken', None)
    if access_token is None:
        return HttpResponse('Your Bearer token has expired, please initiate C2QB flow again')

    realmId = request.session['realmId']
    if realmId is None:
        return HttpResponse('No realm ID. QBO calls only work if the payment scope was passed!')

    refresh_token = request.session['refreshToken']
    create_invoice_response, status_code = createInvoice(access_token, realmId)
    print(create_invoice_response)
    print(status_code)

    if status_code >= 400:
        # if call to QBO doesn't succeed then get a new bearer token from refresh token and try again
        bearer = getBearerTokenFromRefreshToken(refresh_token)
        updateSession(request, bearer.accessToken, bearer.refreshToken, realmId)
        create_invoice_response, status_code = createInvoice(bearer.accessToken, realmId)
        if status_code >= 400:
            return HttpResponseServerError()
    return HttpResponse('Invoice create response: ' + str(create_invoice_response))


def oneInvoice(request):
    access_token = request.session.get('accessToken', None)
    if access_token is None:
        return HttpResponse('Your Bearer token has expired, please initiate C2QB flow again')

    realmId = request.session['realmId']
    if realmId is None:
        return HttpResponse('No realm ID. QBO calls only work if the payment scope was passed!')

    invoiceid = 60

    refresh_token = request.session['refreshToken']
    show_invoice_response, status_code = showInvoice(access_token, realmId, invoiceid)
    print(show_invoice_response)
    print(status_code)

    if status_code >= 400:
        # if call to QBO doesn't succeed then get a new bearer token from refresh token and try again
        bearer = getBearerTokenFromRefreshToken(refresh_token)
        updateSession(request, bearer.accessToken, bearer.refreshToken, realmId)
        create_charge_response, status_code = showInvoice(bearer.accessToken, realmId)
        if status_code >= 400:
            return HttpResponseServerError()
    return HttpResponse('Query Item response: ' + str(show_invoice_response))


# Customer CRUD

def newCustomer(request):
    access_token = request.session.get('accessToken', None)
    if access_token is None:
        return HttpResponse('Your Bearer token has expired, please initiate C2QB flow again')

    realmId = request.session['realmId']
    if realmId is None:
        return HttpResponse('No realm ID. QBO calls only work if the payment scope was passed!')

    refresh_token = request.session['refreshToken']
    create_customer_response, status_code = createCustomer(access_token, realmId)
    print(create_customer_response)
    print(status_code)

    if status_code >= 400:
        # if call to QBO doesn't succeed then get a new bearer token from refresh token and try again
        bearer = getBearerTokenFromRefreshToken(refresh_token)
        updateSession(request, bearer.accessToken, bearer.refreshToken, realmId)
        create_customer_response, status_code = createCustomer(bearer.accessToken, realmId)
        if status_code >= 400:
            return HttpResponseServerError()
    return HttpResponse('Invoice create response: ' + str(create_customer_response))


def oneCustomer(request):
    access_token = request.session.get('accessToken', None)
    if access_token is None:
        return HttpResponse('Your Bearer token has expired, please initiate C2QB flow again')

    realmId = request.session['realmId']
    if realmId is None:
        return HttpResponse('No realm ID. QBO calls only work if the payment scope was passed!')

    customerid = "60"

    refresh_token = request.session['refreshToken']
    show_customer_response, status_code = showCustomer(access_token, realmId, customerid)
    print(show_customer_response)
    print(status_code)

    if status_code >= 400:
        # if call to QBO doesn't succeed then get a new bearer token from refresh token and try again
        bearer = getBearerTokenFromRefreshToken(refresh_token)
        updateSession(request, bearer.accessToken, bearer.refreshToken, realmId)
        create_charge_response, status_code = showCustomer(bearer.accessToken, realmId)
        if status_code >= 400:
            return HttpResponseServerError()
    return HttpResponse('Query Item response: ' + str(show_customer_response))


def allCustomer(request):
    access_token = request.session.get('accessToken', None)
    if access_token is None:
        return HttpResponse('Your Bearer token has expired, please initiate C2QB flow again')

    realmId = request.session['realmId']
    if realmId is None:
        return HttpResponse('No realm ID. QBO calls only work if the payment scope was passed!')

    refresh_token = request.session['refreshToken']
    show_all_customer_response, status_code = showAllCustomer(access_token, realmId)
    print(show_all_customer_response)
    print(status_code)

    if status_code >= 400:
        # if call to QBO doesn't succeed then get a new bearer token from refresh token and try again
        bearer = getBearerTokenFromRefreshToken(refresh_token)
        updateSession(request, bearer.accessToken, bearer.refreshToken, realmId)
        create_charge_response, status_code = showAllCustomer(bearer.accessToken, realmId)
        if status_code >= 400:
            return HttpResponseServerError()
    return HttpResponse('Query Customer response: ' + str(show_all_customer_response))


# Service Items CRUD

def newItem(request):
    access_token = request.session.get('accessToken', None)
    if access_token is None:
        return HttpResponse('Your Bearer token has expired, please initiate C2QB flow again')

    realmId = request.session['realmId']
    if realmId is None:
        return HttpResponse('No realm ID. QBO calls only work if the payment scope was passed!')

    refresh_token = request.session['refreshToken']
    create_item_response, status_code = createItem(access_token, realmId)
    print(create_item_response)
    print(status_code)

    if status_code >= 400:
        # if call to QBO doesn't succeed then get a new bearer token from refresh token and try again
        bearer = getBearerTokenFromRefreshToken(refresh_token)
        updateSession(request, bearer.accessToken, bearer.refreshToken, realmId)
        create_charge_response, status_code = createItem(bearer.accessToken, realmId)
        if status_code >= 400:
            return HttpResponseServerError()
    return HttpResponse('Item Create response: ' + str(create_item_response))


def allItem(request):
    access_token = request.session.get('accessToken', None)
    if access_token is None:
        return HttpResponse('Your Bearer token has expired, please initiate C2QB flow again')

    realmId = request.session['realmId']
    if realmId is None:
        return HttpResponse('No realm ID. QBO calls only work if the payment scope was passed!')

    refresh_token = request.session['refreshToken']
    show_all_item_response, status_code = showAllItem(access_token, realmId)
    print(show_all_item_response)
    print(status_code)

    if status_code >= 400:
        # if call to QBO doesn't succeed then get a new bearer token from refresh token and try again
        bearer = getBearerTokenFromRefreshToken(refresh_token)
        updateSession(request, bearer.accessToken, bearer.refreshToken, realmId)
        create_charge_response, status_code = showAllItem(bearer.accessToken, realmId)
        if status_code >= 400:
            return HttpResponseServerError()
    return HttpResponse('Query Item response: ' + str(show_all_item_response))


def oneItem(request):
    access_token = request.session.get('accessToken', None)
    if access_token is None:
        return HttpResponse('Your Bearer token has expired, please initiate C2QB flow again')

    realmId = request.session['realmId']
    if realmId is None:
        return HttpResponse('No realm ID. QBO calls only work if the payment scope was passed!')

    itemid = "1"

    refresh_token = request.session['refreshToken']
    show_item_response, status_code = showItem(access_token, realmId, itemid)
    print(show_item_response)
    print(status_code)

    if status_code >= 400:
        # if call to QBO doesn't succeed then get a new bearer token from refresh token and try again
        bearer = getBearerTokenFromRefreshToken(refresh_token)
        updateSession(request, bearer.accessToken, bearer.refreshToken, realmId)
        create_charge_response, status_code = showItem(bearer.accessToken, realmId)
        if status_code >= 400:
            return HttpResponseServerError()
    return HttpResponse('Query Item response: ' + str(show_item_response))



def get_CSRF_token(request):
    token = request.session.get('csrfToken', None)
    if token is None:
        token = getSecretKey()
        request.session['csrfToken'] = token
    return token


def updateSession(request, access_token, refresh_token, realmId, name=None):
    request.session['accessToken'] = access_token
    request.session['refreshToken'] = refresh_token
    request.session['realmId'] = realmId
    request.session['name'] = name
