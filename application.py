from flask import Flask,render_template, make_response, request, redirect, jsonify, url_for, flash
app = Flask(__name__)

#from sqlalchemy import create_engine
#from sqlalchemy.orm import sessionmaker
#from database_setup import Base
from flask import session as login_session
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
import random
import string
import requests

CLIENT_ID=json.loads(open('client_secret.json','r').read())['web']['client_id']

@app.route('/')
@app.route('/catalog')
def index():
    return render_template('index.html')


@app.route('/login')
def login():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)

@app.route('/recipe/<int:recipe_id>/')
def showRecipe(recipe_id):
    return render_template('viewrecipe.html')

@app.route('/recipe/create')
@app.route('/create')
def newRecipe():
    return render_template('createrecipe.html')

@app.route('/recipe/<int:recipe_id>/edit')
def editRecipe(recipe_id):
    return render_template('createrecipe.html')

@app.route('/recipe/<int:recipe_id>/delete')
def deleteRecipe(recipe_id):
    return "This is to delete recipe %s" % recipe_id



@app.route('/gconnect', methods=['POST'])
def gconnect():
    if request.args.get('state') != login_session['state']:
        response =  make_response(json.dumps('Invalid State Token Error'),401)
        print "invalid"
        response.headers['Content-Type']= 'application/json'
        return response
    else:
        code = request.data
        try:
            oauth_flow=flow_from_clientsecrets('client_secret.json', scope='')
            oauth_flow.redirect_uri='postmessage'
            credentials = oauth_flow.step2_exchange(code)
        except FlowExchangeError:
            response= make_response(json.dumps('Failed to upgrade authroization code'),401)
            response.headers['Content-Type']= 'application/json'
            print "flow"
            return response
        access_token= credentials.access_token
        url=('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
        h= httplib2.Http()
        result=json.loads(h.request(url,'GET')[1])
        if result.get('error') is not None:
            response = make_response(json.dumps(result.get('error')),500)
            response.headers['Content-Type']='application/json'
        googleid= credentials.id_token['sub']
        if result['user_id'] != googleid:
            response = make_response(json.dumps("Token and User ID dont match"),401)
            response.headers['Content-Type']='application/json'
            print "tu"
            return response
        if result['issued_to'] != CLIENT_ID:
            response = make_response(json.dumps("Token and Client ID dont match"),401)
            response.headers['Content-Type']='application/json'
            print "tc"
            return response
        stored_credentials = login_session.get('credentials')
        stored_gplus_id = login_session.get('googleid')
        if stored_credentials is not None and googleid == stored_gplus_id:
            response = make_response(json.dumps('Current user is already connected.'),
                                 200)
            response.headers['Content-Type'] = 'application/json'
            return response
        login_session['credentials'] = credentials
        login_session['googleid'] = googleid

        # Get user info
        userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
        params = {'access_token': credentials.access_token, 'alt': 'json'}
        answer = requests.get(userinfo_url, params=params)

        data = answer.json()

        login_session['username'] = data['name']
        login_session['picture'] = data['picture']
        login_session['email'] = data['email']

        output = ''
        output += '<h1>Welcome, '
        output += login_session['username']
        output += '!</h1>'
        output += '<img src="'
        output += login_session['picture']
        output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
        flash("you are now logged in as %s" % login_session['username'])
        print "done!"
        return output


@app.route('/gdisconnect')
def gdisconnect():
    credentials= login_session.get('credentials')
    if credentials is None:
        response = make_response(json.dumps('Current user not connected'),401)
        response.headers['Content-Type']='application/json'
        return response
    access_token= credentials.access_token
    url('https://accounts.google.com/o/oauth2/revoke?token=%s'%access_token)
    h= httplib2.Http()
    result = h.request(url,'GET')[0]

    if result['status'] == '200':
        del login_session['access_token']
    	del login_session['gplus_id']
    	del login_session['username']
    	del login_session['email']
    	del login_session['picture']
    	response = make_response(json.dumps('Successfully disconnected.'), 200)
    	response.headers['Content-Type'] = 'application/json'
    	return response
    else:

    	response = make_response(json.dumps('Failed to revoke token for given user.', 400))
    	response.headers['Content-Type'] = 'application/json'
    	return response

if __name__ == '__main__':
  app.secret_key = 'super_secret_key'
  app.debug= True
  app.run(host = '0.0.0.0', port=5000)
