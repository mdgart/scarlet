import datetime
import urllib

from django.forms import widgets
from django import forms
from django.utils.encoding import force_unicode
from django.utils.safestring import mark_safe
from django.utils.html import conditional_escape
from django.core.urlresolvers import reverse
from django.utils import timezone
from django.utils.dateparse import parse_time

from django.contrib.admin.widgets import url_params_from_lookup_dict

class DateWidget(widgets.TextInput):
    """
    Widget for date fields. Sets a **data-date-format**
    attribute to "yyyy-mm-dd"
    """

    def __init__(self, *args, **kwargs):
        super(DateWidget, self).__init__(*args, **kwargs)
        self.attrs['data-date-format'] = "yyyy-mm-dd"


class AutoSlugWidget(widgets.TextInput):
    """
    Widget that render a text field with data used
    to auto populate the Input.

    """
    def __init__(self, prepopulated_fields=None, *args, **kwargs):
        super(AutoSlugWidget, self).__init__(*args, **kwargs)
        if prepopulated_fields:
            for k,v in prepopulated_fields.iteritems():
                self.attrs['data-populate-source'] = ",".join(v)

class TimeChoiceWidget(widgets.Select):
    """
    Widget for time fields. A select widget that will have a 'now'
    option plus an option for each block of time you want to
    display. By default this will be one item in the drop down for
    every 15 min block of a day.

    :param attrs: HTML attributes for the widget; same as django's.
    :param min_interval: Interval for minutes in your dropdown, \
    should be a number between 1 and 60. Default is 15.
    :param sec_interval: Interval for seconds in your dropdown, \
    should be a number between 1 and 60. Default is 60.
    :param twenty_for_hour: Display time in a 24hr format? \
    Default is False.
    """

    NOW = 'now'

    def __init__(self, attrs=None, min_interval=15, sec_interval=60,
                 twenty_four_hour=False):
        super(TimeChoiceWidget, self).__init__(attrs)
        assert min_interval <= 60 and min_interval > 0
        assert sec_interval <=60 and sec_interval > 0

        self.twenty_four_hour = twenty_four_hour
        self.choices = [(self.NOW, 'Now')]
        self.choice_values = set()

        self.repr_format = "%H:%M:%S"
        if twenty_four_hour:
            self.repr_format = "%I:%M:%S %p"

        for hour in range(24):
            for min_v in range(60 / min_interval):
                min_v = min_v * min_interval
                for sec in range(60 / sec_interval):
                    sec = sec * sec_interval
                    t = datetime.time(hour, min_v, sec)
                    self.choices.append((t.strftime("%H:%M:%S"),
                                         t.strftime(self.repr_format)))
                    self.choice_values.add(t.strftime("%H:%M:%S"))

    def value_from_datadict(self, *args):
        data = super(TimeChoiceWidget, self).value_from_datadict(*args)
        if data == self.NOW:
            # Time should be naive, conversion happens later
            data = datetime.datetime.now().strftime("%H:%M:%S")
        return data

    def render(self, name, value, attrs=None, choices=()):
        if value:
            if type(value) == type("") or type(value) == type(u""):
                try:
                    value = parse_time(value)
                except ValueError:
                    value = None

            if value and isinstance(value, datetime.time):
                value_str = value.strftime("%H:%M:%S")
                if not value_str in self.choice_values:
                    choices = list(choices)
                    choices.append((value_str, value.strftime(self.repr_format)))
        return super(TimeChoiceWidget, self).render(name, value, attrs=attrs,
                                                    choices=choices)


class SplitDateTime(widgets.SplitDateTimeWidget):
    """
    Widget for datetime fields. Uses DateWidget, TimeChoiceWidget.
    """

    def __init__(self, attrs=None):
        widgets = [DateWidget, TimeChoiceWidget]
        forms.MultiWidget.__init__(self, widgets, attrs)

    def format_output(self, rendered_widgets):
        return mark_safe(u'%s %s' % (rendered_widgets[0], rendered_widgets[1]))

    def value_from_datadict(self, data, files, name):
        d = super(SplitDateTime, self).value_from_datadict(data, files, name)
        if not self.is_required and len(d) and not d[0]:
            return ['', '']
        return d

class APIChoiceWidget(widgets.Input):
    """
    Widget for selecting a related object. This is used
    as the default widget for ForeignKey fields. Outputs
    text input field that is wrapped in a <div> that contains
    3 data attributes.

    * data-api: The url that can be queried to get the options \
    for this field in json format.
    * data-add: The url that should be called in a popup to add \
    a new item. If not present adding is not supported.
    * data-title: The title of the field.

    In order for this widget to work it needs to know where those urls are and
    if the rendering user has the needed permissions. This is
    accomplished by having the code that prepares the form
    call the `update_links` method. See the method documentation for
    what parameters are needed.

    :param rel: The rel attribute of the foreign key field that \
    this widget is for.
    :param attrs: HTML attributes for this field, same as django's.
    :param using: The database to use. Defaults to None.
    :param view: The string name of the view that will be used for \
    getting the api url. Defaults to 'main'.
    :param api_url: The api url. This is only used if the automatic url \
    discovery fails.
    :param add_view: The string name of the view that will be used for \
    getting the add url. Defaults to 'add'.
    :param add_url: The url for adding a new item. This is only used \
    if the automatic url discovery fails.
    :param extra_query_kwargs: Keyword arguments that you would like \
    passed as part of the query string.
    """

    input_type = 'hidden'
    template = u'<div class="api-select" data-title="%(value)s" data-api="%(link)s" data-add="%(add_link)s">%(input)s</div>'

    def __init__(self, rel, attrs=None, using=None,
                        view="main", api_url='',
                        add_view="add", add_url='',
                        extra_query_kwargs=None):
        super(APIChoiceWidget, self).__init__(attrs=attrs)
        self.rel = rel
        self.model = self.rel.to
        self.db = using

        self.extra_query_kwargs = extra_query_kwargs

        self.view = view
        self.add_view = add_view

        self._api_link = api_url
        self._add_link = add_url


    def render(self, name, value, attrs=None, choices=()):
        data = {
            'input': super(APIChoiceWidget, self).render(name, value,
                                                          attrs=attrs),
            'value': conditional_escape(self.label_for_value(value)),
            'link': self.get_api_link(),
            'add_link' : self.get_add_link()
        }
        return mark_safe(self.template % data)

    def get_qs(self):
        """
        Returns a mapping that will be used to generate
        the query string for the api url. Any values
        in the the `limit_choices_to` specified on the
        foreign key field and any arguments specified on
        self.extra_query_kwargs are converted to a format
        that can be used in a query string and returned as
        a dictionary.
        """

        qs = url_params_from_lookup_dict(self.rel.limit_choices_to)
        if not qs:
            qs = {}

        if self.extra_query_kwargs:
            qs.update(self.extra_query_kwargs)
        return qs

    def _get_bundle_link(self, bundle, view_name, user):
        url = bundle.get_view_url(view_name, user)
        if url:
            return url
        return ''

    def _get_reverse(self, name, url_kwargs):
        return reverse(name, kwargs=url_kwargs)

    def update_links(self, request, admin_site=None):
        """
        Called to update the widget's urls. Tries to find the
        bundle for the model that this foreign key points to and then
        asks it for the urls for adding and listing and sets them on
        this widget instance. The urls are only set if request.user
        has permissions on that url.

        :param request: The request for which this widget is being rendered.
        :param admin_site: If provided, the `admin_site` is used to lookup \
        the bundle that is registered as the primary url for the model \
        that this foreign key points to.
        """

        if admin_site:
            bundle = admin_site.get_bundle_for_model(self.model)

            if bundle:
                self._api_link = self._get_bundle_link(bundle, self.view,
                                                       request.user)
                self._add_link = self._get_bundle_link(bundle, self.add_view,
                                                       request.user)

    def get_api_link(self):
        """
        Adds a query string to the api url. At minimum adds the type=choices
        argument so that the return format is json. Any other filtering
        arguments calculated by the `get_qs` method are then added to the
        url. It is up to the destination url to respect them as filters.
        """

        url = self._api_link
        if url:
            qs = self.get_qs()
            url = "%s?type=choices" % url
            if qs:
                url = "%s&amp;%s" % (url, u'&amp;'.join([u'%s=%s' % (k, urllib.quote(unicode(v).encode('utf8'))) \
                                                        for k, v in qs.items()]))
                url = "%s&amp;%s" % (url, u'&amp;'.join([u'exclude=%s' % x \
                                                        for x in qs.keys()]))
        return url

    def get_add_link(self):
        """
        Appends the popup=1 query string to the url so the
        destination url treats it as a popup.
        """

        url = self._add_link
        if url:
            return "%s?popup=1" % url
        return url

    def label_for_value(self, value, key=None):
        """
        Looks up the current value of the field and returns
        a unicode representation. Default implementation does a lookup
        on the target model and if a match is found calls force_unicode
        on that object. Otherwise a blank string is returned.
        """
        if not key:
            key = self.rel.get_related_field().name

        if value is not None:
            try:
                obj = self.model._default_manager.using(self.db
                                                         ).get(**{key: value})
                return force_unicode(obj)
            except (ValueError, self.model.DoesNotExist):
                return ''
        return ''


class APIModelChoiceWidget(APIChoiceWidget):
    """
    Widget for selecting a related object. This is meant to
    be used in forms that specify their own related fields.
    Inherits from APIChoiceWidget but is based on a model
    instead of a foreign key relation.

    :param model: The model that this widget is for.
    :param attrs: HTML attributes for this field, same as django's.
    :param using: The database to use. Defaults to None.
    :param limit_choices_to: Keyword arguments that you would like \
    passed as part of the query string.
    :param view: The string name of the view that will be used for \
    getting the api url. Defaults to 'main'.
    :param api_url: The api url. This is only used if the automatic url \
    discovery fails.
    :param add_view: The string name of the view that will be used for \
    getting the add url. Defaults to 'add'.
    :param add_url: The url for adding a new item. This is only used \
    if the automatic url discovery fails.
    """

    def __init__(self, model, attrs=None, using=None,
                    limit_choices_to=None,
                    view="main", api_url='',
                    add_view="add", add_url=''):
        super(APIChoiceWidget, self).__init__(attrs=attrs)
        self.limit_choices_to = limit_choices_to
        self.model = model
        self.db = using

        self.view = view
        self.add_view = add_view

        self._api_link = api_url
        self._add_link = add_url


    def get_qs(self):
        return url_params_from_lookup_dict(self.limit_choices_to)

    def label_for_value(self, value):
        return super(APIModelChoiceWidget,
                        self).label_for_value(value, key='pk')


class HiddenTextInput(widgets.HiddenInput):
    """
    Widget for order fields in lists. Inherits from HiddenInput
    so it is marked as hidden in the form, but uses a 'text' input
    type with a class attribute in the rendered html of
    *orderfield*.
    """

    input_type = 'text'

    def __init__(self, *args, **kwargs):
        super(HiddenTextInput, self).__init__(*args, **kwargs)
        self.attrs['class'] = 'orderfield'

class HTMLWidget(widgets.Textarea):
    """
    WYSIWYG Widget. Adds *widget-wysiwyg* to the class attribute
    in the rendered html.
    """

    def __init__(self, *args, **kwargs):
        super(HTMLWidget, self).__init__(*args, **kwargs)
        classes = ["widget-wysiwyg"]
        if self.attrs.get('class'):
            classes.append(self.attrs.get('class'))
        self.attrs['class'] = " ".join(classes)
