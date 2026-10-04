import PublicIcon from "@mui/icons-material/Public";
import { Chip, Table, TableBody, TableCell, TableHead, TableRow, TextField, Typography } from "@mui/material";
import { ReactNode } from "react";
import { Labeled, NumberField, NumberInput, useRecordContext } from "react-admin";
import { useFormContext, useWatch } from "react-hook-form";

import { validate_0_999999, validate_1_999999 } from "../../custom_validators";
import { getServerDate, getServerTimeZone, getServerTimeZoneOffset } from "../../time_zone";

type Schedule = {
    label: string;
    // Prefix of the <source>_crontab_hour and <source>_crontab_minute settings
    source: string;
    shown?: (settings: any) => boolean;
};

const SCHEDULES: Schedule[] = [
    { label: "Risk acceptance expiry", source: "risk_acceptance_expiry" },
    {
        label: "License data import",
        source: "license_import",
        shown: (settings) => settings.feature_license_management,
    },
    { label: "Branch housekeeping", source: "branch_housekeeping" },
    { label: "EPSS and exploit import", source: "background_epss_import" },
    {
        label: "API import, OSV and VulnerableCode scans",
        source: "api_import",
        shown: (settings) => settings.feature_automatic_api_import || settings.feature_automatic_osv_scanning,
    },
];

const pad = (value: number) => String(value).padStart(2, "0");

const runsAt = (settings: any, schedule: Schedule) =>
    pad(settings[schedule.source + "_crontab_hour"]) + ":" + pad(settings[schedule.source + "_crontab_minute"]);

// The backend picks up a changed time only after a restart
function nextRun(at: string): string {
    const now = new Date();
    const serverTime = new Intl.DateTimeFormat("en-GB", {
        timeZone: getServerTimeZone(),
        hour: "2-digit",
        minute: "2-digit",
        hourCycle: "h23",
    }).format(now);
    const [year, month, day] = getServerDate(now).split("-").map(Number);
    return new Date(year, month - 1, at > serverTime ? day : day + 1).toLocaleDateString() + ", " + at;
}

const ServerTimeZoneChip = () => (
    <Chip
        icon={<PublicIcon />}
        label={`${getServerTimeZone()} · ${getServerTimeZoneOffset()}`}
        title="Time zone of the server, the tasks run at these times in this time zone"
        size="small"
        variant="outlined"
        sx={{ display: "flex", width: "fit-content", marginBottom: 2 }}
    />
);

interface ScheduleTableProps {
    settings: any;
    renderRunsAt: (schedule: Schedule) => ReactNode;
}

const ScheduleTable = ({ settings, renderRunsAt }: ScheduleTableProps) => (
    <Table size="small" sx={{ width: "fit-content", marginBottom: 3 }}>
        <TableHead>
            <TableRow>
                <TableCell>Task</TableCell>
                <TableCell>Runs daily at</TableCell>
                <TableCell>Next run</TableCell>
            </TableRow>
        </TableHead>
        <TableBody>
            {SCHEDULES.filter((schedule) => !schedule.shown || schedule.shown(settings)).map((schedule) => (
                <TableRow key={schedule.source}>
                    <TableCell>{schedule.label}</TableCell>
                    <TableCell>{renderRunsAt(schedule)}</TableCell>
                    <TableCell>{nextRun(runsAt(settings, schedule))}</TableCell>
                </TableRow>
            ))}
        </TableBody>
    </Table>
);

const RunsAtInput = ({ settings, schedule }: { settings: any; schedule: Schedule }) => {
    const { setValue } = useFormContext();
    return (
        <TextField
            type="time"
            size="small"
            margin="none"
            value={runsAt(settings, schedule)}
            onChange={(event) => {
                const [hour, minute] = event.target.value.split(":").map(Number);
                // A cleared input keeps the previous time
                if (!isNaN(hour) && !isNaN(minute)) {
                    setValue(schedule.source + "_crontab_hour", hour, { shouldDirty: true });
                    setValue(schedule.source + "_crontab_minute", minute, { shouldDirty: true });
                }
            }}
            slotProps={{ htmlInput: { "aria-label": schedule.label + " time" } }}
        />
    );
};

export const BackgroundTasksInputs = () => {
    const settings = useWatch();

    return (
        <>
            <ServerTimeZoneChip />
            <Typography variant="body2" sx={{ marginBottom: 3 }}>
                The settings in this section require a restart of the SecObserve backend to take effect.
            </Typography>

            <NumberInput
                source="background_product_metrics_interval_minutes"
                label="Product metrics interval (minutes)"
                min={0}
                step={1}
                validate={validate_0_999999}
                helperText="Calculate product metrics every x minutes"
                sx={{ marginBottom: 2 }}
            />

            <ScheduleTable
                settings={settings}
                renderRunsAt={(schedule) => <RunsAtInput settings={settings} schedule={schedule} />}
            />

            <NumberInput
                source="periodic_task_max_entries"
                label="Number of entries of Tracked Tasks to keep per task"
                min={1}
                step={1}
                validate={validate_1_999999}
            />
        </>
    );
};

export const BackgroundTasksFields = () => {
    const settings: any = useRecordContext();
    if (!settings) {
        return null;
    }

    return (
        <>
            <ServerTimeZoneChip />
            <Labeled label="Product metrics interval (minutes)" sx={{ marginBottom: 2 }}>
                <NumberField source="background_product_metrics_interval_minutes" />
            </Labeled>

            <ScheduleTable settings={settings} renderRunsAt={(schedule) => runsAt(settings, schedule)} />

            <Labeled label="Number of entries of Tracked Tasks to keep per task">
                <NumberField source="periodic_task_max_entries" />
            </Labeled>
        </>
    );
};
