import random
import string

from recipes.models import ShortLink


string.ascii_letters = (
    'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')


def check_shortlink(recipe, shortlink):
    if ShortLink.objects.filter(shortlink=shortlink).exists():
        return False
    if ShortLink.objects.filter(recipe=recipe).exists():
        return False
    return True


def create_shortlink(recipe):
    flag_unique = False
    while not flag_unique:
        shortlink = ''.join(random.choice(
            string.ascii_letters) for x in range(3))
        if check_shortlink(recipe, shortlink):
            break
    obj = ShortLink.objects.create(recipe=recipe, shortlink=shortlink)
    obj.save


def sum_ingredients(recipes_in_user_shopping_cart):
    ingr_dict = {}
    for recipe in recipes_in_user_shopping_cart:
        for ingr in recipe.recipe.recipes.annotate():
            if ((ingr.ingredient.name + ', '
                 + ingr.ingredient.measurement_unit)
                    in ingr_dict.keys()):
                ingr_dict[ingr.ingredient.name + ', '
                          + ingr.ingredient.measurement_unit] += ingr.amount
            else:
                ingr_dict[ingr.ingredient.name + ', '
                          + ingr.ingredient.measurement_unit] = ingr.amount
    return ingr_dict
