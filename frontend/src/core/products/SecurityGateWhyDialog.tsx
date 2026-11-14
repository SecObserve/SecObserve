import InfoOutlinedIcon from "@mui/icons-material/InfoOutlined";
import {
    Button,
    Chip,
    Dialog,
    DialogContent,
    DialogTitle,
    IconButton,
    Stack,
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableRow,
    Tooltip,
    Typography,
} from "@mui/material";
import { Fragment, useState } from "react";
import { useNotify } from "react-admin";
import { useNavigate } from "react-router";

import { httpClient } from "../../commons/ra-data-django-rest-framework";
import observations from "../observations";
import { OBSERVATION_STATUS_ACTIVE, Product } from "../types";

type SecurityGateCountRow = {
    severity: string | null;
    priority: number | null;
    count: number;
    threshold: number;
    passed: boolean;
};

const failingObservationsUrl = (product: Product) => {
    const filter = {
        current_status: OBSERVATION_STATUS_ACTIVE,
        fails_security_gate: true,
        ...(product.repository_default_branch ? { branch: product.repository_default_branch } : {}),
    };
    return `/products/${product.id}/show?displayedFilters=%7B%7D&filter=${encodeURIComponent(JSON.stringify(filter))}&order=ASC&sort=current_severity`;
};

const CountsTable = ({ rows }: { rows: SecurityGateCountRow[] }) => (
    <Table size="small">
        <TableHead>
            <TableRow>
                <TableCell>Severity / Priority</TableCell>
                <TableCell align="right">Count</TableCell>
                <TableCell align="right">Threshold</TableCell>
                <TableCell>Result</TableCell>
            </TableRow>
        </TableHead>
        <TableBody>
            {rows.map((row) => (
                <TableRow key={row.severity ?? `priority-${row.priority}`}>
                    <TableCell>{row.severity ?? `Priority ${row.priority}`}</TableCell>
                    <TableCell align="right">{row.count.toLocaleString()}</TableCell>
                    <TableCell align="right">{row.threshold.toLocaleString()}</TableCell>
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

/** Explains the gate in the product header: the active observations of the default branch against each threshold. */
const SecurityGateWhyDialog = ({ product }: { product: Product }) => {
    const [open, setOpen] = useState(false);
    const [rows, setRows] = useState<SecurityGateCountRow[] | null>(null);
    const navigate = useNavigate();
    const notify = useNotify();

    const openDialog = () => {
        setOpen(true);
        setRows(null);
        httpClient(`${window.__RUNTIME_CONFIG__.API_BASE_URL}/products/${product.id}/security_gate_counts/`)
            .then((response) => setRows(response.json))
            .catch((error) => {
                setOpen(false);
                notify(error?.message ?? "Security gate counts could not be loaded", { type: "warning" });
            });
    };

    return (
        <Fragment>
            <Tooltip title="Why?">
                <IconButton size="small" aria-label="Why?" onClick={openDialog}>
                    <InfoOutlinedIcon fontSize="small" />
                </IconButton>
            </Tooltip>
            <Dialog open={open} onClose={() => setOpen(false)} maxWidth="sm" fullWidth>
                <DialogTitle>Security gate</DialogTitle>
                <DialogContent>
                    <Stack spacing={2} sx={{ alignItems: "flex-start" }}>
                        {rows == null && (
                            <Typography variant="body2" color="text.secondary">
                                Loading...
                            </Typography>
                        )}
                        {rows?.length === 0 && (
                            <Typography variant="body2" color="text.secondary">
                                No security gate
                            </Typography>
                        )}
                        {rows?.length ? <CountsTable rows={rows} /> : null}
                        <Button
                            variant="outlined"
                            size="small"
                            startIcon={<observations.icon />}
                            onClick={() => {
                                setOpen(false);
                                navigate(failingObservationsUrl(product));
                            }}
                            sx={{ textTransform: "none" }}
                        >
                            Show failing observations
                        </Button>
                    </Stack>
                </DialogContent>
            </Dialog>
        </Fragment>
    );
};

export default SecurityGateWhyDialog;
