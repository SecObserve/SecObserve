import { Identifier } from "ra-core";
import { ReferenceInput } from "ra-ui-materialui";

import { AutocompleteInputMedium, AutocompleteInputWide } from "../layout/themes";

interface ServiceReferenceInputProps {
    product: Identifier;
    source: string;
    alwaysOn?: boolean;
}

export const ServiceReferenceInput = ({ product, source, alwaysOn }: ServiceReferenceInputProps) => {
    return (
        <ReferenceInput
            source={source}
            reference="services"
            queryOptions={{ meta: { api_resource: "service_names" } }}
            sort={{ field: "name", order: "ASC" }}
            filter={{ product: product }}
            alwaysOn={alwaysOn}
        >
            {alwaysOn && <AutocompleteInputMedium optionText="name" label="Service" />}
            {!alwaysOn && <AutocompleteInputWide optionText="name" label="Service" />}
        </ReferenceInput>
    );
};
