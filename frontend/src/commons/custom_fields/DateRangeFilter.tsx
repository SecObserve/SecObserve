import CalendarMonthIcon from "@mui/icons-material/CalendarMonth";
import {
    Button,
    Chip,
    InputAdornment,
    Popover,
    Stack,
    TextField,
    ToggleButton,
    ToggleButtonGroup,
} from "@mui/material";
import { KeyboardEvent, MouseEvent, useState } from "react";
import { useListContext } from "react-admin";

// The filter state keeps the token, so saved queries and shared links stay relative.
const PRESETS = [
    { token: "Today", label: "Today", days: 0, age: "Today" },
    { token: "7 days", label: "Last 7 days", days: 7, age: "Past 7 days" },
    { token: "30 days", label: "Last 30 days", days: 30, age: "Past 30 days" },
    { token: "90 days", label: "Last 90 days", days: 90, age: "Past 90 days" },
    { token: "1 year", label: "Last year", days: 365, age: "Past 365 days" },
];

const DATE_SOURCES = ["created", "last_observation_log"];
// Its presets are sent as the existing age filter, to keep the backend's semantics of the last change.
const AGE_SOURCE = "last_observation_log";

const DAY = /^\d{4}-\d{2}-\d{2}$/;

// The only place that decides in which time zone a calendar day starts.
export const startOfDay = (day?: string, addDays = 0): Date => {
    const date = day ? new Date(day + "T00:00:00") : new Date();
    return new Date(date.getFullYear(), date.getMonth(), date.getDate() + addDays);
};

// A custom range is stored as "2026-09-26..2026-10-02", either side may be empty.
const parseRange = (value: unknown): [string, string] | undefined => {
    if (typeof value !== "string") {
        return undefined;
    }
    const [from = "", to = "", ...rest] = value.split("..");
    const isDay = (day: string) => day === "" || (DAY.test(day) && !isNaN(startOfDay(day).getTime()));
    if (rest.length > 0 || (!from && !to) || !isDay(from) || !isDay(to)) {
        return undefined;
    }
    return [from, to];
};

const dateParams = (source: string, value: unknown): [string, string][] => {
    const preset = PRESETS.find((preset) => preset.token === value);
    if (preset) {
        if (source === AGE_SOURCE) {
            return [["age", preset.age]];
        }
        return [[source + "_after", startOfDay(undefined, -preset.days).toISOString()]];
    }
    const range = parseRange(value);
    if (!range) {
        return [];
    }
    const params: [string, string][] = [];
    if (range[0]) {
        params.push([source + "_after", startOfDay(range[0]).toISOString()]);
    }
    if (range[1]) {
        params.push([source + "_before", new Date(startOfDay(range[1], 1).getTime() - 1).toISOString()]);
    }
    return params;
};

// Resolves the stored date filters to API parameters, at the time of the request.
export const resolveDateFilters = (filter: Record<string, any>): Record<string, any> =>
    Object.fromEntries(
        Object.entries(filter).flatMap(([key, value]) =>
            DATE_SOURCES.includes(key) ? dateParams(key, value) : [[key, value]]
        )
    );

const formatDay = (day: string, withYear: boolean) =>
    new Date(day + "T00:00:00").toLocaleDateString(undefined, {
        day: "2-digit",
        month: "2-digit",
        year: withYear ? "numeric" : undefined,
    });

const displayValue = (value: unknown): string => {
    const preset = PRESETS.find((preset) => preset.token === value);
    if (preset) {
        return preset.label;
    }
    const range = parseRange(value);
    if (!range) {
        return "";
    }
    const [from, to] = range;
    if (from && to) {
        return formatDay(from, from.slice(0, 4) !== to.slice(0, 4)) + " – " + formatDay(to, true);
    }
    return from ? "From " + formatDay(from, true) : "Until " + formatDay(to, true);
};

type DateRangeField = {
    source: string;
    label: string;
};

interface DateRangeFilterProps {
    fields: DateRangeField[];
    alwaysOn?: boolean;
}

export const DateRangeFilter = ({ fields }: DateRangeFilterProps) => {
    const { filterValues, displayedFilters, setFilters } = useListContext();
    const [anchorEl, setAnchorEl] = useState<HTMLElement | null>(null);
    const [source, setSource] = useState(fields[0].source);
    const [from, setFrom] = useState("");
    const [to, setTo] = useState("");

    const handlesAge = fields.some((field) => field.source === AGE_SOURCE);
    const values = new Map(Object.entries(filterValues));
    let field = fields.find((field) => values.get(field.source));
    let value = field ? values.get(field.source) : undefined;
    // Stored filters from before this control still carry the age filter
    const agePreset = PRESETS.find((preset) => preset.age === filterValues.age);
    if (!field && handlesAge && agePreset) {
        field = fields.find((field) => field.source === AGE_SOURCE);
        value = agePreset.token;
    }
    const current = field ?? fields[0];
    const text = displayValue(value);

    const open = (event: MouseEvent<HTMLElement> | KeyboardEvent<HTMLElement>) => {
        const range = parseRange(value);
        setSource(current.source);
        setFrom(range ? range[0] : "");
        setTo(range ? range[1] : "");
        setAnchorEl(event.currentTarget);
    };

    const apply = (newValue?: string) => {
        const remaining = Object.fromEntries(
            Object.entries(filterValues).filter(
                ([key]) => !fields.some((field) => field.source === key) && !(handlesAge && key === "age")
            )
        );
        setFilters(newValue ? { ...remaining, [source]: newValue } : remaining, displayedFilters);
        setAnchorEl(null);
    };

    return (
        <>
            <TextField
                label={current.label}
                value={text}
                size="small"
                margin="dense"
                onClick={open}
                onKeyDown={(event) => {
                    if (["Enter", " ", "ArrowDown"].includes(event.key)) {
                        event.preventDefault();
                        open(event);
                    }
                }}
                sx={{ width: `max(10em, ${text.length}ch + 60px)`, "& input": { cursor: "pointer" } }}
                slotProps={{
                    htmlInput: { readOnly: true, "aria-haspopup": "dialog" },
                    input: {
                        endAdornment: (
                            <InputAdornment position="end">
                                <CalendarMonthIcon fontSize="small" />
                            </InputAdornment>
                        ),
                    },
                }}
            />
            <Popover
                open={Boolean(anchorEl)}
                anchorEl={anchorEl}
                onClose={() => setAnchorEl(null)}
                anchorOrigin={{ vertical: "bottom", horizontal: "left" }}
            >
                <Stack spacing={2} sx={{ padding: 2, width: "22em" }}>
                    {fields.length > 1 && (
                        <ToggleButtonGroup
                            value={source}
                            exclusive
                            size="small"
                            fullWidth
                            onChange={(_, newSource) => newSource && setSource(newSource)}
                        >
                            {fields.map((field) => (
                                <ToggleButton key={field.source} value={field.source}>
                                    {field.label}
                                </ToggleButton>
                            ))}
                        </ToggleButtonGroup>
                    )}
                    <Stack direction="row" spacing={1} useFlexGap sx={{ flexWrap: "wrap" }}>
                        {PRESETS.map((preset) => {
                            const selected = source === current.source && value === preset.token;
                            return (
                                <Chip
                                    key={preset.token}
                                    label={preset.token}
                                    size="small"
                                    color={selected ? "primary" : "default"}
                                    variant={selected ? "filled" : "outlined"}
                                    onClick={() => apply(preset.token)}
                                />
                            );
                        })}
                    </Stack>
                    <Stack direction="row" spacing={1}>
                        <TextField
                            type="date"
                            label="From"
                            size="small"
                            value={from}
                            onChange={(event) => setFrom(event.target.value)}
                            slotProps={{ inputLabel: { shrink: true }, htmlInput: { max: to || undefined } }}
                        />
                        <TextField
                            type="date"
                            label="To"
                            size="small"
                            value={to}
                            onChange={(event) => setTo(event.target.value)}
                            slotProps={{ inputLabel: { shrink: true }, htmlInput: { min: from || undefined } }}
                        />
                    </Stack>
                    <Stack direction="row" spacing={1} sx={{ justifyContent: "flex-end" }}>
                        <Button onClick={() => apply()}>Clear</Button>
                        <Button
                            variant="contained"
                            disabled={Boolean(from && to && from > to)}
                            onClick={() => apply(from || to ? from + ".." + to : undefined)}
                        >
                            Apply
                        </Button>
                    </Stack>
                </Stack>
            </Popover>
        </>
    );
};
