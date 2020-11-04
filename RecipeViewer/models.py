['manage.py', 'inspectdb']
# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models
from django.contrib.postgres.fields import ArrayField


class Users(models.Model):
    user_id = models.UUIDField(primary_key=True)
    username = models.TextField(blank=True, null=True)

    # def random(self, howMany):
    #     count = self.aggregate(count=Count("user_id"))["count"]
    #     toReturn = list()
    #     for x in range(howMany):
    #         randomIndex = random.randint(0, count-1)
    #         toReturn.append(self.all()[randomIndex])
    #     return toReturn

    class Meta:
        managed = True
        db_table = 'users'
class Ingredients(models.Model):
    location = models.TextField()
    name = models.TextField(unique=True)
    ingredient_id = models.UUIDField(primary_key=True)
    unit = models.TextField()
    quantity = models.FloatField()

    class Meta:
        managed = True
        db_table = 'ingredients'




class Recipes(models.Model):
    recipe_id = models.UUIDField(primary_key=True)
    user = models.ForeignKey('Users', models.DO_NOTHING)
    cook_time_minutes = models.IntegerField()
    description = models.TextField()
    footnotes = ArrayField(models.TextField())
    instructions = ArrayField(models.TextField())
    photo_url = models.TextField()
    prep_time_minutes = models.IntegerField()
    rating_stars = models.FloatField()
    review_count = models.IntegerField()
    title = models.TextField()
    total_time_minutes = models.IntegerField()
    url = models.TextField()

    # def random(self, howMany):
    #     count = self.aggregate(count=Count("recipe_id"))["count"]
    #     toReturn = list()
    #     for x in range(howMany):
    #         randomIndex = random.randint(0, count-1)
    #         toReturn.append(self.all()[randomIndex])
    #     return toReturn


    class Meta:
        managed = True
        db_table = 'recipes'


class Makes(models.Model):
    meal_id = models.UUIDField(primary_key=True)
    datetime = models.DateTimeField(unique=True)
    user = models.OneToOneField('Users', models.DO_NOTHING)
    recipe = models.OneToOneField('Recipes', models.DO_NOTHING)

    class Meta:
        managed = True
        db_table = 'makes'
        

class Usedby(models.Model):
    used_ingredient_id = models.UUIDField(primary_key=True)
    recipe = models.ForeignKey(Recipes, models.DO_NOTHING)
    ingredient = models.ForeignKey(Ingredients, models.DO_NOTHING)
    unit = models.TextField()
    quantity = models.FloatField()

    class Meta:
        managed = True
        db_table = 'usedby'



class Testtable2(models.Model):
    a = models.TextField(blank=True, null=True)
    b = models.IntegerField(blank=True, null=True)
    the_id = models.UUIDField(primary_key=True)
    tt3_id = models.TextField(blank=True, null=True)  # This field type is a guess.

    class Meta:
        managed = True
        db_table = 'testtable2'


class Testtable3(models.Model):
    my_id = models.UUIDField(primary_key=True)
    value = models.TextField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'testtable3'
