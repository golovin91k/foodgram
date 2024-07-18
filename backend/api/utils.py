import random
import string

from recipes.models import ShortLink
from recipes.constans import LEN_SHORT_LINK


def check_shortlink(recipe, shortlink):
    return (
        ShortLink.objects.filter(shortlink=shortlink).exists()
        and ShortLink.objects.filter(recipe=recipe).exists())


def create_shortlink(recipe):
    while True:
        shortlink = ''.join(
            random.choice(
                string.ascii_letters + string.digits) for x in range(
                    LEN_SHORT_LINK))
        if not check_shortlink(recipe, shortlink):
            break
    obj = ShortLink.objects.create(recipe=recipe, shortlink=shortlink)
    obj.save


def sum_ingredients(ingredients_in_recipes):
    ingr_dict = {}
    for ingr in ingredients_in_recipes:
        if ((ingr.ingredient.name + ', '
             + ingr.ingredient.measurement_unit) in ingr_dict.keys()):
            ingr_dict[ingr.ingredient.name + ', '
                      + ingr.ingredient.measurement_unit] += ingr.amount
        else:
            ingr_dict[ingr.ingredient.name + ', '
                      + ingr.ingredient.measurement_unit] = ingr.amount
    return ingr_dict
