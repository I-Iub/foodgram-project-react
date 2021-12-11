from recipes.models import Ingredient, Measurement

AMOUNT_ERROR_MESSAGE = ('Количество ингредиента укажите числом с точкой в '
                        'качестве разделителя десятичной части.')


def get_ingredients_objects(initial_ingredients_list):
    ingredients_objects = []
    for ingredient_dict in initial_ingredients_list:
        measurement_id = ingredient_dict.get('id')
        measurement_object = Measurement.objects.get(id=measurement_id)
        amount = ingredient_dict.get('amount')
        ingredient_object, created = Ingredient.objects.get_or_create(
            measurement=measurement_object, amount=amount
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
                             f"должно быть указано целое неотрицательное "
                             f"число."
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


def get_unnatural(id_list):
    not_natural = []
    for id in id_list:
        try:
            if int(id) <= 0:
                not_natural.append(id)
        except ValueError:
            not_natural.append(id)
    return not_natural


def check_id_list(object_class, id_list):
    errors = []
    unnatural = get_unnatural(id_list)
    if unnatural:
        errors.append(f'{unnatural} - должны быть натуральными числами.')
    natural = set(id_list) - set(unnatural)
    if natural:
        not_exists = []
        for id in natural:
            # проверка наличия в базе:
            if not object_class.objects.filter(pk=id).exists():
                not_exists.append(id)
        if not_exists:
            errors.append(f'{not_exists} - не существует.')
    return errors


def check_amount_list(amount_list):
    errors = []
    for amount in amount_list:
        try:
            amount = float(amount)
            if amount < 0:
                errors.append(
                    f'{amount} - количество должно быть больше нуля.'
                )
        except ValueError:
            errors.append(f'{amount} - ' + AMOUNT_ERROR_MESSAGE)
        except TypeError:
            errors.append(f'{amount} - ' + AMOUNT_ERROR_MESSAGE)
    return errors


def check_ingredients_data(initial_ingredients_list):
    errors = {}
    measurement_list = []
    amount_list = []
    for ingredient in initial_ingredients_list:
        measurement_list.append(ingredient.get('id'))
        amount_list.append(ingredient.get('amount'))

    measurement_errors = check_id_list(Measurement, measurement_list)
    amount_errors = check_amount_list(amount_list)
    if measurement_errors:
        errors['id'] = measurement_errors
    if amount_errors:
        errors['amount'] = amount_errors
    return errors
