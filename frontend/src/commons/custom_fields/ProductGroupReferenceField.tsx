import { ReferenceField } from "ra-ui-materialui";

interface ProductGroupReferenceFieldProps {
    link?: any;
    label?: string;
}

export const ProductGroupReferenceField = ({ link, label }: ProductGroupReferenceFieldProps) => {
    label = label === undefined ? "Product Group" : label;

    return (
        <ReferenceField
            source="product_group"
            reference="product_groups"
            queryOptions={{ meta: { api_resource: "product_group_names" } }}
            link={link}
            sx={{ "& a": { textDecoration: "none" } }}
            label={label}
        />
    );
};
