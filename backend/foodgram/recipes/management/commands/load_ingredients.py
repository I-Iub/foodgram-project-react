import csv
from itertools import islice

from django.conf import settings
from django.core.management import BaseCommand
from recipes.models import Measurement

BATCH_SIZE = 100


class Command(BaseCommand):
    help = 'Read .csv'

    def handle(self, *args, **kwargs):
        project_dir = settings.BASE_DIR
        with open(
            f'{project_dir}/data/ingredients.csv',
            'r', encoding='utf-8'
        ) as csv_file:
            reader = csv.DictReader(
                csv_file, fieldnames=['name', 'measurement_unit']
            )
            objects = (Measurement(
                name=line['name'],
                measurement_unit=line['measurement_unit']) for line in reader
            )
            while True:
                batch = list(islice(objects, BATCH_SIZE))
                if not batch:
                    break
                Measurement.objects.bulk_create(batch, BATCH_SIZE)

        self.stdout.write(self.style.SUCCESS('Ingredients loaded'))
