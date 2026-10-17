import FilterListIcon from "@mui/icons-material/FilterList";
import { Badge, Box, Button, Chip, Divider, Popover, Stack, Typography } from "@mui/material";
import queryString from "query-string";
import { ReactElement, useState } from "react";
import {
    AddSavedQueryDialog,
    FilterForm,
    FilterLiveForm,
    Identifier,
    RemoveSavedQueryDialog,
    extractValidSavedQueries,
    useGetOne,
    useListContext,
    useSavedQueries,
} from "react-admin";
import { useNavigate } from "react-router-dom";

export type SecondaryFilter = {
    column: string;
    input: ReactElement<any>;
    // needed when the input has no source or label prop
    source?: string;
    label?: string;
    // shows the name instead of the id in the chip
    reference?: string;
};

const isEmpty = (value: unknown) =>
    value === undefined || value === null || value === "" || (Array.isArray(value) && value.length === 0);

const ReferenceName = ({ reference, id }: { reference: string; id: Identifier }) => {
    const { data } = useGetOne(reference, { id });
    return data?.name ?? id;
};

const ChipValue = ({ filter, value }: { filter: SecondaryFilter; value: unknown }) => {
    if (filter.reference) {
        return <ReferenceName reference={filter.reference} id={value as Identifier} />;
    }
    if (typeof value === "boolean") {
        return value ? "Yes" : "No";
    }
    return Array.isArray(value) ? value.join(", ") : String(value);
};

interface FilterBarProps {
    filters: ReactElement[];
    moreFilters: SecondaryFilter[];
    saveQuery?: boolean;
}

// One wrapping row: the primary filters, MORE FILTERS and a chip for each active secondary filter.
export const FilterBar = ({ filters, moreFilters, saveQuery = false }: FilterBarProps) => {
    const { filterValues, displayedFilters, setFilters, sort, perPage, resource } = useListContext();
    const navigate = useNavigate();
    const [anchorEl, setAnchorEl] = useState<HTMLElement | null>(null);
    const [dialog, setDialog] = useState<"add" | "remove" | null>(null);
    const [savedQueries] = useSavedQueries(resource);

    const values = new Map(Object.entries(filterValues));
    const sourceOf = (filter: SecondaryFilter): string => filter.source ?? filter.input.props.source;
    const active = moreFilters.filter((filter) => !isEmpty(values.get(sourceOf(filter))));
    const columns = [...new Set(moreFilters.map((filter) => filter.column))];

    const validSavedQueries = saveQuery ? extractValidSavedQueries(savedQueries) : [];
    const currentQuery = JSON.stringify({ filter: filterValues, sort, perPage, displayedFilters });
    const currentIsSaved = validSavedQueries.some((query) => JSON.stringify(query.value) === currentQuery);

    return (
        <Box
            sx={{
                display: "flex",
                flexWrap: "wrap",
                alignItems: "flex-end",
                width: "100%",
                paddingBottom: 0.5,
                "& > form": { display: "contents" },
                // compact primary inputs, so that the usual set fits into one row at 1440px
                "& .filter-field .RaFilterFormInput-spacer": { width: 8 },
                "& .filter-field > .ra-input.MuiTextField-root": { width: "9em" },
                "& .filter-field .MuiAutocomplete-root": { width: "auto", minWidth: "10em" },
            }}
        >
            <FilterForm filters={filters} />
            <Button
                size="small"
                onClick={(event) => setAnchorEl(event.currentTarget)}
                startIcon={
                    <Badge badgeContent={active.length} color="primary">
                        <FilterListIcon />
                    </Badge>
                }
                sx={{ marginBottom: 1 }}
            >
                More filters
            </Button>
            {active.map((filter) => (
                <Chip
                    key={sourceOf(filter)}
                    size="small"
                    label={
                        <>
                            {filter.label ?? filter.input.props.label}:{" "}
                            <ChipValue filter={filter} value={values.get(sourceOf(filter))} />
                        </>
                    }
                    onDelete={() => setFilters({ ...filterValues, [sourceOf(filter)]: undefined }, displayedFilters)}
                    sx={{ marginBottom: 1.75, marginLeft: 1 }}
                />
            ))}
            <Popover
                open={Boolean(anchorEl)}
                anchorEl={anchorEl}
                onClose={() => setAnchorEl(null)}
                anchorOrigin={{ vertical: "bottom", horizontal: "left" }}
                // the form must stay mounted, otherwise a debounced change is lost when the popover closes
                keepMounted
            >
                <Box sx={{ padding: 2, "& .MuiFormHelperText-root": { display: "none" } }}>
                    <FilterLiveForm>
                        <Stack direction="row" spacing={3}>
                            {columns.map((column) => (
                                <Stack key={column} sx={{ width: "15em", "& .MuiFormControl-root": { width: "100%" } }}>
                                    <Typography variant="overline" color="textSecondary">
                                        {column}
                                    </Typography>
                                    {moreFilters
                                        .filter((filter) => filter.column === column)
                                        .map((filter) => (
                                            <Box key={sourceOf(filter)}>{filter.input}</Box>
                                        ))}
                                </Stack>
                            ))}
                        </Stack>
                    </FilterLiveForm>
                    {validSavedQueries.length > 0 && (
                        <>
                            <Divider sx={{ marginTop: 2, marginBottom: 1 }} />
                            <Typography variant="overline" color="textSecondary">
                                Saved queries
                            </Typography>
                            <Stack direction="row" spacing={1} useFlexGap sx={{ flexWrap: "wrap" }}>
                                {validSavedQueries.map((query, index) => (
                                    <Chip
                                        key={index}
                                        label={query.label}
                                        size="small"
                                        variant={JSON.stringify(query.value) === currentQuery ? "filled" : "outlined"}
                                        color={JSON.stringify(query.value) === currentQuery ? "primary" : "default"}
                                        onClick={() => {
                                            navigate({
                                                search: queryString.stringify({
                                                    filter: JSON.stringify(query.value.filter),
                                                    sort: query.value.sort?.field,
                                                    order: query.value.sort?.order,
                                                    page: 1,
                                                    perPage: query.value.perPage,
                                                    displayedFilters: JSON.stringify(query.value.displayedFilters),
                                                }),
                                            });
                                            setAnchorEl(null);
                                        }}
                                    />
                                ))}
                            </Stack>
                        </>
                    )}
                    <Divider sx={{ marginTop: 2, marginBottom: 1 }} />
                    <Stack direction="row" sx={{ justifyContent: "space-between" }}>
                        {saveQuery ? (
                            <Button
                                disabled={Object.keys(filterValues).length === 0}
                                onClick={() => {
                                    setDialog(currentIsSaved ? "remove" : "add");
                                    setAnchorEl(null);
                                }}
                            >
                                {currentIsSaved ? "Remove saved query…" : "Save current query…"}
                            </Button>
                        ) : (
                            <span />
                        )}
                        <Button
                            disabled={Object.keys(filterValues).length === 0}
                            onClick={() => {
                                setFilters({}, {});
                                setAnchorEl(null);
                            }}
                        >
                            Remove all filters
                        </Button>
                    </Stack>
                </Box>
            </Popover>
            {saveQuery && (
                <>
                    <AddSavedQueryDialog open={dialog === "add"} onClose={() => setDialog(null)} />
                    <RemoveSavedQueryDialog open={dialog === "remove"} onClose={() => setDialog(null)} />
                </>
            )}
        </Box>
    );
};
