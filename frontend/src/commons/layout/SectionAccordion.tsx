import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import { Accordion, AccordionDetails, AccordionSummary, Stack, Typography } from "@mui/material";
import { PropsWithChildren, ReactElement } from "react";

import { getElevation } from "../../metrics/functions";

type SectionAccordionProps = PropsWithChildren<{
    /** The label of the open section of the screen, empty when all sections are closed. */
    expandedSection: string;
    setExpandedSection: (label: string) => void;
    label: string;
    icon: ReactElement;
}>;

/**
 * One section of a screen as an accordion. At most one section is open at a time, because all
 * sections of a screen share the state of the open section. The screen owns that state and thus
 * decides how long it lives: component state starts every visit with all sections closed, a store
 * keeps the open section when the screen is left.
 *
 * The elevation depends on the theme, because the dark scheme tints the surface by elevation
 * instead of drawing a shadow, see the accordions of the reviews of a product.
 */
const SectionAccordion = ({ expandedSection, setExpandedSection, label, icon, children }: SectionAccordionProps) => {
    return (
        <Accordion
            expanded={expandedSection === label}
            onChange={(_event, isExpanded) => setExpandedSection(isExpanded ? label : "")}
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
