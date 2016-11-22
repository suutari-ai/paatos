# Open decision API, 6Aika
Open decision API is providing decisions made by a city in a harmonized and machine-readable format.
This app is developed using Django and Django Rest Framework.

# Päätösrajapinta, 6Aika
Päätösrajapinta on avoin ohjelmointirajapinta (API), josta kaupungin päätökset saadaan esiin yhdenmukaisessa ja koneluettavassa muodossa.

Definition is here: https://github.com/6aika/api-paatos

## Initialize database
```
DB=paatos
createdb ${DB}
psql ${DB} -c "CREATE EXTENSION postgis"
python manage.py migrate
```
  
## Importing data

Helsinki organizations
```
python manage.py import_helsinki_orgs <organizations json file>
```

Decision data from Open Ahjo
```
python manage.py import_open_ahjo <decision data json file>
```
