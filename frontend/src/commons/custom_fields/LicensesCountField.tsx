import { RaRecord, useRecordContext } from "react-admin";

import {
    EVALUATION_RESULT_ALLOWED,
    EVALUATION_RESULT_FORBIDDEN,
    EVALUATION_RESULT_IGNORED,
    EVALUATION_RESULT_REVIEW_REQUIRED,
    EVALUATION_RESULT_UNKNOWN,
} from "../../licenses/types";
import { get_evaluation_result_color } from "../functions";

interface LicensesCountProps {
    label: string;
    withLabel: boolean;
    record?: RaRecord;
}

const LicensesCountField = (props: LicensesCountProps) => {
    const record = useRecordContext(props);

    function get_margin(): number {
        if (props.withLabel) {
            return 8;
        } else {
            return 0;
        }
    }

    return record &&
        record.forbidden_licenses_count +
            record.review_required_licenses_count +
            record.unknown_licenses_count +
            record.allowed_licenses_count +
            record.ignored_licenses_count >
            0 ? (
        <div style={{ marginTop: get_margin() }}>
            <span
                style={{
                    background: get_evaluation_result_color(null, EVALUATION_RESULT_FORBIDDEN),
                    color: "white",
                    padding: 8,
                }}
            >
                {record.forbidden_licenses_count}
            </span>
            <span
                style={{
                    background: get_evaluation_result_color(null, EVALUATION_RESULT_REVIEW_REQUIRED),
                    color: "white",
                    padding: 8,
                }}
            >
                {record.review_required_licenses_count}
            </span>
            <span
                style={{
                    background: get_evaluation_result_color(null, EVALUATION_RESULT_UNKNOWN),
                    color: "white",
                    padding: 8,
                }}
            >
                {record.unknown_licenses_count}
            </span>
            <span
                style={{
                    background: get_evaluation_result_color(null, EVALUATION_RESULT_ALLOWED),
                    color: "white",
                    padding: 8,
                }}
            >
                {record.allowed_licenses_count}
            </span>
            <span
                style={{
                    background: get_evaluation_result_color(null, EVALUATION_RESULT_IGNORED),
                    color: "white",
                    padding: 8,
                }}
            >
                {record.ignored_licenses_count}
            </span>
        </div>
    ) : null;
};

export default LicensesCountField;
