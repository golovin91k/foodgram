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


def sum_ingredients(recipes_in_user_shopping_cart):
    ingr_dict = {}
    for recipe in recipes_in_user_shopping_cart:
        for _ in recipe.recipes.select_related('ingredient').all():
            if ((_.ingredient.name + ', '
                 + _.ingredient.measurement_unit) in ingr_dict.keys()):
                ingr_dict[_.ingredient.name + ', '
                          + _.ingredient.measurement_unit] += _.amount
            else:
                ingr_dict[_.ingredient.name + ', '
                          + _.ingredient.measurement_unit] = _.amount
    return ingr_dict


"""
categories = Category.objects.prefetch_related(
    Prefetch('product_set', queryset=Product.objects.prefetch_related(
        'productimage_set'))
)


def sum_ingredients(recipes_in_user_shopping_cart):
    ingr_dict = {}
    for recipe in recipes_in_user_shopping_cart:
        print('444444444444444444444444444444444444444444444444444444444444444')
        print(type(recipe))
        print(recipe.recipe)
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
"""
