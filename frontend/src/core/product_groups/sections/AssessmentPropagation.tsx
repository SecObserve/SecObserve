import { Stack } from "@mui/material";
import {
    ArrayField,
    ArrayInput,
    BooleanField,
    BooleanInput,
    Datagrid,
    FormDataConsumer,
    Labeled,
    SimpleFormIterator,
    TextField,
} from "react-admin";

import { TextInputWide } from "../../../commons/layout/themes";

export const AssessmentPropagationInputs = () => (
    <>
        <ArrayInput source="propagate_branches" label={false} defaultValue={""}>
            <SimpleFormIterator disableReordering inline>
                <TextInputWide label="Propagate to branches (regular expression)" source="propagate_to" />
            </SimpleFormIterator>
        </ArrayInput>
        <FormDataConsumer>
            {({ formData }) =>
                formData.propagate_branches &&
                formData.propagate_branches.length >= 1 && (
                    <Stack>
                        <BooleanInput
                            source="propagate_branches_new_assessment"
                            label="Propagate new assessments to other branches"
                            defaultValue={true}
                        />
                        <BooleanInput
                            source="propagate_branches_new_observation"
                            label="Propagate assessments to new observations"
                            defaultValue={true}
                        />
                    </Stack>
                )
            }
        </FormDataConsumer>
    </>
);

export const isAssessmentPropagationVisible = (product_group: any) =>
    Boolean(product_group.propagate_branches && product_group.propagate_branches.length > 0);

export const AssessmentPropagationFields = () => (
    <>
        <ArrayField source="propagate_branches">
            <Datagrid bulkActionButtons={false} rowClick={false} sx={{ paddingBottom: 2 }}>
                <TextField source="propagate_to" label="Propagate to branches" />
            </Datagrid>
        </ArrayField>
        <Stack>
            <Labeled label="Propagate new assessments to other branches">
                <BooleanField source="propagate_branches_new_assessment" />
            </Labeled>
            <Labeled label="Propagate assessments to new observations">
                <BooleanField source="propagate_branches_new_observation" />
            </Labeled>
        </Stack>
    </>
);
