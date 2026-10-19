import { Identifier } from "ra-core";
import { ReferenceInput } from "ra-ui-materialui";

import { AutocompleteInputMedium, AutocompleteInputWide } from "../layout/themes";
import { AutocompleteInputAutoWidth } from "./AutocompleteInputAutoWidth";

interface ProductGroupReferenceInputProps {
    alwaysOn?: boolean;
    autoWidth?: boolean;
    defaultValue?: Identifier;
}

export const ProductGroupReferenceInput = ({ alwaysOn, autoWidth, defaultValue }: ProductGroupReferenceInputProps) => {
    return (
        <ReferenceInput
            source="product_group"
            reference="product_groups"
            queryOptions={{ meta: { api_resource: "product_group_names" } }}
            sort={{ field: "name", order: "ASC" }}
            alwaysOn={alwaysOn}
        >
            {alwaysOn && autoWidth && <AutocompleteInputAutoWidth optionText="name" defaultValue={defaultValue} />}
            {alwaysOn && !autoWidth && <AutocompleteInputMedium optionText="name" defaultValue={defaultValue} />}
            {!alwaysOn && <AutocompleteInputWide optionText="name" defaultValue={defaultValue} />}
        </ReferenceInput>
    );
};
