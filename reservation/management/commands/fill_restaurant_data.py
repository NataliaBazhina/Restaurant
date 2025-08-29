import json
from django.core.management import BaseCommand
from reservation.models import Hall, Table


class Command(BaseCommand):

    @staticmethod
    def json_read_halls():
        with open('reservation/fixture/restaurant_data.json', 'r', encoding='utf-8') as file:
            data = json.load(file)
            halls = []
            for item in data:
                if item['model'] == 'reservation.hall':
                    halls.append(item)
            return halls


    @staticmethod
    def json_read_tables():
        with open('reservation/fixture/restaurant_data.json', 'r', encoding='utf-8') as file:
            data = json.load(file)
            tables = []
            for item in data:
                if item['model'] == 'reservation.tables':
                    tables.append(item)
            return tables

    def handle(self, *args, **options):
        Hall.objects.all().delete()
        Table.objects.all().delete()

        halls_for_create = []
        for hall in Command.json_read_halls():
            halls_data = hall["fields"]
            halls_for_create.append(Hall(id=hall["pk"], **halls_data))
        Hall.objects.bulk_create(halls_for_create)

        tables_for_create = []
        for table in Command.json_read_tables():
            table_data = table["fields"]
            hall = Hall.objects.get(pk=table_data.pop("hall"))
            tables_for_create.append(
                Table(id=table["pk"], category=hall, **table_data)
            )
        Table.objects.bulk_create(tables_for_create)


