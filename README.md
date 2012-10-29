django-cartodb
==============

Integration of CartoDB.com with Django

Initial
---------

This project extends Django's QuerySet, some initial configurations need to be
done in each model that use CartoDB integration:

See yoinup/django-cartodb/django_cartodb/models.py

```python

from django_cartodb.django_cartodb.models import CartoManager

class SomeModel(models.Model):
    objects = CartoManager()
    _cartodb_table = 'somemodeltable'  # model's table name in CartoDB
```

Usage
---------

All django method's in models manager are the same, your actual code don't 
need modifications to work.

CartoManager includes a **filter_cartodb()** method to do complex queries to CartoDB.

Also, two shortcuts were added:

* Get objects nearest to a position:

```python
nearest(lat, lon, limit=10, offset=0)
```

* Get objects inside a distance from a position:

```python
distance(self, lat, lon, distance=1000, limit=10, offset=0)
```

### filter_cartodb(): ######

Other methods like *filter(), exclude(), order_by()* can be chained and used together with *filter_cartodb()*

**IMPORTANT:** filter_cartodb() isn't lazy like filter() is, so each time is called, a request will be sent to 
CartoDB and your code will block until the response is received.

Parameters required:

* **lat**: float with the latitude
* **lon**: float with the longitude

Optional:

* **distance**: *int*, query objects inside a distance (in meters).
* **limit**: *int*, limit number of objects retrieved
* **offset**: *int*, remove from list first *offset* objects

```python
# To get first 10 objects in 1km around the (lat, lon) point.
SomeModel.objects.filter_cartodb(lat=0.123434, lon=-3.154774, distance=1000, limit=10)
# To get the next 10 objects
SomeModel.objects.filter_cartodb(lat=0.123434, lon=-3.154774, distance=1000, limit=10, offset=10)
```
When iterating over the list of objects returned, each object get a **distance** attr added with 
the distance between the object and the point queried.

#### JOINs: ######

An initial JOINs support is available, add a param like *tableJOIN__fieldJOIN__pkJOIN* when calling **filter_cartodb()**:

* *tableJOIN*: is the name of the table in CartoDB to do the join.
* *fieldJOIN*: the field in *tableJOIN* to filter
* *pkJOIN*: the field in *tableJOIN* with the primary key reference to mix each table.

```python
# add JOIN querying *categorytable* with field *category_id* equals to 2 and *model_id* as primary key field.
SomeModel.objects.filter_cartodb(
  lat=0.123434, 
  lon=-3.154774, 
  distance=1000, 
  categorytable__category_id__model_id=2)
```


TODO:
---------

* Return object list ordered by distance, in MySQL maybe FIELD(param, values) can be used.
* Support to custom ORDER BY.
* Support to add custom SQL queries.