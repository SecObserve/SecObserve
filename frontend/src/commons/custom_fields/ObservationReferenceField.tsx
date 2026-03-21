import { Typography } from "@mui/material";
import { ReferenceField } from "react-admin";

import { useLinkStyles } from "../layout/themes";
import { getResolvedSettingTheme } from "../user_settings/functions";

interface ObservationReferenceFieldProps {
    source: string;
    label?: string;
}

export const ObservationReferenceField = ({ source, label }: ObservationReferenceFieldProps) => {
    const { classes } = useLinkStyles({ setting_theme: getResolvedSettingTheme() });
    label = label === undefined ? "Observation" : label;

    return (
        <ReferenceField
            source={source}
            reference="observations"
            queryOptions={{ meta: { api_resource: "observation_titles" } }}
            link="show"
            sx={{ "& a": { textDecoration: "none" } }}
            label={label}
            render={({ error, isPending, referenceRecord }) => {
                if (isPending) {
                    return <Typography variant="body2">Loading...</Typography>;
                }
                if (error) {
                    return <Typography variant="body2">{error.message}</Typography>;
                }
                return (
                    <Typography variant="body2" className={classes.link}>
                        {referenceRecord?.title}
                    </Typography>
                );
            }}
        />
    );
};
