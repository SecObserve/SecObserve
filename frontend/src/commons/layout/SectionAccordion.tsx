import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import { Accordion, AccordionDetails, AccordionSummary, Stack, Typography } from "@mui/material";
import { PropsWithChildren, ReactElement } from "react";

import { getElevation } from "../../metrics/functions";

type SectionAccordionProps = PropsWithChildren<{
    /** The labels of the open sections of the screen, empty when all sections are closed. */
    expandedSections: string[];
    setExpandedSections: (labels: string[]) => void;
    label: string;
    icon: ReactElement;
}>;

/** Shared by all screens, because useStore re-subscribes when its default value is a new array. */
export const ALL_SECTIONS_CLOSED: string[] = [];

/**
 * One section of a screen as an accordion. Any number of sections can be open at the same time, so
 * opening one does not close the others. The screen owns the labels of its open sections and thus
 * decides how long they live: component state starts every visit with all sections closed, a store
 * keeps the open sections when the screen is left.
 *
 * The elevation depends on the theme, because the dark scheme tints the surface by elevation
 * instead of drawing a shadow, see the accordions of the reviews of a product.
 */
const SectionAccordion = ({ expandedSections, setExpandedSections, label, icon, children }: SectionAccordionProps) => {
    return (
        <Accordion
            expanded={expandedSections.includes(label)}
            onChange={(_event, isExpanded) =>
                setExpandedSections(
                    isExpanded ? [...expandedSections, label] : expandedSections.filter((section) => section !== label)
                )
            }
            elevation={getElevation()}
            sx={{ marginBottom: 2, padding: 0, width: "100%" }}
            disableGutters
        >
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
                    {icon}
                    <Typography variant="h6">{label}</Typography>
                </Stack>
            </AccordionSummary>
            <AccordionDetails>{children}</AccordionDetails>
        </Accordion>
    );
};

export default SectionAccordion;
