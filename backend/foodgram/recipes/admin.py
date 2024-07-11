from django.contrib import admin

from . import models


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
    list_display = ('pk', 'name', 'author', 'in_favorited')
    list_editable = (
        'name', 'cooking_time', 'text', 'tags',
        'image', 'author'
    )
    readonly_fields = ('in_favorites',)
    list_filter = ('name', 'author', 'tags')

    @admin.display(description='В избранном')
    def in_favorited(self, obj):
        return obj.favorite_recipe.count()


@admin.register(models.IngredientInRecipe)
class IngredientInRecipeAdmin(admin.ModelAdmin):
    list_display = ('pk', 'recipe', 'ingredient', 'amount')
    list_editable = ('recipe', 'ingredient', 'amount')


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
