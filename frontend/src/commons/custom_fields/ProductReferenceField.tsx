import { Typography } from "@mui/material";
import { ReferenceField } from "ra-ui-materialui";

import { useLinkStyles } from "../layout/themes";
import { getResolvedSettingTheme } from "../user_settings/functions";

interface ProductReferenceFieldProps {
    link?: any;
    label?: string;
}

export const ProductReferenceField = ({ link, label }: ProductReferenceFieldProps) => {
    const { classes } = useLinkStyles({ setting_theme: getResolvedSettingTheme() });
    label = label === undefined ? "Product" : label;

    return (
        <ReferenceField
            source="product"
            reference="products"
            queryOptions={{ meta: { api_resource: "product_names" } }}
            link={link}
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
                        {referenceRecord?.name}
                    </Typography>
                );
            }}
        />
    );
};
