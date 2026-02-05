import { getResolvedSettingTheme } from "../user_settings/functions";

const Logo = () => {
    if (getResolvedSettingTheme() == "dark") {
        return <img src="secobserve_white.svg" alt="SecObserve logo" height={"20px"} />;
    } else {
        return <img src="secobserve.svg" alt="SecObserve logo" height={"20px"} />;
    }
};

export default Logo;
