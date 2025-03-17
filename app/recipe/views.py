"""
Veies for recipe API
"""

from drf_spectacular.utils import (
    extend_schema_view,
    extend_schema,
    OpenApiParameter,
    OpenApiTypes
)
from rest_framework import (viewsets,
                            mixins,
                            status)

from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from core.models import (Recipe, Tag, Ingredient)
from recipe import serializers


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                'tags',
                OpenApiTypes.STR,
                description='Coma separated list of Tags IDs to filter'
            ),
            OpenApiParameter(
                'ingredients',
                OpenApiTypes.STR,
                description='Coma separated list of Ingredients IDs to filter'
            )
        ]
    )
)
class RecipeViewSets(viewsets.ModelViewSet):
    """View for manage recipe APIs"""
    serializer_class = serializers.RecipeDetailSerializer

    # especifica qual o model de modelos que vamos usar para trabalhar
    queryset = Recipe.objects.all()

    # precisa de token authentication
    authentication_classes = [TokenAuthentication]

    # permissão para usar, precisa estar authenticado
    permission_classes = [IsAuthenticated]

    def _params_to_ints(self, qs):
        '''convert a list of strings to Integers'''
        return [int(str_id) for str_id in qs.split(',')]

    def get_queryset(self):
        '''Retrieve recipes for authenticad user'''
        tags = self.request.query_params.get('tags')
        ingredients = self.request.query_params.get('ingredients')
        queryset = self.queryset
        if tags:
            tag_ids = self._params_to_ints(tags)
            queryset = queryset.filter(tags__id__in=tag_ids)
        if ingredients:
            ingredients_ids = self._params_to_ints(ingredients)
            queryset = queryset.filter(ingredients__id__in=ingredients_ids)

        return queryset.filter(
            user=self.request.user
        ).order_by('-id').distinct()


    def get_serializer_class(self):
        '''Return the serializer class for request'''
        if self.action == 'list':
            return serializers.RecipeSerializer

        if self.action == 'upload_image':
            return serializers.RecipeImageSerializer

        return self.serializer_class

    # vamos utilizar o serializer, quando criamos um novo usuario, o serializer vai
    # buscar a informação do usuario correto e entrega o token de authenticação, assim garantindo que a
    # receita seja criada par ao usuario certo
    def perform_create(self, serializer):
        '''Create a new recipe'''
        serializer.save(user=self.request.user)


    # custon action.
    @action(methods=['POST'], detail=True, url_path='upload_image')
    def upload_image(self, request, pk=None):
        '''Upload an image to recipe'''
        recipe = self.get_object()
        serializer = self.get_serializer(recipe, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                'asigned_only',
                OpenApiTypes.INT, enum=[0,1],
                description='Filter by items assigned to recipes.',
            )
        ]
    )
)
class BaseRecipeAttrViewSet(mixins.DestroyModelMixin,
                  mixins.UpdateModelMixin,
                  mixins.ListModelMixin,
                  viewsets.GenericViewSet):
    '''Base classe for attributes of recipes'''
    # deixe as informações genericas aqui.

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        '''Retrive data for authenticated user'''

        assigned_only = bool(
            int(self.request.query_params.get('assigned_only', 0))
        )
        queryset = self.queryset
        if assigned_only:
            queryset = queryset.filter(recipe__isnull=False)

        return queryset.filter(user=self.request.user).order_by('-name').distinct()

class TagViewsSet(BaseRecipeAttrViewSet):
    '''Manage Tags in the database'''
    serializer_class =  serializers.TagSerializer
    queryset = Tag.objects.all()


class IngredientViewSet(BaseRecipeAttrViewSet):
    ''' manage ingredients in the database'''
    serializer_class = serializers.IngredientSerializer
    queryset = Ingredient.objects.all()

