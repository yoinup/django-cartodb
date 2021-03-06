# coding=utf-8

import re

from django.conf import settings

from cartodb.cartodb import CartoDBAPIKey

cl = CartoDBAPIKey(
    settings.CARTODB_KEY,
    settings.CARTODB_DOMAIN)


def custom_sql(sql):
    """
        Query cartodb to get ID ordered by distance to the point
    """
    result = cl.sql(sql)
    objects = result['rows']
    return objects


def get_nearest(table_name, lat, lon, limit=20, offset=0, **kwargs):
    """
        Query cartodb to get ID ordered by distance to the point
    """
    join_sql = _build_joins(table_name, **kwargs)

    sql = u"""
                SELECT %(tablename)s.cartodb_id,
                    ST_Distance(%(tablename)s.the_geom::geometry,
                        ST_SetSRID(ST_Point(%(lon)s,%(lat)s),
                         4326)::geography) AS distance
                FROM %(tablename)s
                %(joins)s
                ORDER BY %(tablename)s.the_geom <-> ST_SetSRID(ST_Point(
                    %(lon)s,%(lat)s), 4326)::geometry ASC
                LIMIT %(limit)s OFFSET %(offset)s
                """ % {
        'tablename': table_name,
        'lat': '%.6f' % lat,
        'lon': '%.6f' % lon,
        'limit': limit,
        'offset': offset,
        'joins': join_sql,
    }
    if 'custom_sql' in kwargs:
        sql = sql + kwargs['custom_sql']
    result = cl.sql(sql)

    objects = result['rows']
    return objects


def get_in_distance(
        table_name, lat, lon, distance=1000,
        limit=20, offset=0, **kwargs):
    """
        Query cartodb to get venues
        inside a circunference of radious <distance>
    """
    join_sql = _build_joins(table_name, **kwargs)

    sql = u"""
                SELECT %(tablename)s.cartodb_id,
                    ST_Distance(%(tablename)s.the_geom::geometry,
                        ST_SetSRID(ST_Point(%(lon)s,%(lat)s),
                         4326)::geography) AS distance
                FROM %(tablename)s
                %(joins)s
                WHERE ST_DWithin(%(tablename)s.the_geom,
                    ST_SetSRID(ST_Point(%(lon)s,%(lat)s), 4326)::geography,
                    %(distance)s)
                ORDER BY %(tablename)s.the_geom <-> ST_SetSRID(ST_Point(
                    %(lon)s,%(lat)s), 4326)::geometry ASC
                LIMIT %(limit)s OFFSET %(offset)s
                """ % {
        'tablename': table_name,
        'lat': '%.6f' % lat,
        'lon': '%.6f' % lon,
        'distance': distance,
        'limit': limit,
        'offset': offset,
        'joins': join_sql
    }
    if 'custom_sql' in kwargs:
        sql = sql + kwargs['custom_sql']
    result = cl.sql(sql)

    objects = result['rows']
    return objects


def _build_joins(table_name, **kwargs):
    """
        Generate multiple JOINs for the Query.
        To use joins, the filter must have this syntax:
            tableJOIN__fieldJOIN__pkJOIN

            with tableJOIN as the external table name.
            fieldJOIN the field for filtering.
            pkJOIN primary key field in external table to match JOIN.
    """
    join_sql = ''
    for k, v in kwargs.items():
        if re.match('\w+__\w+__\w+', k):
            table_join, field, pk = k.split('__')
            join_sql += """
                JOIN %(tablejoin)s ON
                    (%(tablejoin)s.%(field)s=%(value)s AND
                    %(tablejoin)s.%(pk)s=%(tablename)s.cartodb_id)
                """ % {
                        'tablename': table_name,
                        'tablejoin': table_join,
                        'field': field,
                        'pk': pk,
                        'value': v,
            }
        if re.match('\w+__\w+', k):
            table_join, field = k.split('__')
            join_sql += """
                JOIN %(tablejoin)s ON
                    %(tablejoin)s.%(field)s=%(tablename)s.cartodb_id
                """ % {
                        'tablename': table_name,
                        'tablejoin': table_join,
                        'field': field,
            }
    return join_sql


def delete_row(table_name, pk):
    result = cl.sql(u"""
                DELETE FROM %(tablename)s
                WHERE cartodb_id=%(pk)s;
                """ % {
        'tablename': table_name,
        'pk': pk,
    })

    return result


def delete_all(table_name):
    result = cl.sql(u"""
                DELETE FROM %(tablename)s;
                """ % {
        'tablename': table_name})

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
