'''
Recipe serializers
'''
from django.template.base import tag_re
from rest_framework import serializers

from core.models import (Recipe, Tag, Ingredient)


class IngredientSerializer(serializers.ModelSerializer):
    '''Serializer for ingredients'''
    class Meta:
        model = Ingredient
        fields = ['id', 'name']
        read_only_fields=['ids']

class TagSerializer(serializers.ModelSerializer):
    """serializer for tags"""

    class Meta:
        model = Tag
        fields = ['id', 'name']
        read_only_fields = ['id']

class RecipeSerializer(serializers.ModelSerializer):
    '''Serializer for recipes'''
    tags = TagSerializer(many=True, required=False)
    ingredients = IngredientSerializer(many=True, required=False)

    class Meta:
        model = Recipe
        fields = ['id', 'title', 'time_minutes', 'price',
                  'link', 'tags', 'ingredients']
        read_only_fields = ['id']  # this way the user can't change the id

    def _get_or_create_tags(self,tags, recipe):
        '''Handle getting or creating tags as neeeded'''
        auth_user = self.context['request'].user
        # get the tag from the db if it exists if not create a new one
        # with **tag we can make the code foolprof, if we add new variables to the tags
        # it won't break the code
        for tag in tags:
            tag_obj, created = Tag.objects.get_or_create(
                user=auth_user,
                **tag,
            )
            recipe.tags.add(tag_obj)

    def _get_or_create_ingredients(self,ingredients, recipe):
        '''Handle getting or creating a new ingredient as needed'''
        auth_user = self.context['request'].user
        for ingredient in ingredients:
            ingredient_obj, created = Ingredient.objects.get_or_create(
                user=auth_user,
                **ingredient,
            )
            recipe.ingredients.add(ingredient_obj)

    def create(self, validated_data):
        '''Create a recipe'''
        # remove se existe e adiciona para tags
        tags = validated_data.pop('tags', [])

        # remove se existe e adiciona para tags
        ingredients = validated_data.pop('ingredients', [])

        recipe = Recipe.objects.create(**validated_data)
        self._get_or_create_tags(tags, recipe)
        self._get_or_create_ingredients(ingredients, recipe)

        return recipe

    # Since its a created object, we will work with it's instance as well
    def update(self, instance, validated_data):
        ''' update recipe'''
        tags = validated_data.pop('tags', None)
        ingredients = validated_data.pop('ingredients', None)
        if tags is not None:
            instance.tags.clear()
            self._get_or_create_tags(tags, instance)

        if ingredients is not None:
            instance.ingredients.clear()
            self._get_or_create_ingredients(ingredients, instance)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


# usamos o RecipeSerializer como base, pois vamos só adicionar alguns campos novos
# vamos aproveitar para não ter que rescrever codigo
class RecipeDetailSerializer(RecipeSerializer):
    """Serializer for recipe detail view"""

    # adiciona o campo description ao meta modelo
    class Meta(RecipeSerializer.Meta):
        fields = RecipeSerializer.Meta.fields + ['description', 'image']

class RecipeImageSerializer(serializers.ModelSerializer):
    """Serializer for uploading images to recipes"""

    class Meta:
        model = Recipe
        fields = ['id', 'image']
        read_only_fields = ['id']
        extra_kwargs= {'image': {'required': 'True'}}









