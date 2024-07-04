import random
import string

from django.db import models

from recipes.models import Recipe, ShortLink

string.ascii_letters = (
    'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')


def check_shortlink(recipe, shortlink):
    if ShortLink.objects.filter(shortlink=shortlink) or ShortLink.objects.filter(recipe=recipe):
        return False
    else:
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
