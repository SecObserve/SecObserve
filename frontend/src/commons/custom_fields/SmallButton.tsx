import { Button } from "@mui/material";

interface SmallButtonProps {
    title: string;
    onClick: () => void;
    icon: any;
    disabled?: boolean;
}

const SmallButton = ({ title, onClick, icon, disabled }: SmallButtonProps) => {
    return (
        <Button
            onClick={onClick}
            size="small"
            sx={{ paddingTop: 0, paddingBottom: 0, paddingLeft: "5px", paddingRight: "5px" }}
            startIcon={icon}
            disabled={disabled}
        >
            {title}
        </Button>
    );
};

export default SmallButton;
