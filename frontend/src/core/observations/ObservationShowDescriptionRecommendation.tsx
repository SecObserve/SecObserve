import { Stack } from "@mui/material";
import { Labeled, NumberField, useRecordContext } from "react-admin";

import MarkdownField from "../../commons/custom_fields/MarkdownField";

const ObservationShowDescriptionRecommendation = () => {
    const observation = useRecordContext();
    return (
        <Stack spacing={2}>
            {observation && observation.description != "" && (
                <Labeled>
                    <MarkdownField content={observation.description} label="Description" />
                </Labeled>
            )}
            <Stack spacing={4} direction={"row"}>
                {observation && observation?.recommendation != "" && (
                    <Labeled>
                        <MarkdownField content={observation.recommendation} label="Recommendation" />
                    </Labeled>
                )}
                {observation?.update_impact_score !== null && (
                    <Labeled>
                        <NumberField label="Update impact score" source="update_impact_score" />
                    </Labeled>
                )}
            </Stack>
        </Stack>
    );
};

export default ObservationShowDescriptionRecommendation;
