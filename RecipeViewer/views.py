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
from django.db.models import Q
from django_datatables_view.base_datatable_view import BaseDatatableView

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


#################################################################
#VIEWS
#################################################################

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

def recipeDetails(request, data={}):
    recipe_id = request.GET["recipe_id"]
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

def makeView(request, data={}):
    
    data["title"] = "All Makes"
    if request.GET.__contains__("user"):
        user_id = request.GET["user"]
        username = Users.objects.get(user_id=user_id).username
        data["title"] = "All Makes by " + username
    elif request.GET.__contains__("recipe"):
        recipe_id = request.GET["recipe"]
        title = Recipes.objects.get(recipe_id=recipe_id).title
        data["title"] = "All Makes of " + title
    
    data["nested"] = "makes.html"
    return render(request, "base.html", data)

def recipeView(request, data={}):
    if request.GET.__contains__("ingredient_id"):
        iid = request.GET["ingredient_id"]
        data["title"] = "All Recipes That Use " + Ingredients.objects.get(ingredient_id = iid).name.title()
    elif request.GET.__contains__("author"):
        user_id = request.GET["author"]
        data["title"] = "Recipes by " + Users.objects.get(user_id=user_id).username
    elif request.GET.__contains__("view"):
        if request.GET["view"] == "wcim":
            data["title"] = "What can I make?"
    else:
        data["title"] = "All Recipes"
        data["recipes"] = Recipes.objects.all()
    
    data["nested"] = "recipes.html"
    return render(request, "base.html", data)

def ingredientView(request):
    data={}
    data["nested"] = "ingredients.html"
    return render(request, "base.html", data)

def analyticsView(request, data={}):
    data["nested"] = "analytics.html"
    return render(request, 'base.html', data)

#################################################################
#OTHER HTML RENDERING STUFF
#################################################################

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

def getIngredientRow(request, data={}):    
    number = request.GET["rowIndex"]
    data["rowIndex"] = number
    return render(request, "ingredientRow.html", data)

def ingredientDetails(request, data={}):
    ingredient_id = request.GET["ingredient_id"].split("_")[1]
    data["ingredient"] = Ingredients.objects.get(ingredient_id = ingredient_id)
    return render(request, "ingredientModal.html", data)

def getTopFiveIngByQuant(request, data={}):
    labels = []
    chartData = []

    queryset = Ingredients.objects.order_by('-quantity')[:5]
    for ingredient in queryset:
        labels.append(ingredient.name)
        chartData.append(ingredient.quantity)
    data["labels"] = labels
    data["data"] = chartData
    data["chartID"] = uuid.uuid4()
    return render(request, 'pieChart.html', data)

#################################################################
#OTHER
#################################################################

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

def updateIngredientQuantity(request, data={}):
    ig = Ingredients.objects.get(ingredient_id = request.GET["ingredient_id"])
    ig.quantity=request.GET["newValue"]
    ig.save()
    return HttpResponse()

def theresEnough(ub, ing):
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
    return have>=wanted

def getMakesPerUserGraph(request, data={}):
    print("getMakesPerUser")
    labels = list()
    chartData = list()
    users = dict()
    user_ids = Makes.objects.values("user_id").annotate(entries=Count("user_id"))

    counts = dict()
    for x in user_ids:
        makes = x["entries"]
        if makes in counts:
            counts[makes] += 1
        else:
            counts[makes] = 1   
    dataTobeSorted = list()
    for x in counts:
        dataTobeSorted.append((x, counts[x]))
    dataTobeSorted = sorted(dataTobeSorted)
    mx = max(dataTobeSorted, key=lambda x:x[1])
    
    colors = "["
    for x in dataTobeSorted:
        labels.append(x[0])
        chartData.append(x[1])
        red = 250-x[0]*2
        blue = 0+x[0]*4
        green= 0
        colors += '"#' + f'{red:02x}' + f'{green:02x}' + f'{blue:02x}' + '",'
    colors.strip(",")
    colors += "]"

    data["backgroundColor"] = colors
    data["labels"] = labels
    data["data"] = chartData
    data["chartID"] = uuid.uuid4()
    return render(request, 'barGraph.html', data)

    #counts is now a dict of Makes:How mnay people have that many makes


    #todo:

#top five recipes by review count
def getTFRBRC(request, data={}):
    labels = []
    chartData = []

    queryset = Recipes.objects.order_by('-review_count')[:5]
    for recipe in queryset:
        labels.append(recipe.title)
        chartData.append(recipe.review_count)
    data["labels"] = labels
    data["data"] = chartData
    data["chartID"] = uuid.uuid4()
    return render(request, 'pieChart.html', data)
    
#################################################################
#DATATABLE VIEWS
#################################################################
class makesViewData(BaseDatatableView):
    columns = ["user", "recipe", "datetime", "user_id, ""recipe_id"]
    order_columns = ["user", "recipe", "datetime"]
    model = Makes
    
    def render_column(self, row, column):
        if column == "recipe":
            return row.recipe.title
        if column == "user":
            return row.user.username
        if column == "user_id":
            return row.user.user_id
        if column == "recipe_id":
            return row.recipe.recipe_id
        return super(makesViewData, self).render_column(row, column)

    def filter_queryset(self, qs):

        search = self.request.GET.get('search[value]', None)
        searchType = self.request.GET.get('searchType', None)
        searchTerm = self.request.GET.get('searchTerm', None)
        print(searchType)
        print(searchTerm)
        if searchType == "user":
            print("filtering By User")
            qs = qs.filter(user_id=searchTerm)
        if searchType == "recipe":
            print("filtering by recipe")
            qs = qs.filter(recipe_id=searchTerm)
        if search:
            qs = qs.filter(Q(user__username__icontains=search) | Q(recipe__title__icontains=search) | Q(datetime__icontains=search))
        return qs

class ingredientViewData(BaseDatatableView):
    columns = ["name", "quantity", "unit", "location", "ingredient_id"]
    order_columns = ["name", "quantity", "unit", "location", "ingredient_id"]
    model = Ingredients

    def render_column(self, row, column):
        return super(ingredientViewData, self).render_column(row, column)

    def filter_queryset(self, qs):
        search = self.request.GET.get('search[value]', None)
        if search:
            try:
                theUUID = uuid.UUID(search)
                x = Usedby.objects.filter(ingredient_id=search).values("recipe_id") #this probably won't work
                qs = qs.filter(recipe_id__in=x)
                print("no exception")
            except ValueError as e:
                print("exeption", e)
                x = Usedby.objects.none()
                qs = qs.filter(Q(name__icontains=search))

        return qs

class recipeViewData(BaseDatatableView):
    columns = ["title", "description", "rating", "url", "recipe_id"]
    order_columns = ["title", "description", "rating", "url", "recipe_id"]
    model = Recipes

    def render_column(self, row, column):
        return super(recipeViewData, self).render_column(row, column)

    def filter_queryset(self, qs):
        search = self.request.GET.get('search[value]', None)
        searchType = self.request.GET.get('searchType', None)
        searchTerm = self.request.GET.get('searchTerm', None)

        if searchType == "ingredient_id" and searchTerm:
            x = Usedby.objects.filter(ingredient_id=searchTerm).values("recipe_id")
            qs = qs.filter(recipe_id__in=x)
        elif searchType == "author" and searchTerm:
            qs = qs.filter(user_id=searchTerm)
        elif search:
            qs = qs.filter(Q(title__icontains=search)|Q(description__icontains=search))
        elif searchType == "wcim":
            recipes = dict()
            
            for r in qs:
                recipes[r.recipe_id] = [r, True]
                
            for u in Usedby.objects.all().select_related("ingredient"):
                i = u.ingredient
                if not theresEnough(u, i):
                    recipes[u.recipe_id][1] = False
                    
            actualList = list()
            for r in recipes.values():
                if r[1]:
                    actualList.append(r[0].recipe_id)
            qs = qs.filter(recipe_id__in=actualList)
        return qs



