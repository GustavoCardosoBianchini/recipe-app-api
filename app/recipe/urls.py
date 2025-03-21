'''
Urls for recipe apis
'''

from django.urls import(path, include)

from rest_framework.routers import DefaultRouter

from recipe import views


router = DefaultRouter()
router.register('recipe', views.RecipeViewSets)
router.register('tags', views.TagViewsSet)
router.register('ingredients', views.IngredientViewSet)

app_name = 'recipe'

urlpatterns = [
    path('', include(router.urls))
]
