# coding=utf-8

from django.conf import settings
from cartodb import CartoDBAPIKey

cl = CartoDBAPIKey(
    settings.CARTODB_KEY,
    settings.CARTODB_DOMAIN)


def get_nearest(table_name, lat, lon, limit=20, offset=0):
    """
        Query cartodb to get ID ordered by distance to the point
    """
    result = cl.sql(u"""
                SELECT cartodb_id,
                    ST_Distance(the_geom::geography,
                        ST_SetSRID(ST_Point(%(lon)s,%(lat)s),
                         4326)::geography) AS distance
                FROM %(tablename)s ORDER BY distance
                ASC LIMIT %(limit)s OFFSET %(offset)s
                """ % {
        'tablename': table_name,
        'lat': '%.5f' % lat,
        'lon': '%.5f' % lon,
        'limit': limit,
        'offset': offset,
    })
    objects = result['rows']
    return objects


def get_in_distance(table_name, lat, lon, distance=1000, limit=20, offset=0):
    """
        Query cartodb to get venues
        inside a circunference of radious <distance>
    """
    result = cl.sql(u"""
                SELECT cartodb_id,
                    ST_Distance(the_geom::geography,
                        ST_SetSRID(ST_Point(%(lon)s,%(lat)s),
                         4326)::geography) AS distance
                FROM %(tablename)s
                WHERE ST_DWithin(the_geom,
                    ST_SetSRID(ST_Point(%(lon)s,%(lat)s), 4326)::geography,
                    %(distance)s)
                ORDER BY distance ASC LIMIT %(limit)s OFFSET %(offset)s
                """ % {
        'tablename': table_name,
        'lat': '%.5f' % lat,
        'lon': '%.5f' % lon,
        'distance': distance,
        'limit': limit,
        'offset': offset,
    })
    objects = result['rows']
    return objects


def delete_row(table_name, pk):
    result = cl.sql(u"""
                DELETE FROM %(tablename)s
                WHERE cartodb_id=%(pk)s
                """ % {
        'tablename': table_name,
        'pk': pk,
    })

    return result


def get_row_id(table_name, pk):
    """
        Gets row with carto_db == <pk>
    """
    result = cl.sql(u"""
                SELECT cartodb_id,
                    ST_AsGeoJSON(the_geom)
                FROM %(tablename)s
                WHERE cartodb_id=%(pk)s
                """ % {
        'tablename': table_name,
        'pk': pk,
    })

    return result
