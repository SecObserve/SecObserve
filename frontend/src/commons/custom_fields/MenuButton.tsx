import { Button } from "@mui/material";

import { getIconAndFontColor } from "../../commons/functions";

interface MenuButtonProps {
    title: string;
    onClick: () => void;
    icon: any;
    disabled?: boolean;
}

const MenuButton = ({ title, onClick, icon, disabled }: MenuButtonProps) => {
    return (
        <Button
            onClick={onClick}
            disabled={disabled}
            size="small"
            sx={{
                paddingTop: 0,
                paddingBottom: 0,
                paddingLeft: "5px",
                paddingRight: "5px",
                color: getIconAndFontColor(),
                textTransform: "none",
                fontWeight: "normal",
                fontSize: "1rem",
            }}
            startIcon={icon}
        >
            {title}
        </Button>
    );
};

export default MenuButton;
