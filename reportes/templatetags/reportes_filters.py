from django import template
from django.utils.encoding import force_text
from django.utils.safestring import mark_safe

__author__ = 'Tania'


register = template.Library()


def _scaper(x):
    """
    Funcion para solucionar PEP8 E731 (do not assign name to lambda expression, use a def).
    """
    return x


def unordered_list_grupos(value, autoescape=None):
    """
    Recursively takes a self-nested list and returns an HTML unordered list --
    WITHOUT opening and closing <ul> tags.

    The list is assumed to be in the proper format. For example, if ``var``
    contains: ``['States', ['Kansas', ['Lawrence', 'Topeka'], 'Illinois']]``,
    then ``{{ var|unordered_list }}`` would return::

        <li>States
        <ul>
                <li>Kansas
                <ul>
                        <li>Lawrence</li>
                        <li>Topeka</li>
                </ul>
                </li>
                <li>Illinois</li>
        </ul>
        </li>
    """
    if autoescape:
        from django.utils.html import conditional_escape
        escaper = conditional_escape
    else:
        escaper = _scaper

    def convert_old_style_list(list_):
        """
        Converts old style lists to the new easier to understand format.

        The old list format looked like:
            ['Item 1', [['Item 1.1', []], ['Item 1.2', []]]

        And it is converted to:
            ['Item 1', ['Item 1.1', 'Item 1.2]]
        """

        if not isinstance(list_, (tuple, list)) or len(list_) != 2:
            return list_, False

        first_item, second_item = list_

        if second_item == []:
            return [first_item], True
        try:
            it = iter(second_item)  # see if second item is iterable
        except TypeError:
            return list_, False

        old_style_list = True
        new_second_item = []

        for sublist in second_item:
            item, old_style_list = convert_old_style_list(sublist)
            if not old_style_list:
                break
            new_second_item.extend(item)
        if old_style_list:
            second_item = new_second_item

        return [first_item, second_item], old_style_list

    def _helper(list_, tabs=1):
        indent = '\t' * tabs
        output = []

        list_length = len(list_)
        i = 0
        while i < list_length:
            title = list_[i]
            sublist = ''
            sublist_item = None
            if isinstance(title, (list, tuple)):
                sublist_item = title
                title = ''
            elif i < list_length - 1:
                next_item = list_[i + 1]
                if next_item and isinstance(next_item, (list, tuple)):
                    # The next item is a sub-list.
                    sublist_item = next_item
                    # We've processed the next item now too.
                    i += 1
            if sublist_item:
                sublist = _helper(sublist_item, tabs+1)
                sublist = '\n%s<ul>\n%s\n%s</ul>\n%s' % (indent, sublist,
                                                         indent, indent)
            output.append('%s<li data-id="%s"><a>%s</a>%s</li>' % (
                indent, title.id, escaper(force_text(title)), sublist))
            i += 1
        return '\n'.join(output)

    value, converted = convert_old_style_list(value)

    return mark_safe(_helper(value))
unordered_list_grupos.is_safe = True
unordered_list_grupos.needs_autoescape = True

register.filter(unordered_list_grupos)


@register.filter
def sub(value, arg):
    return value - arg
