"""
Template filter to replace spaces in a string with non-breaking spaces.

Inspired by: https://djangosnippets.org/snippets/2842/
"""
from django.template import Library
from django.utils.safestring import mark_safe


register = Library()


@register.filter()
def nbsp(value):
    """
    Replace spaces in a string with non-breaking spaces.

    An example of how to use ``nbsp``::

        {% load nbsp %}

        {{ '   blah blah   '|nbsp }}


    An example of how ``nbsp`` works::

        >>> nbsp('   blah blah   ')
        '&nbsp;&nbsp;&nbsp;blah&nbsp;blah&nbsp;&nbsp;&nbsp;'
    """
    return mark_safe("&nbsp;".join(value.split(' ')))


def _test():
    import doctest
    doctest.testmod()


if __name__ == "__main__":
    _test()
