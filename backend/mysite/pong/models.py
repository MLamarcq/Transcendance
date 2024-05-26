from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin


# Create your models here.
def validate_image(data):
    """
    Validate that the uploaded data is a valid image.
    """
    image_format = imghdr.what(None, h=data)
    if not image_format:
        raise ValidationError('Invalid image format.')

class User(AbstractBaseUser, PermissionsMixin):
    pseudo = models.CharField(max_length=20,unique=True)
    email = models.EmailField(unique=True)
    avatar = models.BinaryField(validators=[validate_image])
    #amis (pointe) = 
    #party (pointe) =
    #statistiques (pointe) =
    #chats (pointe)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['email']

    def __str__(self):
        return self.pseudo