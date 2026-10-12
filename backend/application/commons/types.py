from typing import Optional


class Age_Choices:
    AGE_DAY = "Today"
    AGE_WEEK = "Past 7 days"
    AGE_MONTH = "Past 30 days"
    AGE_QUARTER = "Past 90 days"
    AGE_YEAR = "Past 365 days"

    AGE_CHOICES = [
        (AGE_DAY, AGE_DAY),
        (AGE_WEEK, AGE_WEEK),
        (AGE_MONTH, AGE_MONTH),
        (AGE_QUARTER, AGE_QUARTER),
        (AGE_YEAR, AGE_YEAR),
    ]

    @classmethod
    def get_days_from_age(cls, value: "Age_Choices") -> Optional[int]:
        if value == cls.AGE_DAY:
            days = 0
        elif value == cls.AGE_WEEK:
            days = 7
        elif value == cls.AGE_MONTH:
            days = 30
        elif value == cls.AGE_QUARTER:
            days = 90
        elif value == cls.AGE_YEAR:
            days = 365
        else:
            days = None
        return days


class VEX_Justification_Styles:
    STYLE_CSAF_OPENVEX = "CSAF/OpenVEX"
    STYLE_CYCLONEDX = "CycloneDX"

    STYLE_CHOICES = [
        (STYLE_CSAF_OPENVEX, STYLE_CSAF_OPENVEX),
        (STYLE_CYCLONEDX, STYLE_CYCLONEDX),
    ]


class Date_Format_Choices:
    DATE_FORMAT_ISO8601 = "ISO8601"
    DATE_FORMAT_BROWSER = "BROWSER"
    DATE_FORMAT_US = "US"
    DATE_FORMAT_UK = "UK"
    DATE_FORMAT_EUROPE = "EUROPE"

    DATE_FORMAT_CHOICES = [
        (DATE_FORMAT_ISO8601, "ISO 8601 (2024-12-31 23:59:59)"),
        (DATE_FORMAT_BROWSER, "Browser locale"),
        (DATE_FORMAT_US, "US (12/31/2024, 11:59:59 PM)"),
        (DATE_FORMAT_UK, "UK (31/12/2024, 23:59:59)"),
        (DATE_FORMAT_EUROPE, "Europe (31.12.2024, 23:59:59)"),
    ]
