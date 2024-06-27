from django.contrib import admin

# Из модуля models импортируем модель Category...
from .models import Recipe, Tag, Ingredient

# ...и регистрируем её в админке:
admin.site.register(Recipe)
admin.site.register(Tag)
#admin.site.register(IngredientInRecipe)
admin.site.register(Ingredient)