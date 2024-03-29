**********
django-compatible-index-sequences
**********

``django-compatible-index-sequences`` is a Django app for identifying compatible index sequences for high-throughput sequencing experiments.

Source code is available on GitHub at `mfcovington/django-compatible-index-sequences <https://github.com/mfcovington/django-compatible-index-sequences>`_.


.. contents:: :local:


Installation
============

.. **PyPI**

.. .. code-block:: sh

..     pip install django-compatible-index-sequences


**GitHub (development branch)**

.. code-block:: sh

    pip install git+http://github.com/mfcovington/django-compatible-index-sequences.git@develop


Configuration
=============

Add ``compatible_index_sequences`` and its dependencies to ``INSTALLED_APPS`` in ``settings.py``:

.. code-block:: python

    INSTALLED_APPS = (
        ...
        'compatible_index_sequences.apps.CompatibleIndexSequencesConfig',
        'bootstrap3',
        'sekizai',
    )


Add the ``compatible_index_sequences`` URLs to the site's ``urls.py``:

.. code-block:: python

    from django.conf.urls import url, include

    urlpatterns = [
        ...
        url(r'^compatible_index_sequences/', include('compatible_index_sequences.urls', namespace='compatible_index_sequences')),
    ]


Add ``sekizai`` settings:

- For **Django versions before 1.10**, add ``sekizai.context_processors.sekizai`` to ``TEMPLATE_CONTEXT_PROCESSORS``:

  .. code-block:: python

      from django.conf.global_settings import TEMPLATE_CONTEXT_PROCESSORS
      TEMPLATE_CONTEXT_PROCESSORS += ('sekizai.context_processors.sekizai',)


- For **Django versions 1.10 and later**, add ``sekizai.context_processors.sekizai`` to ``TEMPLATES``:

  .. code-block:: python

      TEMPLATES = [
          {
              # ...
              'OPTIONS': {
                  'context_processors': [
                      # ...
                      'sekizai.context_processors.sekizai',
                  ],
              },
          },
      ]


Migrations
==========

Create and perform ``compatible_index_sequences`` migrations:

.. code-block:: sh

    python manage.py makemigrations compatible_index_sequences
    python manage.py migrate


Pre-Populate Database
=====================

Add commercial index sets to the database:

.. code-block:: sh

    python manage.py loaddata compatible_index_sequences/fixtures/*.json


Usage
=====

- Start the development server:

.. code-block:: sh

    python manage.py runserver


- Visit: ``http://127.0.0.1:8000/compatible_index_sequences/``


*Version 0.0.0*
