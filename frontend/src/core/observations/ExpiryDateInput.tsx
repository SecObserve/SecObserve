import { useEffect } from "react";
import { DateInput } from "react-admin";
import { useFormContext, useWatch } from "react-hook-form";

import { validate_after_today } from "../../commons/custom_validators";
import { OBSERVATION_STATUS_NOT_AFFECTED, OBSERVATION_STATUS_RISK_ACCEPTED } from "../types";

type ExpiryDateInputProps = {
    statusSource: string;
    riskAcceptanceExpiryDate: string | null;
    notAffectedExpiryDate: string | null;
    currentStatus?: string;
    currentExpiryDate?: string | null;
};

// A form initialised with a record ignores defaultValue when the record holds null, so the date is set explicitly.
const ExpiryDateInput = ({
    statusSource,
    riskAcceptanceExpiryDate,
    notAffectedExpiryDate,
    currentStatus,
    currentExpiryDate,
}: ExpiryDateInputProps) => {
    const status = useWatch({ name: statusSource });
    const { setValue } = useFormContext();
    let calculatedExpiryDate = null;
    if (status === OBSERVATION_STATUS_RISK_ACCEPTED) {
        calculatedExpiryDate = riskAcceptanceExpiryDate;
    } else if (status === OBSERVATION_STATUS_NOT_AFFECTED) {
        calculatedExpiryDate = notAffectedExpiryDate;
    }

    useEffect(() => {
        if (status) {
            setValue(
                "risk_acceptance_expiry_date",
                status === currentStatus ? (currentExpiryDate ?? null) : calculatedExpiryDate
            );
        }
    }, [status, currentStatus, currentExpiryDate, calculatedExpiryDate, setValue]);

    if (!calculatedExpiryDate) {
        return null;
    }
    return <DateInput source="risk_acceptance_expiry_date" label="Expiry date" validate={validate_after_today()} />;
};

export default ExpiryDateInput;
