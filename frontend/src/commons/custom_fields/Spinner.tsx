import { Backdrop, CircularProgress } from "@mui/material";

interface SpinnerProps {
    open: boolean;
}

export const Spinner = ({ open }: SpinnerProps) =>
    open ? (
        <Backdrop sx={{ color: "#fff", zIndex: (theme) => theme.zIndex.drawer + 1 }} open={open}>
            <CircularProgress color="primary" />
        </Backdrop>
    ) : null;
