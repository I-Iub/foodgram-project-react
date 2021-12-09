from base64 import b64decode

from django.core.files.base import ContentFile
from rest_framework import serializers


class Base64ToImageField(serializers.ImageField):
    def to_internal_value(self, base64_string):
        if not base64_string:
            return super().to_internal_value(None)
        if base64_string.startswith('data:image'):
            description, image_string = base64_string.split(';base64,')
            extension = description.split('/')[-1]  # расширение файла
            data = ContentFile(
                b64decode(image_string), name='temp.' + extension
            )
        else:
            image_string = base64_string
            data = ContentFile(b64decode(image_string), name='temp.jpeg')
        return super().to_internal_value(data)
