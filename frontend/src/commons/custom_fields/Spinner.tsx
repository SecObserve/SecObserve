import { Backdrop, CircularProgress, Portal } from "@mui/material";

interface SpinnerProps {
    open: boolean;
}

// The backdrop is rendered in a portal, so that it stays visible when the spinner is used inside a
// component that is hidden while the spinner is shown, e.g. a menu that is kept mounted while closed.
export const Spinner = ({ open }: SpinnerProps) =>
    open ? (
        <Portal>
            <Backdrop sx={{ color: "#fff", zIndex: (theme) => theme.zIndex.modal + 1 }} open={open}>
                <CircularProgress color="primary" />
            </Backdrop>
        </Portal>
    ) : null;
