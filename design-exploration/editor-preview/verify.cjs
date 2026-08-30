const { chromium } = require("playwright");
const fs = require("node:fs");
const path = require("node:path");

const base = process.env.EDITOR_PREVIEW_URL
  || "http://127.0.0.1:4418/design-exploration/editor-preview/index.html";
const captureDir = path.join(__dirname, "captures");
const reportPath = path.join(__dirname, "report.json");
const markdownPath = path.join(__dirname, "REPORT.md");
fs.mkdirSync(captureDir, { recursive: true });

const scenarios = [
  { name: "light-750-collapsed", width: 750, height: 493, theme: "light", tags: "collapsed", dupe: false },
  { name: "dark-750-expanded", width: 750, height: 493, theme: "dark", tags: "expanded", dupe: false },
  { name: "light-400-expanded", width: 400, height: 400, theme: "light", tags: "expanded", dupe: false },
  { name: "dark-400-duplicate", width: 400, height: 400, theme: "dark", tags: "collapsed", dupe: true },
];

function closeTo(actual, expected, tolerance = 0.6) {
  return Math.abs(actual - expected) <= tolerance;
}

function compactDetails(value) {
  if (typeof value === "string") return value;
  return JSON.stringify(value);
}

function markdownReport(report) {
  const rows = report.scenarios.map((scenario) => {
    const failed = scenario.checks.filter((check) => !check.ok);
    const result = failed.length ? `FAIL (${failed.length})` : "PASS";
    return `| ${scenario.name} | ${scenario.viewport.width}×${scenario.viewport.height} | ${scenario.theme} | ${scenario.tags} | ${result} |`;
  });
  const failures = report.scenarios.flatMap((scenario) => scenario.checks
    .filter((check) => !check.ok)
    .map((check) => `- **${scenario.name} · ${check.label}:** ${compactDetails(check.details)}`));

  return `# Editor regression report

Overall: **${report.ok ? "PASS" : "FAIL"}** · ${report.summary.passed}/${report.summary.total} checks passed.

| Scenario | Viewport | Theme | Tags | Result |
| --- | ---: | --- | --- | --- |
${rows.join("\n")}

## Assertions

- Anki-strength Svelte-scoped baseline rules are defeated by stable add-on selectors.
- The toolbar, fields, and tag rail remain inside 750×493 and 400×400 viewports.
- Every toolbar icon button remains exactly 32×32 CSS pixels, including compact layouts.
- Disabled toolbar controls remain legible without reducing whole-control opacity.
- The real nested Tags collapse badge remains a 32px target with a visible keyboard focus ring.
- Field cards keep the intended radius, 12px rhythm, and outer focus treatment.
- Bundled Editorial Inter loads locally for editor chrome.
- User-owned field typography remains Georgia/Menlo rather than inheriting editor chrome.
- Duplicate fields retain a visible danger treatment.

## Failures

${failures.length ? failures.join("\n") : "None."}
`;
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
  const report = { ok: true, summary: { passed: 0, total: 0 }, scenarios: [] };

  try {
    for (const scenario of scenarios) {
      const page = await browser.newPage({ viewport: { width: scenario.width, height: scenario.height } });
      const pageErrors = [];
      const result = {
        name: scenario.name,
        viewport: { width: scenario.width, height: scenario.height },
        theme: scenario.theme,
        tags: scenario.tags,
        duplicate: scenario.dupe,
        checks: [],
      };
      const check = (condition, label, details = "") => {
        const ok = Boolean(condition);
        result.checks.push({ label, ok, details });
        report.summary.total += 1;
        if (ok) report.summary.passed += 1;
      };

      page.on("console", (message) => {
        if (message.type() === "error") pageErrors.push(message.text());
      });
      page.on("pageerror", (error) => pageErrors.push(error.message));

      const url = new URL(base);
      url.searchParams.set("theme", scenario.theme);
      url.searchParams.set("tags", scenario.tags);
      if (scenario.dupe) url.searchParams.set("dupe", "1");

      try {
        await page.goto(url.href);
        await page.waitForLoadState("networkidle");
        await page.evaluate(() => document.fonts.ready);

        const beforeFocus = await page.evaluate(() => {
          const style = (selector) => getComputedStyle(document.querySelector(selector));
          const rect = (selector) => {
            const bounds = document.querySelector(selector).getBoundingClientRect();
            return { top: bounds.top, right: bounds.right, bottom: bounds.bottom, left: bounds.left, width: bounds.width, height: bounds.height };
          };
          const colorValue = (variable) => {
            const probe = document.createElement("span");
            probe.style.color = `var(${variable})`;
            document.body.append(probe);
            const value = getComputedStyle(probe).color;
            probe.remove();
            return value;
          };
          const contrastRatio = (foreground, background) => {
            const channels = (value) => value.match(/[\d.]+/g).slice(0, 3).map(Number);
            const luminance = (value) => {
              const linear = channels(value).map((channel) => {
                const normalized = channel / 255;
                return normalized <= 0.04045
                  ? normalized / 12.92
                  : ((normalized + 0.055) / 1.055) ** 2.4;
              });
              return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2];
            };
            const values = [luminance(foreground), luminance(background)].sort((a, b) => b - a);
            return (values[0] + 0.05) / (values[1] + 0.05);
          };
          const fields = style(".fields");
          const toolbar = style(".editor-toolbar");
          const shelf = style(".button-toolbar");
          const fieldCard = style("[data-field-card='front']");
          const fieldBody = style("[data-editor-field='front']");
          const richInput = getComputedStyle(document.querySelector("[data-field='front']").parentElement);
          const cards = [...document.querySelectorAll("[data-field-card]")].map((node) => {
            const bounds = node.getBoundingClientRect();
            return { top: bounds.top, bottom: bounds.bottom, left: bounds.left, right: bounds.right };
          });
          const shelfNode = document.querySelector(".button-toolbar");
          const iconButtons = [...document.querySelectorAll(".editor-toolbar .icon-button")].map((node) => {
            const bounds = node.getBoundingClientRect();
            const computed = getComputedStyle(node);
            return {
              label: node.getAttribute("aria-label"),
              disabled: node.disabled,
              left: bounds.left,
              right: bounds.right,
              width: bounds.width,
              height: bounds.height,
              opacity: parseFloat(computed.opacity),
              color: computed.color,
            };
          });
          const disabledButton = document.querySelector(".editor-toolbar .icon-button:disabled");
          const disabledStyle = getComputedStyle(disabledButton);
          const fieldBadges = [...document.querySelectorAll(".label-container .badge")].map((node) => {
            const bounds = node.getBoundingClientRect();
            return { width: bounds.width, height: bounds.height };
          });
          const tagButtons = [...document.querySelectorAll(".tag-editor button")].map((node) => {
            const bounds = node.getBoundingClientRect();
            return { width: bounds.width, height: bounds.height };
          });
          const tagCollapseButtons = [...document.querySelectorAll(
            '.note-editor > .collapse-label[role="button"] > .collapse-badge > button.badge',
          )].map((node) => {
            const bounds = node.getBoundingClientRect();
            return { width: bounds.width, height: bounds.height };
          });
          const shelfBackground = shelf.backgroundColor;
          const tagNode = document.querySelector("[data-tags='expanded'] .tag-editor, [data-tags='collapsed'] > .collapse-label");
          const tagStyle = getComputedStyle(tagNode);
          const tagRect = tagNode.getBoundingClientRect();
          const content = style("[data-field='front']");
          const code = style("[data-field='front'] code");
          const duplicateNode = document.querySelector(".editor-field.dupe")
            || document.querySelector("[data-editor-field='back']");
          const duplicateStyle = getComputedStyle(duplicateNode);

          return {
            document: {
              clientWidth: document.documentElement.clientWidth,
              scrollWidth: document.documentElement.scrollWidth,
              clientHeight: document.documentElement.clientHeight,
              scrollHeight: document.documentElement.scrollHeight,
            },
            theme: document.documentElement.dataset.theme,
            fonts: {
              regular: document.fonts.check('400 16px "Editorial Inter"'),
              semibold: document.fonts.check('600 16px "Editorial Inter"'),
              toolbar: toolbar.fontFamily,
              fieldLabel: style(".label-name").fontFamily,
              loadedResources: performance.getEntriesByType("resource")
                .map((entry) => entry.name)
                .filter((name) => name.includes("inter-") && name.endsWith(".woff2")),
            },
            toolbar: {
              rect: rect(".editor-toolbar"),
              paddingTop: parseFloat(toolbar.paddingTop),
              paddingLeft: parseFloat(toolbar.paddingLeft),
            },
            shelf: {
              rect: rect(".button-toolbar"),
              clientWidth: shelfNode.clientWidth,
              scrollWidth: shelfNode.scrollWidth,
              paddingTop: parseFloat(shelf.paddingTop),
              radius: parseFloat(shelf.borderRadius),
            },
            iconButtons,
            disabledButton: {
              count: document.querySelectorAll(".editor-toolbar .icon-button:disabled").length,
              opacity: parseFloat(disabledStyle.opacity),
              color: disabledStyle.color,
              shelfBackground,
              contrast: contrastRatio(disabledStyle.color, shelfBackground),
            },
            fieldBadges,
            tagButtons,
            tagCollapseButtons,
            fields: {
              gap: parseFloat(fields.rowGap),
              marginTop: parseFloat(fields.marginTop),
              paddingLeft: parseFloat(fields.paddingLeft),
              cards,
            },
            fieldCard: {
              radius: parseFloat(fieldCard.borderRadius),
              borderWidth: parseFloat(fieldCard.borderTopWidth),
              shadow: fieldCard.boxShadow,
            },
            fieldBody: {
              margin: parseFloat(fieldBody.marginTop),
              borderWidth: parseFloat(fieldBody.borderTopWidth),
              radius: parseFloat(fieldBody.borderRadius),
              outline: fieldBody.outline,
              shadow: fieldBody.boxShadow,
            },
            richInput: {
              paddingTop: parseFloat(richInput.paddingTop),
              paddingLeft: parseFloat(richInput.paddingLeft),
            },
            tags: {
              rect: { left: tagRect.left, right: tagRect.right, width: tagRect.width, height: tagRect.height },
              radius: parseFloat(tagStyle.borderRadius),
              marginLeft: parseFloat(tagStyle.marginLeft),
              fontFamily: tagStyle.fontFamily,
              collapsedVisible: getComputedStyle(document.querySelector(".collapse-label")).display !== "none",
              expandedVisible: getComputedStyle(document.querySelector(".tag-editor")).display !== "none",
            },
            content: {
              fontFamily: content.fontFamily,
              fontSize: content.fontSize,
              lineHeight: content.lineHeight,
              color: content.color,
              codeFamily: code.fontFamily,
              codeSize: code.fontSize,
            },
            duplicate: {
              active: duplicateNode.classList.contains("dupe"),
              outlineColor: duplicateStyle.outlineColor,
              outlineWidth: parseFloat(duplicateStyle.outlineWidth),
              shadow: duplicateStyle.boxShadow,
              danger: colorValue("--accent-danger"),
            },
            accent: colorValue("--editorial-accent"),
          };
        });

        const toolbarAction = page.locator('.editor-toolbar .icon-button[aria-label="Bold"]');
        const readToolbarAction = () => toolbarAction.evaluate((node) => {
          const style = getComputedStyle(node);
          return {
            color: style.color,
            background: style.backgroundColor,
            border: style.borderTopColor,
            shadow: style.boxShadow,
            outline: style.outlineStyle,
            outlineWidth: parseFloat(style.outlineWidth),
          };
        });
        const toolbarResting = await readToolbarAction();
        await toolbarAction.hover();
        await page.waitForTimeout(180);
        const toolbarHovered = await readToolbarAction();
        await page.mouse.down();
        await page.waitForTimeout(40);
        const toolbarPressed = await readToolbarAction();
        await page.mouse.up();
        await toolbarAction.focus();
        await page.keyboard.press("Tab");
        await page.keyboard.press("Shift+Tab");
        const toolbarFocused = await readToolbarAction();

        const fieldBadge = page.locator(".label-container .badge").first();
        await fieldBadge.focus();
        await page.keyboard.press("Tab");
        await page.keyboard.press("Shift+Tab");
        const fieldBadgeFocus = await fieldBadge.evaluate((node) => {
          const style = getComputedStyle(node);
          return { outline: style.outlineStyle, outlineWidth: parseFloat(style.outlineWidth) };
        });

        let tagCollapseButtonFocus = null;
        if (scenario.tags === "collapsed") {
          const tagCollapseButton = page.locator(
            '.note-editor > .collapse-label[role="button"] > .collapse-badge > button.badge',
          );
          await tagCollapseButton.focus();
          await page.keyboard.press("Tab");
          await page.keyboard.press("Shift+Tab");
          tagCollapseButtonFocus = await tagCollapseButton.evaluate((node) => {
            const style = getComputedStyle(node);
            return { outline: style.outlineStyle, outlineWidth: parseFloat(style.outlineWidth) };
          });
        }

        await page.locator("[data-field='front']").focus();
        const focused = await page.locator("[data-field-card='front']").evaluate((node) => {
          const style = getComputedStyle(node);
          const editorStyle = getComputedStyle(node.querySelector(".editor-field"));
          return {
            focusWithin: node.matches(":focus-within"),
            borderColor: style.borderTopColor,
            shadow: style.boxShadow,
            editorOutlineColor: editorStyle.outlineColor,
            editorOutlineWidth: parseFloat(editorStyle.outlineWidth),
            editorShadow: editorStyle.boxShadow,
          };
        });

        const compact = scenario.width <= 560;
        const expectedInline = compact ? 6 : 10;
        const visualGap = beforeFocus.fields.cards[1].top - beforeFocus.fields.cards[0].bottom;
        const toolbarContained = beforeFocus.shelf.rect.left >= -0.5
          && beforeFocus.shelf.rect.right <= scenario.width + 0.5;
        const iconsContained = beforeFocus.iconButtons.every((button) => (
          button.left >= beforeFocus.shelf.rect.left - 0.5
          && button.right <= beforeFocus.shelf.rect.right + 0.5
        ));
        const tagsContained = beforeFocus.tags.rect.left >= -0.5
          && beforeFocus.tags.rect.right <= scenario.width + 0.5;

        check(pageErrors.length === 0, "no browser errors", pageErrors);
        check(beforeFocus.theme === scenario.theme, "requested theme applied", beforeFocus.theme);
        check(beforeFocus.document.scrollWidth <= beforeFocus.document.clientWidth, "document has no horizontal overflow", beforeFocus.document);
        check(toolbarContained, "toolbar shelf stays inside viewport", beforeFocus.shelf.rect);
        check(beforeFocus.shelf.scrollWidth <= beforeFocus.shelf.clientWidth + 1, "toolbar content wraps without horizontal overflow", beforeFocus.shelf);
        check(beforeFocus.iconButtons.length >= 12, "production-like icon control set is present", beforeFocus.iconButtons.length);
        check(
          beforeFocus.iconButtons.every((button) => button.width === 32 && button.height === 32),
          "every toolbar icon button is exactly 32×32",
          beforeFocus.iconButtons,
        );
        check(iconsContained, "all toolbar icon buttons remain inside the wrapped shelf", beforeFocus.iconButtons);
        check(beforeFocus.disabledButton.count === 1, "disabled toolbar state is represented once", beforeFocus.disabledButton);
        check(beforeFocus.disabledButton.opacity === 1, "disabled toolbar control does not lose whole-control opacity", beforeFocus.disabledButton);
        check(beforeFocus.disabledButton.contrast >= 3, "disabled toolbar control remains visibly distinct", beforeFocus.disabledButton);
        check(
          beforeFocus.fieldBadges.length === 4
            && beforeFocus.fieldBadges.every((button) => button.width >= 32 && button.height >= 32),
          "field-header micro controls keep a 32px target",
          beforeFocus.fieldBadges,
        );
        check(
          scenario.tags === "collapsed" || (
            beforeFocus.tagButtons.length >= 3
            && beforeFocus.tagButtons.every((button) => button.width >= 32 && button.height >= 32)
          ),
          "tag controls keep a 32px target",
          beforeFocus.tagButtons,
        );
        check(
          scenario.tags === "expanded" || (
            beforeFocus.tagCollapseButtons.length === 1
            && beforeFocus.tagCollapseButtons[0].width >= 32
            && beforeFocus.tagCollapseButtons[0].height >= 32
          ),
          "collapsed Tags badge keeps a 32px target",
          beforeFocus.tagCollapseButtons,
        );
        check(
          fieldBadgeFocus.outline !== "none" && fieldBadgeFocus.outlineWidth >= 2,
          "field-header micro control keeps a keyboard focus indicator",
          fieldBadgeFocus,
        );
        check(
          scenario.tags === "expanded" || (
            tagCollapseButtonFocus.outline !== "none"
            && tagCollapseButtonFocus.outlineWidth >= 2
          ),
          "collapsed Tags badge keeps a keyboard focus indicator",
          tagCollapseButtonFocus,
        );
        check(
          toolbarHovered.background !== toolbarResting.background
            && toolbarHovered.border !== toolbarResting.border
            && toolbarHovered.color !== toolbarResting.color,
          "toolbar action has visible hover feedback",
          { resting: toolbarResting, hovered: toolbarHovered },
        );
        check(
          toolbarPressed.background !== toolbarHovered.background && toolbarPressed.shadow !== "none",
          "toolbar action has visible pressed feedback",
          { hovered: toolbarHovered, pressed: toolbarPressed },
        );
        check(
          toolbarFocused.outline !== "none" && toolbarFocused.outlineWidth >= 2,
          "toolbar action keeps a keyboard focus indicator",
          toolbarFocused,
        );

        check(beforeFocus.fonts.regular && beforeFocus.fonts.semibold, "local Editorial Inter faces loaded", beforeFocus.fonts);
        check(beforeFocus.fonts.loadedResources.length >= 2, "both local Inter resources requested", beforeFocus.fonts.loadedResources);
        check(beforeFocus.fonts.toolbar.includes("Editorial Inter"), "toolbar uses Editorial Inter", beforeFocus.fonts.toolbar);
        check(beforeFocus.fonts.fieldLabel.includes("Editorial Inter"), "field label uses Editorial Inter", beforeFocus.fonts.fieldLabel);

        check(closeTo(beforeFocus.toolbar.paddingTop, 8), "stable editor selector defeats scoped toolbar padding", beforeFocus.toolbar);
        check(closeTo(beforeFocus.toolbar.paddingLeft, expectedInline), "responsive toolbar inline padding", beforeFocus.toolbar);
        check(closeTo(beforeFocus.shelf.paddingTop, 6), "command shelf padding defeats scoped baseline", beforeFocus.shelf);
        check(beforeFocus.shelf.radius >= 11.5, "command shelf keeps 12px radius", beforeFocus.shelf.radius);
        check(closeTo(beforeFocus.fields.gap, 12), "field grid uses 12px rhythm", beforeFocus.fields);
        check(closeTo(beforeFocus.fields.marginTop, 10), "field grid top rhythm defeats scoped baseline", beforeFocus.fields);
        check(closeTo(beforeFocus.fields.paddingLeft, expectedInline), "responsive field inline padding", beforeFocus.fields);
        check(closeTo(visualGap, 12), "physical card gap matches computed rhythm", visualGap);
        check(beforeFocus.fieldCard.radius >= 11.5, "field card keeps 12px radius", beforeFocus.fieldCard);
        check(closeTo(beforeFocus.fieldCard.borderWidth, 1), "field card owns the outer border", beforeFocus.fieldCard);
        check(beforeFocus.fieldCard.shadow !== "none", "field card has raised separation", beforeFocus.fieldCard.shadow);
        check(closeTo(beforeFocus.fieldBody.margin, 0) && closeTo(beforeFocus.fieldBody.borderWidth, 0) && closeTo(beforeFocus.fieldBody.radius, 0), "inner editor no longer competes with outer card", beforeFocus.fieldBody);
        check(closeTo(beforeFocus.richInput.paddingTop, 12) && closeTo(beforeFocus.richInput.paddingLeft, 14), "field content inset defeats scoped baseline", beforeFocus.richInput);
        check(focused.focusWithin && focused.borderColor === beforeFocus.accent && focused.shadow !== beforeFocus.fieldCard.shadow, "focus is expressed on the full field card", { focused, accent: beforeFocus.accent, restingShadow: beforeFocus.fieldCard.shadow });

        check(tagsContained, "tag rail stays inside viewport", beforeFocus.tags);
        check(beforeFocus.tags.radius >= 9.5, "tag rail uses the editorial radius", beforeFocus.tags);
        check(closeTo(beforeFocus.tags.marginLeft, expectedInline), "tag rail follows responsive inline rhythm", beforeFocus.tags);
        check(beforeFocus.tags.fontFamily.includes("Editorial Inter"), "tag rail uses Editorial Inter", beforeFocus.tags.fontFamily);
        check(
          scenario.tags === "collapsed"
            ? beforeFocus.tags.collapsedVisible && !beforeFocus.tags.expandedVisible
            : !beforeFocus.tags.collapsedVisible && beforeFocus.tags.expandedVisible,
          "requested tag state is exclusive",
          beforeFocus.tags,
        );

        check(beforeFocus.content.fontFamily.startsWith("Georgia"), "field content keeps user-owned serif", beforeFocus.content);
        check(beforeFocus.content.fontSize === "19px" && beforeFocus.content.lineHeight === "31px", "field content keeps user-owned metrics", beforeFocus.content);
        const expectedUserColor = scenario.theme === "dark" ? "rgb(226, 190, 174)" : "rgb(89, 42, 44)";
        check(beforeFocus.content.color === expectedUserColor, "field content keeps user-owned color", beforeFocus.content.color);
        check(beforeFocus.content.codeFamily.startsWith("Menlo") && beforeFocus.content.codeSize === "13px", "inline code keeps user-owned typography", beforeFocus.content);

        if (scenario.dupe) {
          const restingDangerVisible = (
            beforeFocus.duplicate.outlineWidth >= 2
            && beforeFocus.duplicate.outlineColor === beforeFocus.duplicate.danger
          ) || beforeFocus.duplicate.shadow.includes(beforeFocus.duplicate.danger);
          const focusedDangerVisible = (
            focused.editorOutlineWidth >= 2
            && focused.editorOutlineColor === beforeFocus.duplicate.danger
          ) || focused.editorShadow.includes(beforeFocus.duplicate.danger);
          check(
            beforeFocus.duplicate.active && restingDangerVisible && focusedDangerVisible,
            "duplicate field retains its danger treatment at rest and focus",
            { resting: beforeFocus.duplicate, focused },
          );
        }

        result.metrics = beforeFocus;
        result.toolbarInteraction = { resting: toolbarResting, hovered: toolbarHovered, pressed: toolbarPressed, focused: toolbarFocused };
        result.fieldBadgeFocus = fieldBadgeFocus;
        result.focus = focused;
      } catch (error) {
        check(false, "scenario completed", error.stack || error.message);
      } finally {
        await page.screenshot({
          path: path.join(captureDir, `${scenario.name}.png`),
          fullPage: false,
        });
        await page.close();
      }

      report.scenarios.push(result);
    }
  } finally {
    await browser.close();
  }

  report.ok = report.scenarios.every((scenario) => scenario.checks.every((check) => check.ok));
  fs.writeFileSync(reportPath, `${JSON.stringify(report, null, 2)}\n`);
  fs.writeFileSync(markdownPath, markdownReport(report));

  console.log(`${report.ok ? "PASS" : "FAIL"}: ${report.summary.passed}/${report.summary.total} Editor checks`);
  console.log(`Report: ${reportPath}`);
  console.log(`Screenshots: ${captureDir}`);
  if (!report.ok) {
    for (const scenario of report.scenarios) {
      for (const check of scenario.checks.filter((item) => !item.ok)) {
        console.error(`${scenario.name}: ${check.label} — ${compactDetails(check.details)}`);
      }
    }
    process.exitCode = 1;
  }
})();
