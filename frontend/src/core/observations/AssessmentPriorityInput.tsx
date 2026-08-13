import { Fragment } from "react";
import { BooleanInput, NumberInput } from "react-admin";
import { useWatch } from "react-hook-form";

const AssessmentPriorityInput = () => {
    const change_priority = useWatch({ name: "change_priority" });

    return (
        <Fragment>
            <BooleanInput source="change_priority" label="Change priority" defaultValue={false} />
            {change_priority && (
                <NumberInput
                    source="priority"
                    step={1}
                    min={1}
                    max={99}
                    helperText="Leave empty to remove the priority"
                    sx={{ width: "7em" }}
                />
            )}
        </Fragment>
    );
};

export default AssessmentPriorityInput;
