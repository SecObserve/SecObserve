import { DateField, DateFieldProps } from "react-admin";

import { getServerTimeZone } from "../time_zone";

// For timestamps only: a plain date has no time zone and stays a DateField
export const DateTimeField = (props: DateFieldProps) => (
    <DateField showTime options={{ timeZone: getServerTimeZone() }} {...props} />
);
