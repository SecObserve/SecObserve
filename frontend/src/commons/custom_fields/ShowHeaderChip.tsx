import { Box, Chip } from "@mui/material";
import { Fragment } from "react";
import { Link } from "react-router-dom";

interface ShowHeaderChipProps {
    label: string;
    value: string | number;
    color?: "default" | "warning";
    to?: string;
    state?: unknown;
}

const ShowHeaderChip = ({ label, value, color = "default", to, state }: ShowHeaderChipProps) => {
    const chip_label = (
        <Fragment>
            <Box component="span" sx={color === "default" ? { color: "text.secondary" } : { opacity: 0.75 }}>
                {label}
            </Box>
            <Box component="span" sx={{ fontWeight: 500, marginLeft: 0.75 }}>
                {value}
            </Box>
        </Fragment>
    );

    if (to) {
        return (
            <Chip
                label={chip_label}
                size="small"
                variant="outlined"
                color={color}
                clickable
                component={Link}
                to={to}
                state={state}
            />
        );
    }
    return <Chip label={chip_label} size="small" variant="outlined" color={color} />;
};

export default ShowHeaderChip;
