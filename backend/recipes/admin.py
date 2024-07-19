from django.contrib import admin

from . import models


class IngredientInRecipe(admin.TabularInline):
    model = models.IngredientInRecipe
    extra = 3


@admin.register(models.Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'slug')
    list_editable = ('name', 'slug')


@admin.register(models.Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'measurement_unit')
    list_filter = ('name', )
    search_fields = ('name', )


@admin.register(models.Recipe)
class RecipeAdmin(admin.ModelAdmin):
    inlines = (IngredientInRecipe,)
    list_display = ('pk', 'name', 'cooking_time',
                    'text', 'image', 'author', 'ingredients')
    list_editable = (
        'name', 'cooking_time', 'text',
        'image', 'author', 'ingredients',
    )
    readonly_fields = ('in_favorited',)
    list_filter = ('name', 'author', 'tags')
    empty_value_display = '-пусто-'

    def ingredients(self, row):
        return ','.join([x.amount for x in row.ingredients.all()])

    @admin.display(description='В избранном')
    def in_favorited(self, obj):
        return obj.favorite_recipe.count()


@admin.register(models.FavoriteRecipe)
class FavoriteRecipeAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'recipe')
    list_editable = ('user', 'recipe')


@admin.register(models.ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'recipe')
    list_editable = ('user', 'recipe')


@admin.register(models.Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('pk', 'author', 'subscriber')
    list_editable = ('author', 'subscriber')


@admin.register(models.ShortLink)
class ShortLinkAdmin(admin.ModelAdmin):
    list_display = ('pk', 'recipe', 'shortlink')
    list_editable = ('recipe', 'shortlink')
