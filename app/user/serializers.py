'''
Serializers for the users api view
'''

from django.contrib.auth import (
                                get_user_model,
                                authenticate
                                )

from django.utils.translation import gettext as _

from rest_framework import serializers

class UserSerializer(serializers.ModelSerializer):
    '''serializer for the user object.'''

    # here we create the validation of the model, we want to use
    # we ensure we're using the model by setting the get_user_model()
    # and in the kwargs, we define, how the data must be, if it comes otherwise, it'll fail
    class Meta:
        model = get_user_model()
        fields = ['email', 'password', 'name']
        extra_kwargs ={'password': {'write_only': True, 'min_length': 5}}


    # the function create will only be called IF the validation, we issued to the model
    # is ok, if the data on the payload fail the validation, the create will no be called
    def create(self, validated_data):
        ''' creat and return a user with encrypted password'''
        return get_user_model().objects.create_user(**validated_data)

    # instance é o model que sera atualizado.
    def update(self, instance, validated_data):
        """Update and return user"""
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)

        if password:
            user.set_password(password)
            user.save()
        return user


class AuthTokenSerializer(serializers.Serializer):
    """Serializer for the auth token"""
    email = serializers.EmailField()
    password = serializers.CharField(
        style={'input_type': 'password'},
        trim_whitespace=False,
    )


    # o validate vai ser chamado pela view.
    def validate(self, attrs):
        """Validate and authenticate the user"""
        email = attrs.get('email')
        password = attrs.get('password')
        user = authenticate(
            request = self.context.get('request'),
            username = email,
            password = password
        )

        if not user:
            msg= _('Unable to authenticate with provided credentials.')

            # esse tipo de erro é utilizado, para que quando a view, veja o erro
            # retorno o erro http 400, que é o erro que esperamos no test.
            raise serializers.ValidationError(msg, code='authorization')

        attrs['user'] = user
        return attrs
