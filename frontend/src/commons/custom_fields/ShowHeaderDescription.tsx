import ExpandLessIcon from "@mui/icons-material/ExpandLess";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import { Box, Button } from "@mui/material";
import { useEffect, useRef, useState } from "react";
import { Labeled } from "react-admin";

import MarkdownField from "./MarkdownField";

interface ShowHeaderDescriptionProps {
    description: string;
}

const ShowHeaderDescription = ({ description }: ShowHeaderDescriptionProps) => {
    const [expanded, setExpanded] = useState(false);
    const [overflowing, setOverflowing] = useState(false);
    const contentRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const element = contentRef.current;
        if (!element || expanded) {
            return undefined;
        }
        const checkOverflow = () => setOverflowing(element.scrollHeight > element.clientHeight);
        checkOverflow();
        const resizeObserver = new ResizeObserver(checkOverflow);
        resizeObserver.observe(element);
        return () => resizeObserver.disconnect();
    }, [description, expanded]);

    return (
        <Box sx={{ marginTop: 2 }}>
            <Labeled label="Description">
                <Box
                    ref={contentRef}
                    sx={
                        expanded
                            ? {}
                            : {
                                  display: "-webkit-box",
                                  WebkitLineClamp: 2,
                                  WebkitBoxOrient: "vertical",
                                  overflow: "hidden",
                              }
                    }
                >
                    <MarkdownField content={description} label="Description" />
                </Box>
            </Labeled>
            {(overflowing || expanded) && (
                <Box sx={{ marginTop: 1 }}>
                    <Button
                        size="small"
                        onClick={() => setExpanded(!expanded)}
                        startIcon={expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                        aria-expanded={expanded}
                        sx={{ minWidth: 0, padding: 0 }}
                    >
                        {expanded ? "Show less" : "Show more"}
                    </Button>
                </Box>
            )}
        </Box>
    );
};

export default ShowHeaderDescription;
