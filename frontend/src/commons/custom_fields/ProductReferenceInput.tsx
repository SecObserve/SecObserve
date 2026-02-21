import { ReferenceInput } from "ra-ui-materialui";

import { AutocompleteInputMedium, AutocompleteInputWide } from "../layout/themes";

interface ProductReferenceInputProps {
    alwaysOn?: boolean;
    defaultValue?: string;
    disabled?: boolean;
}

export const ProductReferenceInput = ({ alwaysOn, defaultValue, disabled }: ProductReferenceInputProps) => {
    return (
        <ReferenceInput
            source="product"
            reference="products"
            queryOptions={{ meta: { api_resource: "product_names" } }}
            sort={{ field: "name", order: "ASC" }}
            alwaysOn={alwaysOn}
        >
            {alwaysOn && <AutocompleteInputMedium optionText="name" defaultValue={defaultValue} disabled={disabled} />}
            {!alwaysOn && <AutocompleteInputWide optionText="name" defaultValue={defaultValue} disabled={disabled} />}
        </ReferenceInput>
    );
};
