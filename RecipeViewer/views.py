from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ObjectDoesNotExist
from .models import Recipes, Ingredients, Users, Usedby, Makes
import uuid
from django.utils import timezone
from django.http import JsonResponse
from django.db.models.aggregates import Count
from django.db.models import Prefetch

import random
import datetime

VOLUME_UNITS = {
    "mililiter":1,
    "teaspoon":4.92892,
    "tablespoon":14.7868,
    "fluid ounce":29.5735,
    "cup":236.588,
    "pint":473.176,
    "quart":946.353,
    "liter":1000,
    "gallon":3785.41
}
WEIGHT_UNITS = {
    "ounce":1,
    "pound":16
}


def getRandomDates(count):
    dates = list()
    for i in range(count):
        year = random.randint(2010, 2020)
        month = random.randint(1, 12)
        day = random.randint(1, 28)
        hour = random.randint(0, 23)
        minute = random.randint(0, 59)
        second = random.randint(0, 59)
        t = timezone.make_aware(timezone.datetime(year, month, day, hour, minute, second))
        dates.append(t)
    return dates

        



@csrf_exempt
def generateMakesView(request, data={}):
    data["good"] = "False"
    print("generateMakesView")
    try:
        if request.method == "POST":
            print("it's a post")
            howMany = int(request.POST["makeCount"])
            for k in range(int(howMany/100)+1):
                print("doing the", k, "th howmany")
                randRecipes = list()
                count = Recipes.objects.aggregate(count=Count("recipe_id"))["count"]
                for x in range(100):
                    print("getting recipe", x)
                    randomIndex = random.randint(0, count-1)
                    randRecipes.append(Recipes.objects.all()[randomIndex])
                
                randUsers = list()
                count = Users.objects.aggregate(count=Count("user_id"))["count"]
                for x in range(100):
                    print("getting user",x)
                    randomIndex = random.randint(0, count-1)
                    randUsers.append(Users.objects.all()[randomIndex])

                dates = getRandomDates(count)

                for i in range(100):
                    print("i:",i)
                    m = Makes(
                        meal_id=uuid.uuid4(),
                        datetime=dates[i],
                        user = randUsers[i],
                        recipe=randRecipes[i])
                    m.save()
                    
            data["good"] = "True"
    except Exception as e:
        print(e)
        data["good"] = "False"
    data["nested"] = "generateMakesView.html"
    return render(request, "base.html", data)


def getIngredientRow(request, data={}):
    
    number = request.GET["rowIndex"]
    data["rowIndex"] = number
    return render(request, "ingredientRow.html", data)
    

@csrf_exempt
def makeRecipe(request, data={}):
    ings = request.POST.getlist("ingredients[][]")
    try:
        for x in ings:
            spl = x.split(",")
            iid = spl[0]
            ("iid:" + iid)
            quant = float(spl[1])
            ingred = Ingredients.objects.get(ingredient_id = iid)
            ingred.quantity -= quant
            ingred.save()
        try:
            user=Users.objects.get(username = request.POST["username"])
        except ObjectDoesNotExist as e:
            user = Users(username=request.POST["username"], user_id = uuid.uuid4())
            user.save()
        
        date = request.POST["date"].split("-")
        year = int(date[0])
        month = int(date[1])
        day = int(date[2])
        time = request.POST["time"].split(":")
        hour = int(time[0])
        minute = int(time[1])
        theDateTime = timezone.datetime(year, month,day, hour, minute)
        theDateTime = timezone.make_aware(theDateTime)

        m = Makes(meal_id = uuid.uuid4(),
                user=user,
                recipe=Recipes.objects.get(recipe_id = request.POST["recipe_id"]),
                datetime = theDateTime)
        m.save()
        return HttpResponse(True)
    except Exception as e:
        print("exception")
        print(e)
        return HttpResponse(False)


def getIngredientExists(request, data={}):
    result = {}
    exists = Ingredients.objects.filter(name=request.GET["ingName"]).exists()
    unit = ""
    location=""
    if(exists):
        unit = Ingredients.objects.get(name=request.GET["ingName"]).unit
        location = Ingredients.objects.get(name=request.GET["ingName"]).location
        print("loc:",location)
    return JsonResponse({"exists":exists, "unit":unit, "location":location})

def getIngredientQuantity(request, data={}):
    try:
        iid = request.GET["ingredient_id"]
        quant = Ingredients.objects.get(ingredient_id = iid).quantity
    except:
        quant = -1
        
    return HttpResponse(quant)



@csrf_exempt
def addRecipe(request, data={}):

    data["message"] = [True, ""]
    if request.method == "POST":
        try:
            if(Users.objects.filter(username=request.POST["username"]).exists()):
                user = Users.objects.get(username=request.POST["username"])
            else:
                user = Users(username=request.POST["username"], user_id = uuid.uuid4())
                user.save()

            imageURL = request.POST["imageURL"]
            if imageURL=="":
                imageURL = "http://images.media-allrecipes.com/global/recipes/nophoto/nopicture-910x511.png"
            r = Recipes(recipe_id = uuid.uuid4(),
                    user=user,
                    cook_time_minutes=request.POST["cookTime"],
                    description=request.POST["description"],
                    footnotes=(),
                    instructions = request.POST["instructions"].split("\n"),
                    photo_url = imageURL,
                    prep_time_minutes= request.POST["prepTime"],
                    rating_stars = request.POST["rating"],
                    review_count = request.POST["reviewCount"],
                    title = request.POST["title"],
                    total_time_minutes = request.POST["totalTime"],
                    url = request.POST["url"])
            r.save()

            for x in request.POST.getlist("ingredients[]"):
                print(x)
                [name, unit, quantity, location] = x.split("_")
                if unit == "each":
                    unit = ""
                if Ingredients.objects.filter(name=name).exists():
                    ing = Ingredients.objects.get(name=name);
                else:
                    ing = Ingredients(name=name, unit=unit, quantity=quantity, location=location.lower(), ingredient_id = uuid.uuid4())
                    ing.save()
                ub = Usedby(used_ingredient_id = uuid.uuid4(), 
                        recipe = r,
                        ingredient = ing,
                        unit = unit,
                        quantity = quantity)
                ub.save()
            return HttpResponse(True)
        except Exception as e:
            print(e)
            return HttpResponse(False)
        
    else:
        data["ingredientNames"] = Ingredients.objects.values_list('name', flat=True)
        data["recipenames"] = Recipes.objects.values_list("title", flat=True)
        data["usernames"] = Users.objects.values_list('username', flat=True)
        data["nested"] = "addRecipe.html"
        return render(request, "base.html", data)



@csrf_exempt
def addIngredient(request, data={}):

    if request.method == "POST":
        name = request.POST["name"]
        quantity = request.POST["quantity"]
        unit = request.POST["unit"]
        location = request.POST["location"].lower()
        nameGood=False
        try:
            Ingredients.objects.get(name = name)
        except ObjectDoesNotExist as e:
            nameGood=True
            print(e)
        if nameGood:
            x = Ingredients(name=name, quantity=quantity, unit=unit, location=location, ingredient_id = uuid.uuid4())
            x.save()
            data["message"]= ("green", "Ingredient Created Successfully")
        else:
            data["message"]= ("red", "Ingredient Already Exists. Please choose a different name.")

    data["usedNames"] = Ingredients.objects.values_list('name', flat=True)
    data["locationNames"] = Ingredients.objects.values_list('location', flat=True).distinct()

    data["nested"] = "addIngredient.html"
    return render(request, "base.html", data)

def updateIngredientQuantity(request, data={}):
    ig = Ingredients.objects.get(ingredient_id = request.GET["ingredient_id"])
    ig.quantity=request.GET["newValue"]
    ig.save()
    return HttpResponse()

def ingredientDetails(request, data={}):
    ingredient_id = request.GET["ingredient_id"].split("_")[1]
    data["ingredient"] = Ingredients.objects.get(ingredient_id = ingredient_id)
    return render(request, "ingredientModal.html", data)

def recipeDetails(request, data={}):

    recipe_id = request.GET["recipe_id"].split("_")[1]
    data["recipe"] = Recipes.objects.get(recipe_id=recipe_id)
    data["recipe"].title = data["recipe"].title.title()
    ingredients = Usedby.objects.filter(recipe=recipe_id)
    pantry = list()
    for x in ingredients:
        pantry.append(x.ingredient)
    data["ingredients"] = zip(ingredients, pantry)
    data["instructions"] = data["recipe"].instructions.split('"')[1::2]

    data["usernames"] = Users.objects.values_list('username', flat=True)

    return render(request, "recipeModal.html", data)

def userView(request, data={}):
    
    users = Users.objects.all()
    threeData = list()
    for u in users:
        recipeCount = Recipes.objects.filter(user = u).count()
        makesCount = Makes.objects.filter(user = u).count()
        threeData.append({"recipeCount":recipeCount, "makesCount":makesCount, "user":u});

    data["threeData"] = threeData
    data["nested"] = "users.html"
    return render(request, "base.html", data)

def makeView(request, data={}):

    if request.GET.__contains__("user_id"):
        if(Users.objects.filter(user_id=request.GET["user_id"]).exists()):
            user = Users.objects.get(user_id=request.GET["user_id"])
            makes = Makes.objects.filter(user = user)
            makes = makes
            data["title"] = "All Makes By " + user.username
        else:
            data["title"] = "All Makes"
            # makes = Makes.objects.all().prefetch_related(Prefetch("recipes", to_attr="title")).select_related("user")#TODO HERETODAY   
            makes = Makes.objects.all()
    else:
        data["title"] = "All Makes"
        makes = Makes.objects.all()
    threeData = list()
    for x in makes:
        threeData.append({"date":x.datetime,"title":x.recipe.title, "recipe_id":x.recipe.recipe_id, "username":x.user.username, "user_id":x.user.user_id})

    data["threeData"] = threeData
    data["nested"] = "makes.html"
    return render(request, "base.html", data)

def theresEnough(ub, ing):

    try:
        have = ing.quantity
        haveUnit = ing.unit

        wanted = ub.quantity
        wantedUnit = ub.unit

        if wantedUnit == haveUnit:
            return have >= wanted
        elif wantedUnit in VOLUME_UNITS and haveUnit in VOLUME_UNITS:
            have = have*VOLUME_UNITS[haveUnit]/VOLUME_UNITS[wantedUnit];
        elif wantedUnit in WEIGHT_UNITS and haveUnit in WEIGHT_UNITS:
            have = have*WEIGHT_UNITS[haveUnit]/WEIGHT_UNITS[wantedUnit];
    except:
        print("exception")
        print("have:",have)
        print("haveunit:",haveUnit)
        print("wanted:",wanted)
        print("wantedUnit",wantedUnit)

    return have>=wanted

def recipeView(request, data={}):
    if request.GET.__contains__("ingredient_id"):
        iid = request.GET["ingredient_id"]
        print("hi")
        usedbys = Usedby.objects.filter(ingredient_id = iid)
        recipes=list()
        for u in usedbys:
            recipes.append(u.recipe)
        data["recipes"] = recipes
        data["title"] = "All Recipes That Use " + Ingredients.objects.get(ingredient_id = iid).name.title()
    elif request.GET.__contains__("view"):
        if request.GET["view"] == "wcim":
            recipes = dict()
            print("start")
            for r in Recipes.objects.all():
                recipes[r.recipe_id] = [r, True]
            print("step 1")
            ingredients = Ingredients.objects.all()
            print("step 1.1")
            for u in Usedby.objects.all().select_related("ingredient"):
                i = u.ingredient
                if not theresEnough(u, i):
                    recipes[u.recipe_id][1] = False
            print("step 2")
            actualList = list()
            for r in recipes.values():
                if r[1]:
                    actualList.append(r[0])
            print("step 3")
            data["recipes"] = actualList
            data["title"] = "What can I make?"
    else:
        data["title"] = "All Recipes"
        data["recipes"] = Recipes.objects.all()
    
    data["nested"] = "recipes.html"
    return render(request, "base.html", data)

def ingredientView(request):
    data={}

    data["name"] = "noah"
    data["ingredients"] = Ingredients.objects.all()
    data["nested"] = "ingredients.html"

    return render(request, "base.html", data)
# Create your views here.
