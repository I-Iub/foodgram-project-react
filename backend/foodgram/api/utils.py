from rest_framework import serializers
from recipes.models import Ingredient, Measurement  # , Tag

AMOUNT_ERROR_MESSAGE = ('Количество ингредиента укажите числом с точкой в '
                        'качестве разделителя десятичной части.')


# def get_tags_objects(tag_list):
#     try:
#         return [
#             Tag.objects.get(id=tag_id) for tag_id in tag_list
#         ]
#     except Tag.DoesNotExist:
#         raise serializers.ValidationError({
#             'tags': ['Тега не существует.']
#         })
#     except ValueError:
#         raise serializers.ValidationError({
#             'tags': ['Тег должен передаваться натуральным числом.']
#         })

def get_unnatural(id_list):
    not_natural = []
    for id in id_list:
        if type(id) == int:
            next
        try:
            if int(id) <= 0:
                not_natural.append(id)
        except ValueError:
            not_natural.append(id)
    return not_natural




def get_ingredients_objects(initial_ingredients_list):
    ingredients_objects = []
    # for ingredient_dict in initial_ingredients_list:
    #     measurement_id = ingredient_dict.get('id')
    #     try:
    #         measurement_object = Measurement.objects.get(id=measurement_id)
    #     except Measurement.DoesNotExist:
    #         raise serializers.ValidationError({  # Для валидации в сериализаторе используется метод validate
    #             'ingredients': [
    #                 'Ингредиента не существует.'
    #             ]
    #         })
    #     amount = ingredient_dict.get('amount')
    #     try:
    #         amount = float(amount)  # добавить проверку, что количество больше 0
    #     except ValueError:
    #         raise serializers.ValidationError({  # Для валидации в сериализаторе используется метод validate
    #             'amount': [AMOUNT_ERROR_MESSAGE]
    #         })
    #     except TypeError:
    #         raise serializers.ValidationError({  # Для валидации в сериализаторе используется метод validate
    #             'amount': [AMOUNT_ERROR_MESSAGE]
    #         })
    for ingredient_dict in initial_ingredients_list:
        measurement_id = ingredient_dict.get('id')
        measurement_object = Measurement.objects.get(id=measurement_id)
        amount = ingredient_dict.get('amount')
        if not Ingredient.objects.filter(
                measurement=measurement_object,
                amount=amount).exists():
            ingredient_object = Ingredient.objects.create(
                measurement=measurement_object,
                amount=amount
            )
        else:
            ingredient_object = Ingredient.objects.get(
                measurement=measurement_object,
                amount=amount
            )
        ingredients_objects += [ingredient_object]
    return ingredients_objects


def get_integer_list(parameter_list, parameter_name):
    """Возвращает словарь со списком параметров, преобразованных в целые числа
    или сообщением об ошибке, если преобразовать не удалось.
    """
    try:
        integer_list = [
            int(parameter) for parameter in parameter_list
        ]
        return {
            'list': integer_list
        }
    except ValueError:
        return {
            'error_message': f"Ошибка: в параметре запроса '{parameter_name}' "
                             f"должно быть указано натуральное число."
        }


def get_object_if_exists(object_class, object_id):
    try:
        object = object_class.objects.get(pk=object_id)
        return {
            'object': object}
    except object_class.DoesNotExist:
        return {
            'error_message': f'Объекта с id={object_id} не существует.'
        }
    except ValueError:
        return {
            'error_message': (
                f'{object_id} - id должен передаваться натуральным числом.'
            )
        }
