import { useRecordContext } from "react-admin";

import { getSettingListSize } from "../../commons/user_settings/functions";
import {
    OBSERVATION_SEVERITY_CRITICAL,
    OBSERVATION_SEVERITY_HIGH,
    OBSERVATION_SEVERITY_LOW,
    OBSERVATION_SEVERITY_MEDIUM,
    OBSERVATION_SEVERITY_NONE,
    OBSERVATION_SEVERITY_UNKNOWN,
} from "../../core/types";
import { get_severity_color } from "../functions";

interface ObservationsProps {
    label: string;
    withLabel: boolean;
}

const ObservationsCountField = (props: ObservationsProps) => {
    const record = useRecordContext();

    function get_no_label_margin(): number {
        if (getSettingListSize() === "small" && !props.withLabel) {
            return 8;
        } else {
            return 0;
        }
    }

    function get_margin(): number {
        if (props.withLabel) {
            return 8;
        } else {
            return get_no_label_margin();
        }
    }

    return record ? (
        <div style={{ marginTop: get_margin(), marginBottom: get_no_label_margin() }}>
            <span
                style={{
                    background: get_severity_color(OBSERVATION_SEVERITY_CRITICAL),
                    color: "white",
                    padding: 8,
                }}
            >
                {record.active_critical_observation_count}
            </span>
            <span
                style={{
                    background: get_severity_color(OBSERVATION_SEVERITY_HIGH),
                    color: "white",
                    padding: 8,
                }}
            >
                {record.active_high_observation_count}
            </span>
            <span
                style={{
                    background: get_severity_color(OBSERVATION_SEVERITY_MEDIUM),
                    color: "white",
                    padding: 8,
                }}
            >
                {record.active_medium_observation_count}
            </span>
            <span
                style={{
                    background: get_severity_color(OBSERVATION_SEVERITY_LOW),
                    color: "white",
                    padding: 8,
                }}
            >
                {record.active_low_observation_count}
            </span>
            <span
                style={{
                    background: get_severity_color(OBSERVATION_SEVERITY_NONE),
                    color: "white",
                    padding: 8,
                }}
            >
                {record.active_none_observation_count}
            </span>
            <span
                style={{
                    background: get_severity_color(OBSERVATION_SEVERITY_UNKNOWN),
                    color: "white",
                    padding: 8,
                }}
            >
                {record.active_unknown_observation_count}
            </span>
        </div>
    ) : null;
};

export default ObservationsCountField;
