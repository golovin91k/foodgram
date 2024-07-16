from django.core.exceptions import ValidationError

from .constans import MINIMUM_COOKING_TIME, MINIMUM_AMOUNT


def validate_cooking_time(value):
    if value < MINIMUM_COOKING_TIME:
        raise ValidationError(
            'Время приготовления должно быть не меньше единицы')


def validate_amount(value):
    if value < MINIMUM_AMOUNT:
        raise ValidationError(
            'Количество ингредиента должно быть не меньше единицы')
