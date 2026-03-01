import { ReferenceField } from "ra-ui-materialui";

interface ObservationReferenceFieldProps {
    source: string;
    label?: string;
}

export const ObservationReferenceField = ({ source, label }: ObservationReferenceFieldProps) => {
    label = label === undefined ? "Observation" : label;

    return (
        <ReferenceField
            source={source}
            reference="observations"
            queryOptions={{ meta: { api_resource: "observation_titles" } }}
            link="show"
            sx={{ "& a": { textDecoration: "none" } }}
            label={label}
        />
    );
};
