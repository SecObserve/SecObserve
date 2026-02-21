import { ReferenceField } from "ra-ui-materialui";

interface ProductReferenceFieldProps {
    link?: any;
    label?: string;
}

export const ProductReferenceField = ({ link, label }: ProductReferenceFieldProps) => {
    label = label === undefined ? "Product" : label;

    return (
        <ReferenceField
            source="product"
            reference="products"
            queryOptions={{ meta: { api_resource: "product_names" } }}
            link={link}
            sx={{ "& a": { textDecoration: "none" } }}
            label={label}
        />
    );
};
