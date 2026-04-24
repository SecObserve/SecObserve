import { Page, expect, test } from "@playwright/test";

test.describe("SecObserve", async () => {
    test.describe.configure({ mode: "serial" });

    let page: Page;

    const delay = ms => new Promise(resolve => setTimeout(resolve, ms))

    test.beforeAll(async ({ browser }) => {
        page = await browser.newPage();
    });

    test("Login", async () => {

        if (process.env.SO_PW_DOCKER) {
            await delay(60000);
        }

        await page.goto(process.env.SO_PW_FRONTEND_BASE_URL);

        await expect(page).toHaveURL(process.env.SO_PW_FRONTEND_BASE_URL + "/#/login");

        await page.getByLabel("Username *").click();
        await page.getByLabel("Username *").fill(process.env.SO_PW_USERNAME);
        await page.getByLabel("Username *").press("Tab");
        await page.getByLabel("Password *").fill(process.env.SO_PW_PASSWORD);
        await page.getByRole("button", { name: "Sign in with user" }).click();

        await expect(page).toHaveURL(process.env.SO_PW_FRONTEND_BASE_URL + "/#/");

        await page.getByRole("menuitem", { name: "Product Groups" }).click();
        await expect(page).toHaveURL(process.env.SO_PW_FRONTEND_BASE_URL + "/#/product_groups");

        await page.getByRole("menuitem", { name: "Products" }).click();
        await expect(page).toHaveURL(process.env.SO_PW_FRONTEND_BASE_URL + "/#/products");

        await page.getByRole("menuitem", { name: "Observations" }).click();
        await expect(page).toHaveURL(process.env.SO_PW_FRONTEND_BASE_URL + "/#/observations");
    });
});
