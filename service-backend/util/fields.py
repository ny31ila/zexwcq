# service-backend/util/fields.py
"""
Custom serializer fields for the project.
This file will contain fields that handle specific data type conversions,
like Jalali dates.
"""
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
import jdatetime
from datetime import datetime, date

class JalaliDateField(serializers.DateField):
    """
    A DateField that accepts and returns Jalali dates in the format 'YYYY/MM/DD'.
    Internally stores and works with Gregorian dates.
    """
    default_error_messages = {
        'invalid': _('Date has wrong format. Use one of the formats YYYY/MM/DD.'),
    }

    def to_representation(self, value):
        """
        Convert Gregorian date from the model to Jalali string for API output.
        """
        if not value:
            return None
        if isinstance(value, datetime):
            value = value.date()
        if isinstance(value, date):
            try:
                jalali_date = jdatetime.date.fromgregorian(date=value)
                return jalali_date.strftime('%Y/%m/%d')
            except ValueError:
                # Handle potential conversion errors gracefully
                return None
        return None

    def to_internal_value(self, data):
        """
        Convert Jalali date string from API input to Gregorian date for the model.
        """
        if data is None or data == '':
            return None

        if isinstance(data, str):
            try:
                # Parse the Jalali date string
                year, month, day = map(int, data.split('/'))
                # Convert to Gregorian date
                gregorian_date = jdatetime.date(year, month, day).togregorian()
                return gregorian_date
            except (ValueError, TypeError):
                 self.fail('invalid')
        # If data is already a date/datetime (e.g., from partial updates), return as is
        # after validation by the parent class.
        return super().to_internal_value(data)


# If datetime fields are needed in Jalali format as well:
# class JalaliDateTimeField(serializers.DateTimeField):
#     """
#     A DateTimeField that accepts and returns Jalali datetimes.
#     Format: 'YYYY/MM/DD HH:MM:SS'
#     Internally stores and works with Gregorian datetimes.
#     """
#     # Implementation would be similar, using jdatetime.datetime
#     # and converting to/from Gregorian datetime objects.
#     pass
