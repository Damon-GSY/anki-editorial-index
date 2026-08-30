const { chromium } = require("playwright");
const fs = require("node:fs");

const base = process.env.STANDALONE_PREVIEW_URL
  || "http://127.0.0.1:4418/design-exploration/standalone-preview/index.html";

let assertions = 0;

function check(condition, message) {
  assertions += 1;
  if (!condition) throw new Error(message);
}

function channels(color) {
  const values = color.match(/[\d.]+/g)?.map(Number) || [];
  return values.slice(0, 3);
}

function luminance(color) {
  const values = channels(color).map(value => {
    const normalized = value / 255;
    return normalized <= 0.04045
      ? normalized / 12.92
      : ((normalized + 0.055) / 1.055) ** 2.4;
  });
  return 0.2126 * values[0] + 0.7152 * values[1] + 0.0722 * values[2];
}

function contrast(foreground, background) {
  const first = luminance(foreground);
  const second = luminance(background);
  return (Math.max(first, second) + 0.05) / (Math.min(first, second) + 0.05);
}

function px(value) {
  return Number.parseFloat(value) || 0;
}

async function computed(locator, properties) {
  return locator.evaluate((node, names) => {
    const style = getComputedStyle(node);
    return Object.fromEntries(names.map(name => [name, style[name]]));
  }, properties);
}

async function keyboardFocus(page, locator, label) {
  await locator.focus();
  await page.keyboard.press("Tab");
  await page.keyboard.press("Shift+Tab");
  check(await locator.evaluate(node => node === document.activeElement), `${label}: keyboard focus was not restored`);
  check(await locator.evaluate(node => node.matches(":focus-visible")), `${label}: :focus-visible did not match`);
}

(async () => {
  const launchOptions = { headless: true };
  const localChrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
  if (process.env.PLAYWRIGHT_CHROME) {
    launchOptions.executablePath = process.env.PLAYWRIGHT_CHROME;
  } else if (process.platform === "darwin" && fs.existsSync(localChrome)) {
    launchOptions.executablePath = localChrome;
  }

  const browser = await chromium.launch(launchOptions);
  const errors = [];
  const widths = [768, 520, 360];
  const contexts = ["stats", "deck-options"];
  const themes = ["light", "dark"];

  try {
    for (const width of widths) {
      for (const theme of themes) {
        for (const context of contexts) {
          const page = await browser.newPage({ viewport: { width, height: 900 } });
          const label = `${context}/${theme}/${width}`;
          page.on("console", message => {
            if (message.type() === "error") errors.push(`${label}: ${message.text()}`);
          });
          page.on("pageerror", error => errors.push(`${label}: ${error.message}`));

          await page.goto(`${base}?context=${context}&theme=${theme}`);
          await page.waitForLoadState("networkidle");
          await page.evaluate(() => document.fonts.ready);

          check(await page.locator("html").getAttribute("data-mistline-context") === context, `${label}: context marker mismatch`);
          check((await page.locator("html").evaluate(node => node.classList.contains("night-mode"))) === (theme === "dark"), `${label}: night-mode mismatch`);
          check(await page.evaluate(() => document.fonts.check('400 16px "Mist Inter"')), `${label}: Mist Inter did not load`);
          check(await page.evaluate(() => document.fonts.check('600 30px "Mist Source Serif"')), `${label}: Mist Source Serif did not load`);

          const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
          check(overflow <= 0, `${label}: horizontal overflow ${overflow}px`);

          const bodyStyle = await computed(page.locator("body"), ["backgroundColor", "color", "fontFamily"]);
          check(bodyStyle.fontFamily.includes("Mist Inter"), `${label}: body font mismatch ${bodyStyle.fontFamily}`);
          check(contrast(bodyStyle.color, bodyStyle.backgroundColor) >= 4.5, `${label}: body contrast below 4.5 (${bodyStyle.color} on ${bodyStyle.backgroundColor})`);

          if (context === "stats") {
            const range = page.locator(".range-box");
            const rangeStyle = await computed(range, ["borderRadius", "boxShadow", "rowGap", "columnGap", "paddingLeft"]);
            check(px(rangeStyle.borderRadius) >= 12, `${label}: range shelf radius ${rangeStyle.borderRadius}`);
            check(rangeStyle.boxShadow !== "none", `${label}: range shelf shadow missing`);
            check(px(rangeStyle.rowGap) >= 8 && px(rangeStyle.columnGap) >= 16, `${label}: range shelf gap mismatch ${rangeStyle.rowGap}/${rangeStyle.columnGap}`);
            check(px(rangeStyle.paddingLeft) >= 8, `${label}: range shelf padding too small ${rangeStyle.paddingLeft}`);

            const search = page.locator("#statisticsSearchText");
            const searchStyle = await computed(search, ["borderRadius", "minHeight", "fontFamily"]);
            check(px(searchStyle.borderRadius) >= 9, `${label}: search radius ${searchStyle.borderRadius}`);
            check(px(searchStyle.minHeight) >= 34, `${label}: search min-height ${searchStyle.minHeight}`);
            check(searchStyle.fontFamily.includes("Mist Inter"), `${label}: search font mismatch ${searchStyle.fontFamily}`);
            await search.fill("tag:marked");
            check(await search.inputValue() === "tag:marked", `${label}: search input did not accept text`);
            await search.focus();
            const focusedSearch = await computed(search, ["outlineStyle", "outlineWidth", "borderColor"]);
            check(focusedSearch.outlineStyle !== "none" && px(focusedSearch.outlineWidth) >= 2, `${label}: search focus ring missing`);

            const radios = page.locator('input[type="radio"]');
            const radioStyle = await computed(radios.first(), ["width", "height", "borderRadius"]);
            check(px(radioStyle.width) === 18 && px(radioStyle.height) === 18, `${label}: radio size mismatch ${radioStyle.width}/${radioStyle.height}`);
            check(px(radioStyle.borderRadius) >= 9, `${label}: radio is not circular ${radioStyle.borderRadius}`);
            await radios.nth(1).check();
            check(await radios.nth(1).isChecked(), `${label}: radio interaction failed`);

            const checkbox = page.locator("#include-suspended");
            const checkboxStyle = await computed(checkbox, ["width", "height", "borderRadius"]);
            check(px(checkboxStyle.width) === 18 && px(checkboxStyle.height) === 18, `${label}: checkbox size mismatch`);
            check(px(checkboxStyle.borderRadius) >= 5, `${label}: checkbox radius ${checkboxStyle.borderRadius}`);
            await keyboardFocus(page, checkbox, `${label} checkbox`);
            const checkboxFocus = await computed(checkbox, ["outlineStyle", "outlineWidth"]);
            check(checkboxFocus.outlineStyle !== "none" && px(checkboxFocus.outlineWidth) >= 2, `${label}: checkbox focus ring missing`);

            const cards = page.locator(".graphs-container > .container.light");
            check(await cards.count() === 2, `${label}: stats cards missing`);
            const cardStyle = await computed(cards.first(), ["borderRadius", "boxShadow", "paddingTop", "paddingLeft"]);
            check(px(cardStyle.borderRadius) >= 12, `${label}: stats card radius ${cardStyle.borderRadius}`);
            check(cardStyle.boxShadow !== "none", `${label}: stats card shadow missing`);
            check(px(cardStyle.paddingTop) >= 18 && px(cardStyle.paddingLeft) >= (width <= 520 ? 14 : 20), `${label}: stats card padding mismatch ${cardStyle.paddingTop}/${cardStyle.paddingLeft}`);

            const headingStyle = await computed(cards.first().locator("h1"), ["fontFamily", "fontSize", "paddingBottom", "marginBottom"]);
            check(headingStyle.fontFamily.includes("Mist Source Serif"), `${label}: stats heading font mismatch ${headingStyle.fontFamily}`);
            check(px(headingStyle.fontSize) >= 26, `${label}: stats heading too small ${headingStyle.fontSize}`);
            check(px(headingStyle.paddingBottom) >= 12 && px(headingStyle.marginBottom) >= 12, `${label}: stats heading rhythm mismatch`);

            const secondary = page.locator("#stats-secondary");
            const secondaryStyle = await computed(secondary, ["borderRadius", "boxShadow"]);
            check(px(secondaryStyle.borderRadius) >= 8, `${label}: stats secondary radius ${secondaryStyle.borderRadius}`);
            check(secondaryStyle.boxShadow !== "none", `${label}: stats secondary shadow missing`);
            await keyboardFocus(page, secondary, `${label} stats secondary`);
            const secondaryFocus = await computed(secondary, ["outlineStyle", "outlineWidth"]);
            check(secondaryFocus.outlineStyle !== "none" && px(secondaryFocus.outlineWidth) >= 2, `${label}: stats secondary focus missing`);
            await secondary.click();
            check(await page.locator("body").getAttribute("data-secondary") === "true", `${label}: stats secondary action failed`);

            const disabled = page.locator("#stats-disabled");
            check(await disabled.isDisabled(), `${label}: disabled stats action is enabled`);
            const disabledStyle = await computed(disabled, ["opacity", "boxShadow", "cursor"]);
            check(px(disabledStyle.opacity) >= 0.6 && px(disabledStyle.opacity) <= 0.75, `${label}: disabled stats action attenuation mismatch ${disabledStyle.opacity}`);
            check(disabledStyle.boxShadow === "none" && disabledStyle.cursor === "not-allowed", `${label}: disabled stats action still looks interactive`);
            const searchLink = await computed(page.locator("button.search-link"), ["boxShadow", "borderRadius"]);
            check(searchLink.boxShadow === "none" && px(searchLink.borderRadius) >= 4, `${label}: inline search action treatment mismatch`);
            const chartFilter = await page.locator(".graph svg .bars rect").first().evaluate(node => getComputedStyle(node).filter);
            check(chartFilter !== "none", `${label}: graph color harmonization missing`);
          }

          if (context === "deck-options") {
            const stickyStyle = await computed(page.locator(".sticky-container"), ["paddingLeft", "paddingTop", "borderBottomWidth"]);
            check(px(stickyStyle.paddingLeft) >= 8 && px(stickyStyle.paddingTop) >= 10, `${label}: sticky shelf padding mismatch ${stickyStyle.paddingLeft}/${stickyStyle.paddingTop}`);
            check(px(stickyStyle.borderBottomWidth) >= 1, `${label}: sticky shelf divider missing`);

            const columnsStyle = await computed(page.locator(".container-columns"), ["rowGap", "columnGap", "paddingLeft", "paddingBottom"]);
            check(px(columnsStyle.rowGap) >= 16 && px(columnsStyle.columnGap) >= 16, `${label}: card grid gap mismatch ${columnsStyle.rowGap}/${columnsStyle.columnGap}`);
            check(px(columnsStyle.paddingLeft) >= 8 && px(columnsStyle.paddingBottom) >= 24, `${label}: card grid outer padding mismatch`);

            const cards = page.locator(".container-columns .container.light");
            check(await cards.count() === 2, `${label}: deck option cards missing`);
            const cardStyle = await computed(cards.first(), ["borderRadius", "boxShadow", "paddingTop", "paddingLeft"]);
            check(px(cardStyle.borderRadius) >= 12, `${label}: deck option card radius ${cardStyle.borderRadius}`);
            check(cardStyle.boxShadow !== "none", `${label}: deck option card shadow missing`);
            check(px(cardStyle.paddingTop) >= 16 && px(cardStyle.paddingLeft) >= 14, `${label}: deck option card padding mismatch ${cardStyle.paddingTop}/${cardStyle.paddingLeft}`);

            const headingStyle = await computed(cards.first().locator("h1"), ["fontFamily", "fontSize", "paddingBottom", "marginBottom"]);
            check(headingStyle.fontFamily.includes("Mist Source Serif"), `${label}: deck option heading font mismatch ${headingStyle.fontFamily}`);
            check(px(headingStyle.fontSize) >= 26, `${label}: deck option heading too small ${headingStyle.fontSize}`);
            check(px(headingStyle.paddingBottom) >= 12 && px(headingStyle.marginBottom) >= 12, `${label}: deck option heading rhythm mismatch`);

            const spin = page.locator('[data-spinbox="new-limit"]');
            const spinStyle = await computed(spin, ["minHeight", "borderRadius", "boxShadow"]);
            check(px(spinStyle.minHeight) >= 36, `${label}: spin box min-height ${spinStyle.minHeight}`);
            check(px(spinStyle.borderRadius) >= 9, `${label}: spin box radius ${spinStyle.borderRadius}`);
            check(spinStyle.boxShadow !== "none", `${label}: spin box inset shadow missing`);
            const spinInput = spin.locator("input");
            await spinInput.focus();
            const focusedSpin = await computed(spin, ["borderColor", "boxShadow"]);
            check(focusedSpin.boxShadow !== spinStyle.boxShadow, `${label}: spin box focus-within feedback missing`);
            const previousValue = Number(await spinInput.inputValue());
            await spin.locator(".spinner.increment").click();
            check(Number(await spinInput.inputValue()) === previousValue + 1, `${label}: spin box increment failed`);

            const switchInput = page.locator("#limit-switch");
            const switchStyle = await computed(switchInput, ["width", "height", "borderRadius", "backgroundColor"]);
            check(px(switchStyle.width) === 40 && px(switchStyle.height) === 24, `${label}: switch size mismatch ${switchStyle.width}/${switchStyle.height}`);
            check(px(switchStyle.borderRadius) >= 12, `${label}: switch radius ${switchStyle.borderRadius}`);
            await keyboardFocus(page, switchInput, `${label} switch`);
            const switchFocus = await computed(switchInput, ["outlineStyle", "outlineWidth"]);
            check(switchFocus.outlineStyle !== "none" && px(switchFocus.outlineWidth) >= 2, `${label}: switch focus ring missing`);
            await switchInput.click();
            check(!(await switchInput.isChecked()), `${label}: switch interaction failed`);
            await page.waitForTimeout(220);
            const switchedBackground = (await computed(switchInput, ["backgroundColor"])).backgroundColor;
            check(switchedBackground !== switchStyle.backgroundColor, `${label}: switch state has no visual change`);

            const select = page.locator("#preset-select");
            const selectStyle = await computed(select, ["minHeight", "borderRadius", "boxShadow"]);
            check(px(selectStyle.minHeight) >= 38, `${label}: select min-height ${selectStyle.minHeight}`);
            check(px(selectStyle.borderRadius) >= 9, `${label}: select radius ${selectStyle.borderRadius}`);
            check(selectStyle.boxShadow !== "none", `${label}: select inset shadow missing`);
            await keyboardFocus(page, select, `${label} select`);
            const selectFocus = await computed(select, ["outlineStyle", "outlineWidth"]);
            check(selectFocus.outlineStyle !== "none" && px(selectFocus.outlineWidth) >= 2, `${label}: select focus ring missing`);
            await select.click();
            check(await select.getAttribute("aria-expanded") === "true", `${label}: select expansion failed`);

            const save = page.locator("#deck-save");
            const saveStyle = await computed(save, ["minHeight", "borderTopLeftRadius", "borderTopRightRadius", "boxShadow", "backgroundColor"]);
            check(px(saveStyle.minHeight) >= 38, `${label}: Save min-height ${saveStyle.minHeight}`);
            check(px(saveStyle.borderTopLeftRadius) >= 9 && px(saveStyle.borderTopRightRadius) === 0, `${label}: Save split-button radius mismatch`);
            check(saveStyle.boxShadow !== "none", `${label}: Save shadow missing`);
            check(saveStyle.backgroundColor !== bodyStyle.backgroundColor, `${label}: Save lacks primary fill`);
            await keyboardFocus(page, save, `${label} Save`);
            const saveFocus = await computed(save, ["outlineStyle", "outlineWidth"]);
            check(saveFocus.outlineStyle !== "none" && px(saveFocus.outlineWidth) >= 2, `${label}: Save focus ring missing`);
            await save.click();
            check(await page.locator("body").getAttribute("data-saved") === "true", `${label}: Save action failed`);

            const secondary = page.locator("#deck-secondary");
            const secondaryStyle = await computed(secondary, ["borderRadius", "boxShadow"]);
            check(px(secondaryStyle.borderRadius) >= 8, `${label}: secondary button radius ${secondaryStyle.borderRadius}`);
            check(secondaryStyle.boxShadow !== "none", `${label}: secondary button shadow missing`);
            await secondary.click();
            check(await page.locator("body").getAttribute("data-secondary") === "true", `${label}: secondary action failed`);

            const disabledInput = page.locator("#inherited-limit");
            check(await disabledInput.isDisabled(), `${label}: inherited limit is not disabled`);
            const disabledInputStyle = await computed(disabledInput, ["opacity", "cursor"]);
            check(px(disabledInputStyle.opacity) >= 0.65 && px(disabledInputStyle.opacity) <= 0.8, `${label}: disabled input attenuation mismatch ${disabledInputStyle.opacity}`);
            check(disabledInputStyle.cursor === "not-allowed", `${label}: disabled input still looks interactive`);

            const columnCount = await page.locator(".container-columns").evaluate(node => getComputedStyle(node).gridTemplateColumns.split(" ").length);
            check(columnCount === (width <= 620 ? 1 : 2), `${label}: responsive card columns ${columnCount}`);
          }

          const finalOverflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
          check(finalOverflow <= 0, `${label}: interaction introduced horizontal overflow ${finalOverflow}px`);
          await page.close();
        }
      }
    }

    check(errors.length === 0, `browser errors:\n${errors.join("\n")}`);
    console.log(`PASS ${assertions}/${assertions} standalone Stats + Deck Options assertions`);
  } finally {
    await browser.close();
  }
})().catch(error => {
  console.error(`FAIL after ${assertions} assertions: ${error.stack || error}`);
  process.exit(1);
});
