"""
Template filter to fit lists into tables.

Inspired by: https://djangosnippets.org/snippets/401/
"""
from math import ceil

from django.template import Library


register = Library()


@register.filter
def list2table(thelist, n):
    """
    Break a list into rows of up to ``n`` elements to fit into a table with ``n`` columns.

    An example of how to use ``list2table``::

        {% load list2table %}

        <table>
          {% for row in mylist|list2table:8 %}
            <tr>
              {% for item in row  %}
                <td>{{ item }}</td>
              {% endfor %}
            </tr>
          {% endfor %}
        </table>


    An example of how ``list2table`` works::

        >>> l = range(10)

        >>> list2table(l, 2)
        [[0, 1], [2, 3], [4, 5], [6, 7], [8, 9]]

        >>> list2table(l, 3)
        [[0, 1, 2], [3, 4, 5], [6, 7, 8], [9]]

        >>> list2table(l, 4)
        [[0, 1, 2, 3], [4, 5, 6, 7], [8, 9]]

        >>> list2table(l, 5)
        [[0, 1, 2, 3, 4], [5, 6, 7, 8, 9]]

        >>> list2table(l, 9)
        [[0, 1, 2, 3, 4, 5, 6, 7, 8], [9]]

        >>> list2table(l, 20)
        [[0, 1, 2, 3, 4, 5, 6, 7, 8, 9]]
    """

    try:
        n = int(n)
        thelist = list(thelist)
    except (ValueError, TypeError):
        return [thelist]
    return [thelist[n * i:n * (i + 1)] for i in range(ceil(len(thelist) / n))]


def _test():
    import doctest
    doctest.testmod()


if __name__ == "__main__":
    _test()
