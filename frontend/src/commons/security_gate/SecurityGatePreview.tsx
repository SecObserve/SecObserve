import RefreshIcon from "@mui/icons-material/Refresh";
import {
    Button,
    Chip,
    Paper,
    Stack,
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableRow,
    Typography,
} from "@mui/material";
import { useEffect, useState } from "react";
import { Identifier, useNotify, useRecordContext, useResourceContext } from "react-admin";
import { useFormContext } from "react-hook-form";

import { httpClient } from "../ra-data-django-rest-framework";
import { SeverityChip, ThresholdChip } from "./SecurityGateChips";
import {
    SECURITY_GATE_SEVERITIES,
    SecurityGatePreviewRow,
    cleanSecurityGateConditions,
    thresholdSource,
} from "./conditions";

/** A draft is posted, without one the configured gate is read, which every viewer of a product may do. */
const fetchPreview = (resource: string, id: Identifier, draft?: object): Promise<SecurityGatePreviewRow[]> =>
    httpClient(`${window.__RUNTIME_CONFIG__.API_BASE_URL}/${resource}/${id}/security_gate_preview/`, {
        method: draft ? "POST" : "GET",
        body: draft ? JSON.stringify(draft) : undefined,
    }).then((response) => response.json);

const PreviewTable = ({ rows }: { rows: SecurityGatePreviewRow[] }) => (
    <Table size="small">
        <TableHead>
            <TableRow>
                <TableCell>Severity</TableCell>
                <TableCell align="right">Counted</TableCell>
                <TableCell align="right">Active</TableCell>
                <TableCell>Threshold</TableCell>
                <TableCell>Result</TableCell>
            </TableRow>
        </TableHead>
        <TableBody>
            {rows.map((row) => (
                <TableRow key={row.severity}>
                    <TableCell>
                        <SeverityChip severity={row.severity} />
                    </TableCell>
                    <TableCell align="right">{row.counted.toLocaleString()}</TableCell>
                    <TableCell align="right">{row.active.toLocaleString()}</TableCell>
                    <TableCell>
                        <ThresholdChip threshold={row.threshold} />
                    </TableCell>
                    <TableCell>
                        <Chip
                            size="small"
                            label={row.passed ? "Passed" : "Failed"}
                            sx={{ backgroundColor: row.passed ? "#00aa00" : "#d4333f", color: "white" }}
                        />
                    </TableCell>
                </TableRow>
            ))}
        </TableBody>
    </Table>
);

type PreviewPanelProps = {
    title: string;
    rows: SecurityGatePreviewRow[] | null;
    onRefresh?: () => void;
};

const PreviewPanel = ({ title, rows, onRefresh }: PreviewPanelProps) => (
    <Paper variant="outlined" sx={{ padding: 2 }}>
        <Stack direction="row" spacing={2} sx={{ alignItems: "center", justifyContent: "space-between" }}>
            <Stack>
                <Typography variant="subtitle2">{title}</Typography>
                <Typography variant="caption" color="text.secondary">
                    Active observations of the default branches
                </Typography>
            </Stack>
            {onRefresh && (
                <Button
                    variant="outlined"
                    size="small"
                    startIcon={<RefreshIcon />}
                    onClick={onRefresh}
                    sx={{ textTransform: "none" }}
                >
                    Refresh
                </Button>
            )}
        </Stack>
        {rows ? (
            <PreviewTable rows={rows} />
        ) : (
            <Typography variant="body2" color="text.secondary" sx={{ marginTop: 1 }}>
                {onRefresh ? "Refresh to preview the counts" : "Loading..."}
            </Typography>
        )}
    </Paper>
);

/** Previews the gate as it is being edited; the form values are sent, nothing is saved. */
export const SecurityGateDraftPreview = () => {
    const record = useRecordContext();
    const resource = useResourceContext();
    const { getValues } = useFormContext();
    const notify = useNotify();
    const [rows, setRows] = useState<SecurityGatePreviewRow[] | null>(null);

    if (!record?.id || !resource) {
        return null;
    }

    const refresh = () => {
        const values = getValues();
        const body: any = {
            security_gate_advanced: Boolean(values.security_gate_advanced),
            security_gate_conditions: values.security_gate_conditions ?? {},
        };
        cleanSecurityGateConditions(body);
        for (const severity of SECURITY_GATE_SEVERITIES) {
            const threshold = values[thresholdSource(severity)];
            if (threshold != null && threshold !== "") {
                body[thresholdSource(severity)] = threshold;
            }
        }
        fetchPreview(resource, record.id, body)
            .then(setRows)
            .catch((error) => notify(error?.message ?? "Preview failed", { type: "warning" }));
    };

    return <PreviewPanel title="Preview" rows={rows} onRefresh={refresh} />;
};

/** Shows why the configured gate of a product passes or fails. */
export const SecurityGatePreview = () => {
    const record = useRecordContext();
    const notify = useNotify();
    const [rows, setRows] = useState<SecurityGatePreviewRow[] | null>(null);

    useEffect(() => {
        if (record?.id) {
            fetchPreview("products", record.id)
                .then(setRows)
                .catch((error) => notify(error?.message ?? "Preview failed", { type: "warning" }));
        }
    }, [record?.id, notify]);

    if (!record?.id) {
        return null;
    }

    return <PreviewPanel title={record.security_gate_passed ? "Why it passes" : "Why it fails"} rows={rows} />;
};
