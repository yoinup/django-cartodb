# coding=utf-8

import _geohash

from django.db import models
from django.conf import settings
from django.core.cache import cache
from django.utils.datastructures import SortedDict

import lib as cartodb


CACHE_DURATION = getattr(settings, 'CARTODB_CACHE_DURATION', 120 * 60)


class CartoQuerySet(models.query.QuerySet):
    """
        We use this class to add methods to queryset,
        because we can't chain managers and do queries
        like:
            semi_filtered = super(YoinModelResource, self).apply_filters(
                request, applicable_filters)
            return semi_filtered.for_user(user__id)

        After doing Foo.objects.all() or similar, django stop working
        with managers and use plain QuerySet.

        POSSIBLE IMPROVEMENTS:
            Queryset are lazy, but when be use filter_cartodb, we need to
            call cartodb inmediately, maybe this can be modified to delay
            it until we evaluate the queryset. Modify __getitem__.

            In filter_cartodb, we need to use params limit and offset, maybe
            we can change that to use retrieve item or slice:
                Venue.objects.filter_cartodb(lat,lon)[2:15]

            Use Cache to store cartodb results and avoid duplicate queries
    """

    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)
        # need to store cartodb results
        self._cartodb_result_cache = {}

    def iterator(self):
        superiter = super(CartoQuerySet, self).iterator()
        while True:
            obj = superiter.next()
            if not hasattr(obj, 'distance'):
                if self._cartodb_result_cache:
                    setattr(
                        obj,
                        'distance',
                        float('%.3f' % self._cartodb_result_cache[obj.id].get(
                            'distance', 0)))
                else:
                    setattr(obj, 'distance', 0)
            # Use cache.add instead of cache.set to prevent race conditions
            yield obj

    def filter_cartodb(self, **kwargs):
        """
            THIS QUERY IS NOT LAZY
            Add filter_cartodb to Queryset.

            Search in cartodb the ids and add a
            filter "pk__in=[]" to current queryset.

            Raises error if model is not synced with cartodb

            To use joins, the filter must have this syntax:
                tableJOIN__fieldJOIN__pkJOIN

                with:
                    tableJOIN as the external table name.
                    fieldJOIN the field for filtering.
                    pkJOIN primary key field in external table to match JOIN.
        """
        assert 'lat' in kwargs
        assert 'lon' in kwargs
        assert hasattr(self.model, '_cartodb_table')

        cartodb_table = self.model._cartodb_table

        key = self._get_cache_key(**kwargs)
        if settings.DEBUG:
            self._cartodb_result_cache = None
        else:
            self._cartodb_result_cache = cache.get(key)
        if not self._cartodb_result_cache:
            if 'distance' in kwargs:
                if kwargs['distance'] > 10000:
                    kwargs['distance'] = 10000
                results = cartodb.get_in_distance(
                    cartodb_table,
                    **kwargs)
            else:
                results = cartodb.get_nearest(
                    cartodb_table,
                    **kwargs)
            if not results:
                return self.none()
            # store cartodb response in cache to avoid more queries
            self._cartodb_result_cache = SortedDict([
                (row['cartodb_id'], row) for row in results])
            # ADD prevent race conditions
            cache.add(key, self._cartodb_result_cache, CACHE_DURATION)

        return self._filter_or_exclude(
            negate=False,
            pk__in=self._cartodb_result_cache.keys())

    def _clone(self, klass=None, setup=False, **kwargs):
        """
            Querysets are inmutable, so each time one is modified
            Django clone it, but django doesn't know about
            _cartodb_result_cache, and will get lost,
        """
        c = super(self.__class__, self)._clone(
            klass=klass, setup=setup, **kwargs)
        # copy _cartodb_result_cache to not lost it.
        c._cartodb_result_cache = self._cartodb_result_cache
        return c

    def _get_cache_key(self, **kwargs):
        """
            Generates a valid cache key with a geohash.
            the geohash square is approximately 20 m
        """
        key = 'cartodb_%s_' % _geohash.encode(
            kwargs.pop('lat'), kwargs.pop('lon'))[:8]
        key += '_'.join([
            '%s=%s' % (k, kwargs[k]) for k in sorted(kwargs.iterkeys())])
        return key


class CartoManager(models.Manager):
    def get_query_set(self):
        """
            Use custom QuerySet
        """
        return CartoQuerySet(self.model)

    def nearest(self, lat, lon, limit=10, offset=0):
        """
            From cartoDB gets venues results nearest to point

            return queryset
        """
        return self.get_query_set().filter_cartodb(
            lat=lat,
            lon=lon,
            limit=limit,
            offset=offset)

    def distance(self, lat, lon, distance=1000, limit=10, offset=0):
        """
            From cartoDB gets venues results inside distance

            return queryset
        """
        return self.get_query_set().filter_cartodb(
            lat=lat,
            lon=lon,
            distance=distance,
            limit=limit,
            offset=offset)

    def filter_cartodb(self, **kwargs):
        return self.get_query_set().filter_cartodb(**kwargs)
