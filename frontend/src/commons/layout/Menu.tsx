import ChecklistIcon from "@mui/icons-material/Checklist";
import SecurityIcon from "@mui/icons-material/Security";
import SettingsIcon from "@mui/icons-material/Settings";
import { Badge, Box } from "@mui/material";
import { useEffect, useState } from "react";
import { DashboardMenuItem, MenuItemLink, MenuProps, useSidebarState } from "react-admin";

import administration from "../../access_control/access_control_administration";
import periodic_tasks from "../../background_tasks/periodic_tasks";
import components from "../../core/components";
import observations from "../../core/observations";
import product_groups from "../../core/product_groups";
import products from "../../core/products";
import parsers from "../../import_observations/parsers";
import licenses from "../../licenses/licenses";
import notifications from "../../notifications";
import { get_notification_count, update_notification_count } from "../../notifications/notification_count";
import general_rules from "../../rules/general_rules";
import csaf from "../../vex/csaf";
import cyclonedx from "../../vex/cyclonedx";
import openvex from "../../vex/openvex";
import vex_counters from "../../vex/vex_counters";
import vex_documents from "../../vex/vex_documents";
import { IntervalHooks } from "../IntervalHooks";
import { feature_license_management, feature_vex_enabled, is_superuser } from "../functions";
import settings from "../settings";
import SubMenu from "./SubMenu";

type MenuName = "menuSettings" | "menuVEX";

const Menu = ({ dense = false }: MenuProps) => {
    const [open] = useSidebarState();
    const [state, setState] = useState({ menuSettings: false, menuVEX: false });
    const handleToggle = (menu: MenuName) => {
        setState((state) => ({ ...state, [menu]: !state[menu] })); // eslint-disable-line security/detect-object-injection
    };

    IntervalHooks.useDispatch(
        () => {
            update_notification_count();
        },
        5 * 60 * 1000
    );

    useEffect(() => {
        update_notification_count();
    }, []);

    return (
        <Box
            sx={{
                width: open ? 220 : 50,
                marginTop: 1,
                marginBottom: 1,
                transition: (theme) =>
                    theme.transitions.create("width", {
                        easing: theme.transitions.easing.sharp,
                        duration: theme.transitions.duration.leavingScreen,
                    }),
            }}
        >
            <DashboardMenuItem />
            <MenuItemLink
                to="/product_groups"
                state={{ _scrollToTop: true }}
                primaryText="Product Groups"
                leftIcon={<product_groups.icon />}
                dense={dense}
            />
            <MenuItemLink
                to="/products"
                state={{ _scrollToTop: true }}
                primaryText="Products"
                leftIcon={<products.icon />}
                dense={dense}
            />
            <MenuItemLink
                to="/observations"
                state={{ _scrollToTop: true }}
                primaryText="Observations"
                leftIcon={<observations.icon />}
                dense={dense}
            />
            <MenuItemLink
                to="/components"
                state={{ _scrollToTop: true }}
                primaryText="Components"
                leftIcon={<components.icon />}
                dense={dense}
            />
            <MenuItemLink
                to="/reviews"
                state={{ _scrollToTop: true }}
                primaryText="Reviews"
                leftIcon={<ChecklistIcon />}
                dense={dense}
            />
            <MenuItemLink
                to="/notifications"
                state={{ _scrollToTop: true }}
                leftIcon={<notifications.icon />}
                dense={dense}
            >
                Notifications
                {get_notification_count() && get_notification_count() != "0" && (
                    <Badge badgeContent={get_notification_count()} color="secondary" sx={{ marginLeft: 3 }} />
                )}
            </MenuItemLink>
            {feature_vex_enabled() && (
                <SubMenu
                    handleToggle={() => handleToggle("menuVEX")}
                    isOpen={state.menuVEX}
                    name="VEX"
                    icon={<SecurityIcon />}
                    dense={dense}
                >
                    <MenuItemLink
                        to="/vex/csaf"
                        state={{ _scrollToTop: true }}
                        primaryText="CSAF"
                        leftIcon={<csaf.icon />}
                        dense={dense}
                    />
                    <MenuItemLink
                        to="/vex/cyclonedx"
                        state={{ _scrollToTop: true }}
                        primaryText="CycloneDX"
                        leftIcon={<cyclonedx.icon />}
                        dense={dense}
                    />
                    <MenuItemLink
                        to="/vex/openvex"
                        state={{ _scrollToTop: true }}
                        primaryText="OpenVEX"
                        leftIcon={<openvex.icon />}
                        dense={dense}
                    />
                    {is_superuser() && (
                        <MenuItemLink
                            to="/vex/vex_documents"
                            state={{ _scrollToTop: true }}
                            primaryText="VEX documents"
                            leftIcon={<vex_documents.icon />}
                            dense={dense}
                        />
                    )}
                </SubMenu>
            )}
            <SubMenu
                handleToggle={() => handleToggle("menuSettings")}
                isOpen={state.menuSettings}
                name="Administration"
                icon={<SettingsIcon />}
                dense={dense}
            >
                {feature_license_management() && (
                    <MenuItemLink
                        to="/license/licenses"
                        state={{ _scrollToTop: true }}
                        primaryText="Licenses"
                        leftIcon={<licenses.icon />}
                        dense={dense}
                    />
                )}
                <MenuItemLink
                    to="/access_control/users"
                    state={{ _scrollToTop: true }}
                    primaryText="Access Control"
                    leftIcon={<administration.icon />}
                    dense={dense}
                />
                {is_superuser() && (
                    <MenuItemLink
                        to="/settings/1/show"
                        state={{ _scrollToTop: true }}
                        primaryText="Settings"
                        leftIcon={<settings.icon />}
                        dense={dense}
                    />
                )}
                {is_superuser() && (
                    <MenuItemLink
                        to="/periodic_tasks"
                        state={{ _scrollToTop: true }}
                        primaryText="Periodic Tasks"
                        leftIcon={<periodic_tasks.icon />}
                        dense={dense}
                    />
                )}
                <MenuItemLink
                    to="/parsers"
                    state={{ _scrollToTop: true }}
                    primaryText="Parsers"
                    leftIcon={<parsers.icon />}
                    dense={dense}
                />
                <MenuItemLink
                    to="/general_rules"
                    state={{ _scrollToTop: true }}
                    primaryText="General Rules"
                    leftIcon={<general_rules.icon />}
                    dense={dense}
                />
                {feature_vex_enabled() && (
                    <MenuItemLink
                        to="/vex/vex_counters"
                        state={{ _scrollToTop: true }}
                        primaryText="VEX Counters"
                        leftIcon={<vex_counters.icon />}
                        dense={dense}
                    />
                )}
            </SubMenu>
        </Box>
    );
};

export default Menu;
