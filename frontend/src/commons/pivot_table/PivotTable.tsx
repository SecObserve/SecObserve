import PivotTableChartIcon from "@mui/icons-material/PivotTableChart";
import UploadIcon from "@mui/icons-material/Upload";
import { Box, CircularProgress, Paper, Typography } from "@mui/material";
import Papa from "papaparse";
import { Fragment, useCallback, useEffect, useState } from "react";
import { useNotify } from "react-admin";
import { useDropzone } from "react-dropzone";
import PivotTableUI from "react-pivottable/PivotTableUI";
import { useSearchParams } from "react-router-dom";

import axios_instance from "../../access_control/auth_provider/axios_instance";
import { getResolvedSettingTheme } from "../user_settings/functions";
import "./PivotTable.css";

// Whitelist of default aggregator names provided by react-pivottable
const DEFAULT_AGGREGATORS = [
    "Count",
    "Count Unique Values",
    "List Unique Values",
    "Sum",
    "Integer Sum",
    "Average",
    "Median",
    "Sample Variance",
    "Sample Standard Deviation",
    "Minimum",
    "Maximum",
    "First",
    "Last",
    "Sum over Sum",
    "Sum as Fraction of Total",
    "Sum as Fraction of Rows",
    "Sum as Fraction of Columns",
    "Count as Fraction of Total",
    "Count as Fraction of Rows",
    "Count as Fraction of Columns",
] as const;

// Whitelist of pivot config fields that are plain-data and safe to JSON.stringify.
// react-pivottable's onChange passes back the entire merged props (including
// `aggregators`, `renderers`, `sorters`, `derivedAttributes` — all objects of
// functions). JSON.stringify silently drops functions, so persisting those keys
// would store empty objects that override the library defaults on reload.
const PERSISTED_KEYS = [
    "rows",
    "cols",
    "vals",
    "rendererName",
    "valueFilter",
    "rowOrder",
    "colOrder",
    "unusedAttrsVertical",
    "menuLimit",
    "hiddenAttributes",
    "hiddenFromAggregators",
    "hiddenFromDragDrop",
] as const;

const sanitizePivotConfig = (raw: Record<string, unknown>): Record<string, unknown> => {
    const sanitized: Record<string, unknown> = {};
    for (const k of PERSISTED_KEYS) {
        if (k in raw) sanitized[k] = raw[k];
    }
    const aggName = raw.aggregatorName;
    if (typeof aggName === "string" && (DEFAULT_AGGREGATORS as readonly string[]).includes(aggName)) {
        sanitized.aggregatorName = aggName;
    }
    return sanitized;
};

const PivotTable = () => {
    const [data, setData] = useState([]);
    const [loading, setLoading] = useState(false);
    const [searchParams] = useSearchParams();
    const notify = useNotify();

    const hasQueryParams = searchParams.toString().length > 0;

    // Derive a stable, canonical key from the search params to scope pivot state per query
    const paramsKey = (() => {
        if (!hasQueryParams) return null;
        const sorted = new URLSearchParams(searchParams.toString());
        sorted.sort();
        return `pivot_state:${sorted.toString()}`;
    })();

    // Only track pivot _configuration_ (rows, cols, vals, aggregatorName, filters, …).
    // The actual dataset lives in `data` state and must NOT be serialized (it overflows localStorage).
    const [pivotConfig, setPivotConfig] = useState<Record<string, unknown>>({});
    const [lastLoadedParamsKey, setLastLoadedParamsKey] = useState<string | null>(null);

    // Load stored config (for the current paramsKey) whenever it changes
    useEffect(() => {
        if (!paramsKey) {
            setPivotConfig({});
            setData([]);
            setLastLoadedParamsKey(null);
            return;
        }
        if (paramsKey === lastLoadedParamsKey) return; // already loaded for this key

        const saved = localStorage.getItem(paramsKey);
        setPivotConfig(saved ? sanitizePivotConfig(JSON.parse(saved)) : {});
        setLastLoadedParamsKey(paramsKey);
    }, [paramsKey]);

    // Persist pivot config to localStorage whenever it changes
    useEffect(() => {
        if (!paramsKey) return;
        if (Object.keys(pivotConfig).length === 0) return;
        localStorage.setItem(paramsKey, JSON.stringify(pivotConfig));
    }, [paramsKey, pivotConfig]);

    const handlePivotChange = useCallback((newState: Record<string, unknown>) => {
        setPivotConfig(sanitizePivotConfig(newState));
    }, []);

    const onDrop = useCallback(
        (acceptedFiles: File[]) => {
            const file = acceptedFiles[0];
            if (!file) return;

            Papa.parse(file, {
                header: true,
                skipEmptyLines: true,
                dynamicTyping: true,
                complete: (results: any) => {
                    if (results.error) {
                        notify(`Failed to parse CSV file: ${results.error.message}`, {
                            type: "error",
                        });
                        return;
                    }
                    setData(results.data);
                },
            });
        },
        [notify]
    );

    // Fetch data from API when query parameters are present
    useEffect(() => {
        if (!hasQueryParams) {
            return;
        }

        let isMounted = true;

        const fetchData = async () => {
            setLoading(true);

            try {
                const query = searchParams.toString();
                const url = `/observations/export_csv/?${query}`;

                const response = await axios_instance.get(url, {
                    responseType: "blob",
                });

                // Create a blob from the response and convert to text
                const csvText = await response.data.text();

                if (!isMounted) return;

                const results = Papa.parse(csvText, {
                    header: true,
                    skipEmptyLines: true,
                    dynamicTyping: true,
                    complete: (results: any) => {
                        if (results.error) {
                            notify(`Failed to parse CSV file: ${results.error.message}`, {
                                type: "error",
                            });
                        }
                        setData(results.data);
                    },
                });

                setData(results.data);
                setLoading(false);
            } catch (err) {
                if (!isMounted) return;
                notify(err instanceof Error ? err.message : "Failed to load data", {
                    type: "error",
                });
                setLoading(false);
            }
        };

        fetchData();

        return () => {
            isMounted = false;
        };
    }, [hasQueryParams, searchParams, notify]);

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: { "text/csv": [".csv"] },
        multiple: false,
    });

    return (
        <Paper sx={{ marginTop: 2, padding: 2 }} className={getResolvedSettingTheme() === "dark" ? "pvt-dark" : undefined}>
            <Typography variant="h6" alignItems="center" display={"flex"} sx={{ marginBottom: 2 }}>
                <Fragment>
                    <PivotTableChartIcon />
                    &nbsp;&nbsp;{hasQueryParams ? "Pivot Table for Observations" : "Pivot Table"}
                </Fragment>
            </Typography>

            {hasQueryParams ? (
                // API mode: show loading indicator or error
                <Box sx={{ textAlign: "center", py: 4 }}>
                    {loading && (
                        <Box sx={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 2 }}>
                            <CircularProgress size={30} />
                            <Typography color="text.secondary">Loading observations ...</Typography>
                        </Box>
                    )}
                </Box>
            ) : (
                // File upload mode
                <Paper
                    {...getRootProps()}
                    variant="outlined"
                    sx={{
                        padding: 2,
                        marginBottom: 2,
                        textAlign: "center",
                        cursor: "pointer",
                        bgcolor: isDragActive ? "action.hover" : "background.paper",
                        "&:hover": { bgcolor: "action.hover" },
                        width: "30em",
                    }}
                >
                    <input {...getInputProps()} />
                    <UploadIcon sx={{ fontSize: 30, color: "text.secondary", mb: 1 }} />
                    <Typography color="text.secondary">
                        {isDragActive ? "Drop the CSV file here..." : "Drag & drop a CSV file here, or click to select"}
                    </Typography>
                </Paper>
            )}

            {data.length > 0 && (!hasQueryParams || !loading) && (
                <PivotTableUI
                    data={data}
                    unusedOrientationCutoff={Infinity}
                    onChange={handlePivotChange}
                    {...pivotConfig}
                />
            )}
        </Paper>
    );
};

export default PivotTable;
