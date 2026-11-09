import { CheckForApplicationUpdate, Layout, LayoutProps } from "react-admin";

import { useSettingsRefresh } from "../useSettingsRefresh";
import AppBar from "./AppBar";
import Menu from "./Menu";

const CustomLayout = ({ children }: LayoutProps) => {
    // Not in the Menu, because it is only mounted while the drawer is open on small screens
    useSettingsRefresh();

    return (
        <Layout appBar={AppBar} menu={Menu}>
            {children}
            <CheckForApplicationUpdate interval={5 * 60 * 1000} />
        </Layout>
    );
};

export default CustomLayout;
