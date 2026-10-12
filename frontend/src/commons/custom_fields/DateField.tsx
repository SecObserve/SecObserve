import { DateFieldProps, DateField as RaDateField } from "react-admin";

import { date_format_locales, settings_date_format } from "../functions";

/**
 * A DateField that renders dates and times with the date format configured in the instance settings.
 *
 * Use this instead of the DateField of react-admin, so that all dates and times in the frontend use
 * the configured format. A date format set with the locales prop still has precedence.
 */
export const DateField = (props: DateFieldProps) => (
    <RaDateField {...props} locales={props.locales ?? date_format_locales(settings_date_format())} />
);
