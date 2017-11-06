from __future__ import print_function
import sys
import httplib2
import json
import random
import string
import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Recipe
from database_setup import Categories, IngredientList, Steps
from flask import session as login_session
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
from flask import Flask, render_template, make_response
from flask import request, g, redirect, jsonify, url_for, flash
from functools import wraps
app = Flask(__name__)

CLIENT_ID = json.loads(
                    open('client_secret.json', 'r').read())['web']['client_id']

# Connect to Database and create database session
engine = create_engine('postgresql:///catalog')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate State token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid State Token Error'), 401)
        print ("invalid")
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data
    try:
        # Upgrade the authroization code
        oauth_flow = flow_from_clientsecrets('client_secret.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(json.dumps(
            'Failed to upgrade authroization code'), 401)
        response.headers['Content-Type'] = 'application/json'

        return response
    # Check if access token is valid
    access_token = credentials.access_token
    url = 'https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' \
        % access_token
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If error abort
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
    gplus_id = credentials.id_token['sub']
    # Verify the access token is used for the intended user
    if result['user_id'] != gplus_id:
        response = make_response(json.dumps(
            "Token and User ID dont match"), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Verify that the access token is valid for this application
    if result['issued_to'] != CLIENT_ID:
        response = make_response(json.dumps(
            "Token and Client ID dont match"), 401)
        response.headers['Content-Type'] = 'application/json'

        return response
    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(
                                json.dumps
                                ('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Store access token for later use
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    user_id = getUserId(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px;"'
    output += "height: 300px;border-radius: 150px;"
    output += "-webkit-border-radius: 150px;"
    output += '-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print ("done!")
    return output


@app.route('/gdisconnect', methods=['GET', 'POST'])
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(json.dumps('Current user not connected'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' \
        % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

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

        response = make_response(json.dumps(
            'Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response

    return redirect(url_for('index'))


def createUser(login_session):
    newUser = User(name=login_session['username'],
                   email=login_session['email'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter(
        User.email == login_session['email']).one()
    return user.id


def getuserinfo(user_id):
    user = session.query(User).filter(User.id == user_id).one()
    return user


def getUserId(email):
    try:
        user = session.query(User).filter(User.email == email).one()
        return user.id

    except:
        return None


# Home page
@app.route('/', methods=['GET', 'POST'])
@app.route('/catalog')
def index():

    if request.method == 'POST':
        return redirect(url_for('login'))
    else:
        categories = session.query(Categories).all()
        recipes = session.query(Recipe).limit(10).all()
        return render_template(
                                'index.html',
                                categories=categories,
                                recipes=recipes)


# Specific category page
@app.route('/catalog/<path:category>/', methods=['GET',  'POST'])
def category(category):
    if request.method == 'POST':
        return redirect(url_for('login'))
    else:
        categories = session.query(Categories).all()
        find_id = session.query(Categories).\
            filter(Categories.name == category).one()
        category_id = find_id.id
        recipes = session.query(Recipe).\
            filter(Recipe.category_id == category_id).\
            limit(10).all()

        return render_template(
                                'category.html',
                                categories=categories,
                                recipes=recipes,
                                find_id=find_id)


# Create anti-forgery token
@app.route('/login', methods=['GET', 'POST'])
def login():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in login_session:
            return redirect(url_for('login'))
        else:
            return f(*args, **kwargs)
    return decorated_function


def authorization_required(func):
    @wraps(func)
    def authorization(*args, **kwargs):
        userid = getUserId(login_session['email'])

        recipe_id = kwargs['recipe_id']
        try:
            userrecipe = session.query(Recipe).\
                filter(Recipe.user_id == userid).\
                filter(Recipe.id == recipe_id).first()
            uid = userrecipe.user_id
        except:
            uid = 0

        if uid != login_session['user_id']:
            flash("You do not have authorization of this recipe")
            return redirect(url_for('index'))

        else:
            return func(*args, **kwargs)
    return authorization


# View list of all recipes made by the logged in user
@app.route('/myrecipe')
@login_required
def myRecipe():

    userid = getUserId(login_session['email'])
    recipe = session.query(Recipe).filter(Recipe.user_id == userid).all()

    return render_template('myrecipe.html', recipe=recipe)


# View recipe
@app.route('/recipe/<int:recipe_id>/', methods=['GET', 'POST'])
def showRecipe(recipe_id):
    recipe = session.query(Recipe).filter(Recipe.id == recipe_id).first()
    ingredient = session.query(IngredientList).\
        filter(IngredientList.recipe_id == recipe_id).all()
    steps = session.query(Steps).filter(Steps.recipe_id == recipe_id).all()
    cook_time_list = []
    prep_time_list = []
    # Check the time and convert back to hours and minutes
    if recipe.prep_time > 60:
        prep_hours = recipe.prep_time / 60
        prep_minutes = recipe.prep_time % 60
        prep_time_list.append(prep_hours)
        prep_time_list.append(prep_minutes)

    else:
        prep_time_list.append(0)
        prep_time_list.append(recipe.prep_time)

    if recipe.cook_time > 60:

        cook_hours = recipe.cook_time / 60
        cook_minutes = recipe.cook_time % 60
        cook_time_list.append(cook_hours)
        cook_time_list.append(cook_minutes)

    else:
        cook_time_list.append(0)
        cook_time_list.append(recipe.cook_time)

    return render_template(
                            'viewrecipe.html',
                            recipe=recipe,
                            ingredient=ingredient,
                            steps=steps,
                            cook_time=cook_time_list,
                            prep_time=prep_time_list)


# Create Recipe
@app.route('/recipe/create', methods=['GET', 'POST'])
@app.route('/create', methods=['GET', 'POST'])
@login_required
def newRecipe():

    if request.method == 'POST':

        latest_id = session.query(Recipe).order_by(Recipe.id.desc()).first()
        # Get the latest restaurant id to populate Recipe tables
        if latest_id is None:
            idnum = 1
        else:
            idnum = latest_id.id + 1

        categories = request.form['categories'].lower()
        # Check to see if Category exists if not we add it and calculate the id
        if session.query(Categories).\
                filter(Categories.name == categories).count() == 0:
            latest_category_id = session.query(
                Categories).order_by(Categories.id.desc()).first()
            category = Categories(name=categories)
            session.add(category)
            if latest_category_id is None:
                cat_id = 1

            else:
                cat_id = latest_category_id.id + 1

        else:
            category = session.query(Categories).filter(
                Categories.name == categories).first()
            cat_id = category.id

        prep_hours = int(request.form['prep_hours'])
        prep_minutes = int(request.form['prep_minutes'])
        cook_hours = int(request.form['cook_hours'])
        cook_minutes = int(request.form['cook_minutes'])

        preptime = prep_hours * 60 + prep_minutes
        cooktime = cook_hours * 60 + cook_minutes

        newRecipe = Recipe(
                            name=request.form['recipe_name'],
                            description=request.form['description'],
                            prep_time=preptime,
                            cook_time=cooktime,
                            user_id=login_session['user_id'],
                            category_id=cat_id)
        session.add(newRecipe)
        ingredients = request.form['ingredient']
        ingredientlist = ingredients.split("\n")
        ingredientlist[:] = (value for value in ingredientlist if value != "")
        step = request.form['step']

        steplist = step.split("\n")
        steplist[:] = (value for value in steplist if value != "")
        for index in range(len(ingredientlist)):
            ingredient_strip = ingredientlist[index].rstrip('\r')
            ingredient = IngredientList(
                                        ingredient_number=index,
                                        ingredient=ingredient_strip,
                                        recipe_id=idnum)
            print(ingredientlist[index])
            session.add(ingredient)

        for index in range(len(steplist)):
            step_strip = steplist[index].rstrip('\r')
            stepnum = Steps(step_number=index,
                            step_description=step_strip, recipe_id=idnum)
            print (steplist[index])
            session.add(stepnum)

        session.commit()

        flash("Recipe successfully added")
        return redirect(url_for('index'))
    else:
        category = session.query(Categories).all()
        return render_template('createrecipe.html', category=category)


# Edit Recipe
@app.route('/recipe/<int:recipe_id>/edit', methods=['GET', 'POST'])
@login_required
@authorization_required
def editRecipe(recipe_id):

    recipe = session.query(Recipe).filter(Recipe.id == recipe_id).first()
    ingredient = session.query(IngredientList).filter(
        IngredientList.recipe_id == recipe_id).all()
    steps = session.query(Steps).filter(Steps.recipe_id == recipe_id).all()
    category = session.query(Categories).all()
    specific_category = session.query(Categories).filter(
        Categories.id == recipe.category_id).first()

    if request.method == 'POST':

        categories = request.form['categories'].lower()
        if session.query(Categories).\
                filter(Categories.name == categories).count() == 0:
            latest_category_id = session.query(
                Categories).order_by(Categories.id.desc()).first()
            category = Categories(name=categories)
            session.add(category)
            if latest_category_id is None:
                cat_id = 1
                recipe.category_id = cat_id

            else:
                cat_id = latest_category_id.id + 1
                recipe.category_id = cat_id

        recipe.name = request.form['recipe_name']

        recipe.description = request.form['description']

        prep_hours = int(request.form['prep_hours'])
        prep_minutes = int(request.form['prep_minutes'])
        cook_hours = int(request.form['cook_hours'])
        cook_minutes = int(request.form['cook_minutes'])
        preptime = prep_hours * 60 + prep_minutes
        cooktime = cook_hours * 60 + cook_minutes
        recipe.prep_time = preptime
        recipe.cook_time = cooktime

        session.add(recipe)

        ingredient_length_before = len(ingredient)
        steps_length_before = len(steps)

        ingredients = request.form['ingredient']
        ingredientlist = ingredients.split("\n")
        ingredientlist[:] = (value for value in ingredientlist if value != "")
        step = request.form['step']

        steplist = step.split("\n")
        steplist[:] = (value for value in steplist if value != "")
        # Here we check whats been added or deleted and add/delete/modify for
        # both steps and ingredients

        # If the size of the list is bigger than what we first got
        if len(ingredientlist) > ingredient_length_before:
            num_added = len(ingredientlist) - ingredient_length_before
            # Loop through the original size and modify
            for index in range(ingredient_length_before):
                edit_ingredient = session.query(IngredientList).filter(
                    IngredientList.id == ingredient[index].id).one()
                edit_ingredient.ingredient = ingredientlist[index]
                session.add(edit_ingredient)
            # Add the remaining in the database
            for x in range(num_added):
                new_ingredient = IngredientList(
                                ingredient_number=ingredient_length_before + x,
                                ingredient=ingredientlist
                                [ingredient_length_before + x],
                                recipe_id=recipe_id)
                session.add(new_ingredient)
        # If the size of the list is less than before
        elif len(ingredientlist) < ingredient_length_before:

            num_deleted = ingredient_length_before - len(ingredientlist)
            # Loop through and changed based on the size of the altered list
            for index in range(len(ingredientlist)):
                edit_ingredient = session.query(IngredientList).filter(
                    IngredientList.id == ingredient[index].id).one()
                edit_ingredient.ingredient = ingredientlist[index]
                session.add(edit_ingredient)
            # Delete extras
            for x in range(num_deleted):
                delete_item = session.query(IngredientList).\
                    filter(IngredientList.id ==
                           ingredient[len(ingredientlist)].id + x).one()
                session.delete(delete_item)

        else:
            for index in range(len(ingredientlist)):
                edit_ingredient = session.query(IngredientList).filter(
                    IngredientList.id == ingredient[index].id).one()
                edit_ingredient.ingredient = ingredientlist[index]
                session.add(edit_ingredient)

        if len(steplist) > steps_length_before:
            print (len(steplist))
            print (steps_length_before)
            num_added = len(steplist) - steps_length_before
            for index in range(steps_length_before):
                edit_step = session.query(Steps).filter(
                    Steps.step_id == steps[index].step_id).one()
                edit_step.step_description = steplist[index]
                session.add(edit_step)
            for x in range(num_added):
                new_step = Steps(step_number=steps_length_before + x,
                                 step_description=steplist
                                 [steps_length_before + x],
                                 recipe_id=recipe_id)
                print (steplist[steps_length_before + x])
                session.add(new_step)

        elif len(steplist) < steps_length_before:
            num_deleted = steps_length_before - len(steplist)
            for index in range(len(steplist)):
                edit_step = session.query(Steps).filter(
                    Steps.step_id == steps[index].step_id).one()
                edit_step.step_description = steplist[index]
                session.add(edit_step)
            for x in range(num_deleted):
                delete_item = session.query(Steps).\
                    filter(Steps.step_id == steps[len(
                        steplist)].step_id + x).one()
                print(delete_item.step_description)
                session.delete(delete_item)

        else:
            for index in range(len(steplist)):
                edit_step = session.query(Steps).filter(
                    Steps.step_id == steps[index].step_id).one()
                edit_step.step_description = steplist[index]
                session.add(edit_step)

        session.commit()
        flash("Recipe successfully edited")
        return redirect(url_for('index'))
    else:

        cook_time_list = []
        prep_time_list = []

        if recipe.prep_time > 60:
            prep_hours = recipe.prep_time / 60
            prep_minutes = recipe.prep_time % 60
            prep_time_list.append(prep_hours)
            prep_time_list.append(prep_minutes)

        else:
            prep_time_list.append(0)
            prep_time_list.append(recipe.prep_time)

        if recipe.cook_time > 60:

            cook_hours = recipe.cook_time / 60
            cook_minutes = recipe.cook_time % 60
            cook_time_list.append(cook_hours)
            cook_time_list.append(cook_minutes)

        else:
            cook_time_list.append(0)
            cook_time_list.append(recipe.cook_time)

        return render_template(
                            'edit.html',
                            recipe=recipe,
                            ingredient=ingredient,
                            steps=steps,
                            cook_time=cook_time_list,
                            prep_time=prep_time_list,
                            category=category,
                            recipe_id=recipe_id,
                            specific_category=specific_category)


# Delete Recipe
@app.route('/recipe/<int:recipe_id>/delete', methods=['GET', 'POST'])
@login_required
@authorization_required
def deleteRecipe(recipe_id):

    recipe = session.query(Recipe).filter(Recipe.id == recipe_id).one()
    ingredient = session.query(IngredientList).\
        filter(IngredientList.recipe_id == recipe_id).all()
    steps = session.query(Steps).filter(Steps.recipe_id == recipe_id).all()

    if request.method == 'POST':

        if request.form['confirm'] == recipe.name:
            for index in range(len(ingredient)):
                delete_item = session.query(IngredientList).\
                    filter(IngredientList.id == ingredient[index].id).one()
                session.delete(delete_item)

            for index in range(len(steps)):
                delete_item = session.query(Steps).\
                    filter(Steps.step_id == steps[index].step_id).one()
                session.delete(delete_item)

            session.delete(recipe)
            session.commit()
            flash("Recipe successfully deleted")
            return redirect(url_for('index'))

    else:

        return render_template(
                                'delete.html',
                                recipe=recipe,
                                recipe_id=recipe_id)


# JSON Endpoint
@app.route('/recipe/<int:recipe_id>/JSON')
def recipeJSON(recipe_id):
    recipe = session.query(Recipe).filter(Recipe.id == recipe_id).first()
    ingredient = session.query(IngredientList).filter(
        IngredientList.recipe_id == recipe_id).all()
    steps = session.query(Steps).filter(Steps.recipe_id == recipe_id).all()
    category = session.query(Categories).filter(
        Categories.id == recipe.category_id).first()

    return jsonify(
                    Recipe=[
                        [recipe.serialize],
                        [category.serialize],
                        [i.serialize for i in ingredient],
                        [x.serialize for x in steps]])


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
