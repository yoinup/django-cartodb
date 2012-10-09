# coding=utf-8

import _geohash

from django.db import models
from django.conf import settings
from django.core.cache import cache

import cartoyoin.lib as cartoyoin

CACHE_DURATION = getattr(settings, 'CARTOYOIN_CACHE_DURATION', 120 * 60)


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
                        '%.3f' % self._cartodb_result_cache[obj.id].get(
                            'distance', 0))
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

            Raises NotImplementedError if model is not synced with cartodb
        """
        assert 'lat' in kwargs
        assert 'lon' in kwargs

        if self.model == models.get_model('venues', 'Venue'):
            carto_table = settings.CARTODB_VENUES
        elif self.model == models.get_model('venues', 'VenueCheckIn'):
            carto_table = settings.CARTODB_CHECKINS
        else:
            raise NotImplementedError('Unknown model type')

        """
            We do a little trick here, generate a small square around the point
            with geohash and store it in cache, so we avoid repeating very
            close queries to cartodb
        """
        key = self._get_cache_key(kwargs['lat'], kwargs['lon'])
        self._cartodb_result_cache = cache.get(key)
        if self._cartodb_result_cache:
            return self._filter_or_exclude(
                negate=False,
                pk__in=self._cartodb_result_cache.keys())

        if 'distance' in kwargs:
            if kwargs['distance'] > 10000:
                kwargs['distance'] = 10000
            results = cartoyoin.get_in_distance(
                carto_table,
                **kwargs)
        else:
            results = cartoyoin.get_nearest(
                carto_table,
                **kwargs)

        if not results:
            return self.none()

        # store cartodb response in cache to avoid more queries
        self._cartodb_result_cache = {
            row['cartodb_id']: row for row in results}

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

    def _get_cache_key(self, lat, lon):
        """
            Generates a valid cache key with a geohash.
            the geohash square is approximately 20 m
        """
        return 'cartodb_%s' % _geohash.encode(lat, lon)[:8]


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
