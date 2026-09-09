import ArrowDropDownIcon from "@mui/icons-material/ArrowDropDown";
import { ListItemIcon, Menu, MenuItem, Stack, Tab, Tabs, TabsProps } from "@mui/material";
import { Children, Fragment, MouseEvent, ReactElement, cloneElement, isValidElement, useState } from "react";
import { LinkBase, getShowLayoutTabFullPath, useParams, useSplatPathBase } from "react-admin";

interface TabsWithSubMenuProps extends TabsProps {
    subMenuLabel: string;
    subMenuIcon: ReactElement;
    subMenuPaths: string[];
    syncWithLocation?: boolean;
}

/**
 * Drop-in replacement for react-admin's TabbedShowLayoutTabs that moves the tabs with the given
 * paths out of the tab bar into a dropdown menu, so that long tab bars stay manageable.
 *
 * The tabs remain children of the TabbedShowLayout, so their routes are created as usual. They are
 * only omitted from the tab bar and rendered as menu items instead.
 */
const TabsWithSubMenu = ({
    children,
    syncWithLocation,
    value,
    subMenuLabel,
    subMenuIcon,
    subMenuPaths,
    ...rest
}: TabsWithSubMenuProps) => {
    const params = useParams();
    const splatPathBase = useSplatPathBase();
    const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
    const open = Boolean(anchorEl);
    const handleClick = (event: MouseEvent<HTMLElement>) => {
        setAnchorEl(event.currentTarget);
    };
    const handleClose = () => {
        setAnchorEl(null);
    };

    // params will include eventual parameters from the root pathname and * for the remaining part
    // which should match the tabs paths
    const currentPath = params["*"];

    // The path of a tab depends on its index in the complete list of tabs, so the paths have to be
    // calculated before the tabs are split into tab bar and sub menu.
    const tabs = Children.toArray(children)
        .filter((tab) => isValidElement(tab))
        .map((tab, index) => ({
            tab: tab as ReactElement<any>,
            index: index,
            path: getShowLayoutTabFullPath(tab, index),
        }));
    const barTabs = tabs.filter(({ path }) => !subMenuPaths.includes(path));
    const subMenuTabs = tabs.filter(({ path }) => subMenuPaths.includes(path));

    // The sub menu tab is selected as long as any of its tabs is shown, so that the tab bar always
    // has a selected value.
    const subMenuValue = subMenuPaths[0];
    const inSubMenu = currentPath !== undefined && subMenuPaths.includes(currentPath);
    const tabsValue = syncWithLocation ? (inSubMenu ? subMenuValue : currentPath) : value;

    // The sub menu tab shows the tab that is currently displayed, but the first tab of the sub menu
    // has the same label as the sub menu itself, so that it is not repeated.
    const activeSubMenuLabel = subMenuTabs.find(({ path }) => path === currentPath)?.tab.props.label;
    const showActiveSubMenuLabel = activeSubMenuLabel !== undefined && activeSubMenuLabel !== subMenuLabel;

    return (
        <Fragment>
            <Tabs indicatorColor="primary" value={tabsValue} {...rest}>
                {barTabs.map(({ tab, index, path }) =>
                    cloneElement(tab, {
                        key: path,
                        context: "header",
                        value: syncWithLocation ? path : index,
                        syncWithLocation,
                    })
                )}
                {subMenuTabs.length > 0 && (
                    <Tab
                        id="sub-menu-tab"
                        aria-controls={open ? "sub-menu" : undefined}
                        aria-haspopup="true"
                        aria-expanded={open ? "true" : undefined}
                        value={subMenuValue}
                        icon={subMenuIcon}
                        label={
                            <Stack direction="row" spacing={0.5} sx={{ alignItems: "center" }}>
                                <span>{subMenuLabel}</span>
                                {showActiveSubMenuLabel && (
                                    <Fragment>
                                        <span>/</span>
                                        <span>{activeSubMenuLabel}</span>
                                    </Fragment>
                                )}
                                <ArrowDropDownIcon fontSize="small" />
                            </Stack>
                        }
                        onClick={handleClick}
                    />
                )}
            </Tabs>
            <Menu
                id="sub-menu"
                anchorEl={anchorEl}
                open={open}
                onClose={handleClose}
                slotProps={{
                    list: {
                        "aria-labelledby": "sub-menu-tab",
                    },
                }}
            >
                {subMenuTabs.map(({ tab, path }) => (
                    <MenuItem
                        key={path}
                        component={LinkBase}
                        to={`${splatPathBase}/${path}`}
                        selected={path === currentPath}
                        onClick={handleClose}
                    >
                        <ListItemIcon>{tab.props.icon}</ListItemIcon>
                        {tab.props.label}
                    </MenuItem>
                ))}
            </Menu>
        </Fragment>
    );
};

export default TabsWithSubMenu;
