import { Stack } from "@mui/material";
import { ReactNode } from "react";

interface ToolbarProps {
    children?: ReactNode;
}

const Toolbar = (props: ToolbarProps) => {
    const { children } = props;

    return (
        <Stack direction="row" spacing={2} sx={{ justifyContent: "flex-end", alignItems: "center" }}>
            {children}
        </Stack>
    );
};

export default Toolbar;
