const { chromium } = require("playwright");
const fs = require("node:fs");
const path = require("node:path");

const base = process.env.PREVIEW_URL || "http://127.0.0.1:4418/design-exploration/production-preview/index.html";
const captureDir = path.join(__dirname, "captures");
fs.mkdirSync(captureDir, { recursive: true });

function check(condition, message) {
  if (!condition) throw new Error(message);
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
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  const errors = [];
  const bottomHeights = new Map();
  page.on("console", message => { if (message.type() === "error") errors.push(message.text()); });
  page.on("pageerror", error => errors.push(error.message));

  async function auditButtonInteraction(url, selector, label) {
    await page.setViewportSize({ width: 1440, height: 820 });
    await page.goto(url);
    await page.waitForLoadState("networkidle");
    const button = page.locator(selector).first();
    check(await button.count() === 1, `${label}: action missing`);
    const resting = await button.evaluate(node => ({
      shadow: getComputedStyle(node).boxShadow,
      transform: getComputedStyle(node).transform,
    }));
    await button.hover();
    await page.waitForTimeout(220);
    const hovered = await button.evaluate(node => ({
      shadow: getComputedStyle(node).boxShadow,
      transform: getComputedStyle(node).transform,
    }));
    check(hovered.shadow !== resting.shadow && hovered.transform !== resting.transform, `${label}: hover feedback missing ${JSON.stringify({ resting, hovered })}`);
    const buttonBounds = await button.boundingBox();
    check(buttonBounds, `${label}: action has no pointer bounds`);
    await page.mouse.move(
      buttonBounds.x + buttonBounds.width / 2,
      buttonBounds.y + buttonBounds.height / 2,
    );
    await page.mouse.down();
    await page.waitForTimeout(180);
    const pressed = await button.evaluate(node => ({
      shadow: getComputedStyle(node).boxShadow,
      transform: getComputedStyle(node).transform,
    }));
    check(pressed.shadow !== hovered.shadow && pressed.transform !== hovered.transform, `${label}: pressed feedback missing ${JSON.stringify({ hovered, pressed })}`);
    await page.mouse.up();
    await page.mouse.move(0, 500);

    await page.evaluate(() => document.activeElement?.blur());
    let focused = false;
    for (let index = 0; index < 12; index += 1) {
      await page.keyboard.press("Tab");
      focused = await page.evaluate(target => document.activeElement?.matches(target) ?? false, selector);
      if (focused) break;
    }
    check(focused, `${label}: keyboard focus target unreachable`);
    const focusStyle = await button.evaluate(node => ({
      outline: getComputedStyle(node).outlineStyle,
      outlineWidth: getComputedStyle(node).outlineWidth,
    }));
    check(focusStyle.outline !== "none" && parseFloat(focusStyle.outlineWidth) >= 2, `${label}: focus indicator missing ${JSON.stringify(focusStyle)}`);
  }

  async function auditHeatmap(context, label) {
    await page.waitForTimeout(100);
    const expectedHeatmapView = context === "deck-browser" ? "rh-view-deckbrowser" : "rh-view-overview";
    check(await page.locator(`.rh-container.${expectedHeatmapView}`).count() === 1, `${label}: Review Heatmap view contract missing`);
    const stylesheetOrder = await page.evaluate(() => {
      const nodes = [...document.head.querySelectorAll('link[rel="stylesheet"], style')];
      return {
        theme: nodes.findIndex(node => node.getAttribute("href")?.includes("/addon/web/theme.css")),
        heatmap: nodes.findIndex(node => node.id === "review-heatmap-late-style"),
      };
    });
    check(stylesheetOrder.theme >= 0 && stylesheetOrder.heatmap > stylesheetOrder.theme, `${label}: late Review Heatmap stylesheet not reproduced ${JSON.stringify(stylesheetOrder)}`);
    const streakStats = await page.locator(".streak .sstats").evaluateAll(nodes => {
      const channels = value => {
        const parsed = (value.match(/[\d.]+/g) || []).slice(0, 3).map(Number);
        return value.startsWith("color(srgb")
          ? parsed.map(channel => channel * 255)
          : parsed;
      };
      const luminance = value => channels(value)
        .map(channel => channel / 255)
        .map(channel => channel <= .04045 ? channel / 12.92 : ((channel + .055) / 1.055) ** 2.4)
        .reduce((total, channel, index) => total + channel * [.2126, .7152, .0722][index], 0);
      return nodes.map((node, nodeIndex) => {
        const color = getComputedStyle(node).color;
        let backdrop = node;
        let background = "rgba(0, 0, 0, 0)";
        while (backdrop) {
          const candidate = getComputedStyle(backdrop).backgroundColor;
          const alpha = Number((candidate.match(/[\d.]+/g) || [0, 0, 0, 0])[3] ?? 1);
          if (alpha > 0) {
            background = candidate;
            break;
          }
          backdrop = backdrop.parentElement;
        }
        const rect = node.getBoundingClientRect();
        const foregroundLuminance = luminance(color);
        const backgroundLuminance = luminance(background);
        const contrast = (Math.max(foregroundLuminance, backgroundLuminance) + .05)
          / (Math.min(foregroundLuminance, backgroundLuminance) + .05);
        const overlaps = nodes.some((other, otherIndex) => {
          if (nodeIndex === otherIndex) return false;
          const otherRect = other.getBoundingClientRect();
          return Math.min(rect.right, otherRect.right) - Math.max(rect.left, otherRect.left) > .5
            && Math.min(rect.bottom, otherRect.bottom) - Math.max(rect.top, otherRect.top) > .5;
        });
        return {
          text: node.textContent.trim(),
          color,
          background,
          backdrop: backdrop?.tagName || null,
          contrast,
          visible: rect.width > 0 && rect.height > 0,
          overlaps,
        };
      });
    });
    check(streakStats.length === 4, `${label}: streak summary missing ${JSON.stringify(streakStats)}`);
    check(streakStats.every(item => item.visible && !item.overlaps), `${label}: streak visibility/overlap regression ${JSON.stringify(streakStats)}`);
    check(streakStats.every(item => item.contrast >= 4.5), `${label}: streak contrast regression ${JSON.stringify(streakStats)}`);
    const calendar = await page.evaluate(() => {
      const root = document.documentElement;
      const resolveSvg = (property, variable) => {
        const probe = document.createElementNS("http://www.w3.org/2000/svg", "rect");
        probe.style.setProperty(property, `var(${variable})`);
        document.body.append(probe);
        const resolved = getComputedStyle(probe).getPropertyValue(property);
        probe.remove();
        return resolved;
      };
      const expectedTokens = {
        empty: "--mist-heatmap-empty",
        "future-empty": "--mist-paper-light",
        "future-1": "--mist-heatmap-future-1",
        "future-2": "--mist-heatmap-future-2",
        "future-3": "--mist-heatmap-future-3",
        "future-4": "--mist-heatmap-future-4",
        "today-empty": "--mist-heatmap-empty",
        "history-1": "--mist-heatmap-history-1",
        "history-2": "--mist-heatmap-history-2",
        "history-3": "--mist-heatmap-history-3",
        "history-4": "--mist-heatmap-history-4",
        selected: "--mist-heatmap-history-4",
      };
      const cells = [...document.querySelectorAll(".cal-heatmap-container rect[data-heatmap-role]")]
        .map(node => {
          const role = node.dataset.heatmapRole;
          const style = getComputedStyle(node);
          return {
            role,
            fill: style.fill,
            expectedFill: resolveSvg("fill", expectedTokens[role]),
            stroke: style.stroke,
            strokeWidth: Number.parseFloat(style.strokeWidth),
          };
        });
      const current = cells.find(cell => cell.role === "today-empty");
      const selected = cells.find(cell => cell.role === "selected");
      const control = getComputedStyle(document.querySelector(".rh-container .hm-btn"));
      const labelStyle = getComputedStyle(document.querySelector(".cal-heatmap-container .graph-label"));
      return {
        cells,
        current,
        selected,
        currentStroke: resolveSvg("stroke", "--mist-ink"),
        selectedStroke: resolveSvg("stroke", "--mist-focus"),
        controlBackground: control.backgroundColor,
        oldControlBackground: control.backgroundColor === "rgb(230, 230, 230)",
        labelFill: labelStyle.fill,
        expectedLabelFill: resolveSvg("fill", "--mist-muted"),
        rootIdentity: root.dataset.mistlineEnabled,
      };
    });
    check(calendar.cells.length === 12, `${label}: real SVG Review Heatmap fixture missing ${JSON.stringify(calendar.cells)}`);
    check(calendar.cells.every(cell => cell.fill === cell.expectedFill), `${label}: selected-palette heatmap ramp mismatch ${JSON.stringify(calendar.cells)}`);
    check(new Set(calendar.cells.filter(cell => cell.role.startsWith("future-") && cell.role !== "future-empty").map(cell => cell.fill)).size === 4, `${label}: forecast hierarchy collapsed ${JSON.stringify(calendar.cells)}`);
    check(new Set(calendar.cells.filter(cell => cell.role.startsWith("history-")).map(cell => cell.fill)).size === 4, `${label}: history hierarchy collapsed ${JSON.stringify(calendar.cells)}`);
    check(calendar.current?.stroke === calendar.currentStroke && calendar.current.strokeWidth >= 1, `${label}: today outline mismatch ${JSON.stringify(calendar.current)}`);
    check(calendar.selected?.stroke === calendar.selectedStroke && calendar.selected.strokeWidth >= 2, `${label}: selected-day outline mismatch ${JSON.stringify(calendar.selected)}`);
    check(!calendar.oldControlBackground && calendar.controlBackground, `${label}: Review Heatmap controls kept third-party gray ${JSON.stringify(calendar)}`);
    check(calendar.labelFill === calendar.expectedLabelFill, `${label}: Review Heatmap label color mismatch ${JSON.stringify(calendar)}`);
    check(calendar.rootIdentity === "on", `${label}: theme ownership marker missing`);
  }

  async function auditTextContrast(selector, label) {
    const samples = await page.locator(selector).evaluateAll(nodes => {
      const pixelFor = (layers) => {
        const canvas = document.createElement("canvas");
        canvas.width = 1;
        canvas.height = 1;
        const context = canvas.getContext("2d", { willReadFrequently: true });
        context.clearRect(0, 0, 1, 1);
        for (const layer of layers) {
          context.fillStyle = layer;
          context.fillRect(0, 0, 1, 1);
        }
        return [...context.getImageData(0, 0, 1, 1).data].slice(0, 3);
      };
      const luminance = channels => channels
        .map(channel => channel / 255)
        .map(channel => channel <= .04045 ? channel / 12.92 : ((channel + .055) / 1.055) ** 2.4)
        .reduce((total, channel, index) => total + channel * [.2126, .7152, .0722][index], 0);
      return nodes.map(node => {
        const ancestors = [];
        for (let current = node; current; current = current.parentElement) ancestors.unshift(current);
        const background = pixelFor(ancestors.map(current => getComputedStyle(current).backgroundColor));
        const colorValue = getComputedStyle(node).color;
        const foreground = pixelFor([colorValue]);
        const first = luminance(foreground);
        const second = luminance(background);
        return {
          text: node.textContent.trim(),
          color: colorValue,
          background: `rgb(${background.join(", ")})`,
          contrast: (Math.max(first, second) + .05) / (Math.min(first, second) + .05),
        };
      });
    });
    check(samples.length > 0, `${label}: contrast targets missing`);
    check(samples.every(sample => sample.contrast >= 4.5), `${label}: text contrast below 4.5 ${JSON.stringify(samples)}`);
  }

  async function auditReviewerInheritanceBoundary(label) {
    const inheritance = await page.evaluate(() => {
      const root = document.documentElement;
      const selectors = ["#qa", ".user-card-inheritance-probe", ".user-card-button"];
      const read = () => Object.fromEntries(selectors.map(selector => {
        const style = getComputedStyle(document.querySelector(selector));
        return [selector, {
          colorScheme: style.getPropertyValue("color-scheme"),
          fontSynthesis: style.getPropertyValue("font-synthesis"),
          fontKerning: style.getPropertyValue("font-kerning"),
        }];
      }));
      const context = root.getAttribute("data-mistline-context");
      const active = read();
      root.removeAttribute("data-mistline-context");
      const unmanaged = read();
      root.setAttribute("data-mistline-context", context);
      const restored = read();
      return { active, unmanaged, restored };
    });
    check(
      Object.values(inheritance.unmanaged).every(sample => Object.values(sample).every(Boolean)),
      `${label}: computed inheritance audit returned an empty property ${JSON.stringify(inheritance)}`,
    );
    check(
      JSON.stringify(inheritance.active) === JSON.stringify(inheritance.unmanaged),
      `${label}: inherited card rendering preferences were restyled ${JSON.stringify(inheritance)}`,
    );
    check(
      JSON.stringify(inheritance.restored) === JSON.stringify(inheritance.active),
      `${label}: reviewer inheritance audit did not restore its context ${JSON.stringify(inheritance)}`,
    );
  }

  const views = [
    ["top-toolbar", "deck", "top-toolbar.png"],
    ["deck-browser", "deck", "deck-browser.png"],
    ["overview", "deck", "overview.png"],
    ["reviewer", "question", "reviewer-question.png"],
    ["reviewer", "answer", "reviewer-answer.png"],
    ["standard-bottom-bar", "deck", "standard-bottom-bar.png"],
    ["reviewer-bottom-bar", "question", "bottom-question.png"],
    ["reviewer-bottom-bar", "answer", "bottom-answer.png"],
  ];

  for (const [context, state, filename] of views) {
    await page.goto(`${base}?context=${context}&state=${state}`);
    await page.waitForLoadState("networkidle");
    await page.evaluate(() => window.scrollTo(0, 0));
    check(await page.locator("html").getAttribute("data-mistline-context") === context, `${filename}: context marker mismatch`);
    await page.evaluate(() => document.fonts.ready);
    check(await page.evaluate(() => document.fonts.check('400 16px "Mist Inter"')), `${filename}: Mist Inter failed to load`);
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
    check(overflow <= 0, `${filename}: horizontal overflow ${overflow}px`);
    if (context === "deck-browser") {
      check(await page.locator(".mistline-deck-heading").count() === 1, "deck heading missing");
      check(await page.locator("tr.deck").count() === 8, "deck rows missing");
      const radius = await page.locator("tr.current td").first().evaluate(node => getComputedStyle(node).borderRadius);
      check(radius === "0px", `selected row unexpectedly rounded: ${radius}`);
      const heading = await page.locator(".mistline-deck-heading h1").evaluate(node => {
        const style = getComputedStyle(node);
        return { fontFamily: style.fontFamily, fontSize: style.fontSize };
      });
      check(heading.fontFamily.includes("Mist Source Serif"), `deck heading serif mismatch: ${heading.fontFamily}`);
      check(Math.abs(parseFloat(heading.fontSize) - 43.2) < 0.1, `deck heading size mismatch: ${heading.fontSize}`);
      const parentDeck = await page.locator("tr.deck:has(a.collapse) a.deck").first().evaluate(node => {
        const style = getComputedStyle(node);
        return { fontFamily: style.fontFamily, fontSize: style.fontSize, fontWeight: style.fontWeight };
      });
      check(parentDeck.fontFamily.includes("Mist Inter"), `deck row sans mismatch: ${parentDeck.fontFamily}`);
      check(parentDeck.fontSize === "16px" && parentDeck.fontWeight === "600", `deck parent metrics mismatch: ${parentDeck.fontSize}/${parentDeck.fontWeight}`);
      const leafDeck = await page.locator("tr.deck:not(:has(a.collapse)) a.deck").first().evaluate(node => {
        const style = getComputedStyle(node);
        return { fontSize: style.fontSize, fontWeight: style.fontWeight };
      });
      check(leafDeck.fontSize === "15.5px" && leafDeck.fontWeight === "400", `deck leaf metrics mismatch: ${leafDeck.fontSize}/${leafDeck.fontWeight}`);
      await auditTextContrast("tr.deck .new-count, tr.deck .learn-count, tr.deck .review-count", "deck semantic counts");
    }
    if (context === "top-toolbar") {
      const navItems = page.locator(".toolbar > .hitem");
      check(await navItems.count() === 5, "toolbar action count mismatch");
      const nav = await page.locator("#decks").evaluate(node => {
        const style = getComputedStyle(node);
        return { fontFamily: style.fontFamily, fontSize: style.fontSize, fontWeight: style.fontWeight };
      });
      check(nav.fontFamily.includes("Mist Inter"), `toolbar font mismatch: ${nav.fontFamily}`);
      check(nav.fontSize === "15px" && nav.fontWeight === "400", `toolbar metrics mismatch: ${nav.fontSize}/${nav.fontWeight}`);
      const headerHeight = await page.locator(".header").evaluate(node => node.getBoundingClientRect().height);
      check(headerHeight >= 60, `toolbar breathing height too small: ${headerHeight}px`);
      const buttonSystem = await navItems.evaluateAll(nodes => nodes.map(node => {
        const style = getComputedStyle(node);
        const rect = node.getBoundingClientRect();
        return {
          left: rect.left,
          right: rect.right,
          width: rect.width,
          height: rect.height,
          clientWidth: node.clientWidth,
          scrollWidth: node.scrollWidth,
          radius: parseFloat(style.borderRadius),
          shadow: style.boxShadow,
          tabIndex: node.tabIndex,
        };
      }));
      check(buttonSystem.every(item => item.width >= 44 && item.height >= 44), `toolbar target size mismatch: ${JSON.stringify(buttonSystem)}`);
      check(buttonSystem.every(item => item.clientWidth >= 42 && item.scrollWidth <= item.clientWidth), `toolbar label clipping: ${JSON.stringify(buttonSystem)}`);
      check(buttonSystem.every(item => item.tabIndex === -1), `toolbar ownership/tab order mismatch: ${JSON.stringify(buttonSystem)}`);
      check(buttonSystem.every(item => item.radius >= 8), `toolbar radius mismatch: ${JSON.stringify(buttonSystem)}`);
      check(buttonSystem.every(item => item.shadow !== "none"), "toolbar button shadow missing");
      const gaps = buttonSystem.slice(1).map((item, index) => item.left - buttonSystem[index].right);
      check(gaps.every(gap => gap >= 8), `toolbar gap too small: ${JSON.stringify(gaps)}`);
      const idleSpinner = await page.locator("#sync-spinner").evaluate(node => {
        const style = getComputedStyle(node);
        return { width: node.getBoundingClientRect().width, visibility: style.visibility };
      });
      check(idleSpinner.width === 0 && idleSpinner.visibility === "hidden", `sync idle state mismatch: ${JSON.stringify(idleSpinner)}`);
      for (const [index, id] of ["decks", "add", "browse", "stats", "sync"].entries()) {
        const action = page.locator(`#${id}`);
        const resting = buttonSystem[index];
        await action.hover();
        await page.waitForTimeout(220);
        const hovered = await action.evaluate(node => ({ shadow: getComputedStyle(node).boxShadow, transform: getComputedStyle(node).transform }));
        check(hovered.shadow !== resting.shadow && hovered.transform !== "none", `${id}: toolbar hover feedback missing ${JSON.stringify(hovered)}`);
        const actionBounds = await action.boundingBox();
        check(actionBounds, `${id}: toolbar action has no pointer bounds`);
        await page.mouse.move(
          actionBounds.x + actionBounds.width / 2,
          actionBounds.y + actionBounds.height / 2,
        );
        await page.mouse.down();
        await page.waitForTimeout(180);
        const pressed = await action.evaluate(node => ({ shadow: getComputedStyle(node).boxShadow, transform: getComputedStyle(node).transform }));
        check(pressed.shadow !== hovered.shadow && pressed.transform !== hovered.transform, `${id}: toolbar pressed feedback missing ${JSON.stringify(pressed)}`);
        await page.mouse.up();
        await page.mouse.move(0, 500);
        await page.waitForTimeout(220);
      }
    }
    if (context === "reviewer") {
      await auditReviewerInheritanceBoundary(filename);
      const background = await page.locator("#qa").evaluate(node => getComputedStyle(node).backgroundColor);
      check(background === "rgba(0, 0, 0, 0)", `#qa became an opaque card: ${background}`);
      const inherited = await page.locator(".user-card-inheritance-probe").evaluate(node => {
        const style = getComputedStyle(node);
        return {
          color: style.color,
          fontFamily: style.fontFamily,
          lineHeight: style.lineHeight,
        };
      });
      check(
        inherited.color === "rgb(41, 73, 105)"
          && inherited.fontFamily.includes("Arial")
          && inherited.lineHeight === "46px",
        `reviewer user-owned inherited typography was restyled: ${JSON.stringify(inherited)}`,
      );
    }
    if (context === "overview") {
      const study = page.locator("#study");
      const style = await study.evaluate(node => {
        const computed = getComputedStyle(node);
        return { radius: parseFloat(computed.borderRadius), shadow: computed.boxShadow };
      });
      check(style.radius >= 8, `study button radius too small: ${style.radius}px`);
      check(style.shadow !== "none", "study button shadow missing");
      const studyText = await study.evaluate(node => {
        const style = getComputedStyle(node);
        return { fontFamily: style.fontFamily, fontSize: style.fontSize };
      });
      check(studyText.fontFamily.includes("Mist Inter") && studyText.fontSize === "16px", `study typography mismatch: ${studyText.fontFamily}/${studyText.fontSize}`);
      const overviewLayout = await page.evaluate(() => {
        const body = document.body.getBoundingClientRect();
        const table = document.querySelector('center > table[width="400"]').getBoundingClientRect();
        return { body: { left: body.left, right: body.right }, table: { left: table.left, right: table.right, width: table.width } };
      });
      check(overviewLayout.table.left >= overviewLayout.body.left && overviewLayout.table.right <= overviewLayout.body.right, `overview table escapes body: ${JSON.stringify(overviewLayout)}`);
      check(overviewLayout.table.width <= 640.5, `overview table exceeds max width: ${overviewLayout.table.width}px`);
      await auditTextContrast(".new-count, .learn-count, .review-count", "overview semantic counts");
    }
    if (context === "overview" || context === "deck-browser") await auditHeatmap(context, context);
    if (context === "reviewer-bottom-bar" && state === "answer") {
      check(await page.locator("button[data-ease]").count() === 4, "rating tray incomplete");
      check(await page.locator("button[data-ease] .nobold").count() === 4, "rating intervals missing");
      const ratingStyles = await page.locator("button[data-ease]").evaluateAll(nodes => nodes.map(node => {
        const computed = getComputedStyle(node);
        return { radius: parseFloat(computed.borderRadius), shadow: computed.boxShadow };
      }));
      check(ratingStyles.every(style => style.radius >= 8), `rating button radius too small: ${JSON.stringify(ratingStyles)}`);
      check(ratingStyles.every(style => style.shadow !== "none"), "rating button shadow missing");
      const ratingText = await page.locator("button[data-ease]").first().evaluate(node => {
        const style = getComputedStyle(node);
        return { fontFamily: style.fontFamily, fontSize: style.fontSize };
      });
      check(ratingText.fontFamily.includes("Mist Inter") && ratingText.fontSize === "14px", `rating typography mismatch: ${ratingText.fontFamily}/${ratingText.fontSize}`);
      for (const ease of [1, 2, 3, 4]) {
        await page.locator(`button[data-ease="${ease}"]`).hover();
        await page.waitForTimeout(180);
        await auditTextContrast(`button[data-ease="${ease}"]`, `rating ${ease}/light hover`);
      }
      await page.mouse.move(0, 500);
    }
    if (context === "reviewer") {
      const userButton = await page.locator(".user-card-button").evaluate(node => {
        const style = getComputedStyle(node);
        return {
          radius: style.borderRadius,
          border: style.borderTopStyle,
          shadow: style.boxShadow,
          fontFamily: style.fontFamily,
          fontWeight: style.fontWeight,
          animationDuration: style.animationDuration,
          transitionDuration: style.transitionDuration,
        };
      });
      check(
        userButton.radius === "19px"
          && userButton.border === "dotted"
          && userButton.shadow !== "none"
          && userButton.fontFamily.includes("Georgia")
          && userButton.fontWeight === "400"
          && userButton.animationDuration === "3s"
          && userButton.transitionDuration === "2s",
        `reviewer user-owned button was restyled: ${JSON.stringify(userButton)}`,
      );
    }
    if (context === "reviewer-bottom-bar") {
      const spacing = await page.evaluate(() => {
        const outer = document.querySelector("#outer").getBoundingClientRect();
        const buttons = [...document.querySelectorAll("#middle button")].map(node => node.getBoundingClientRect());
        const intervals = [...document.querySelectorAll("#middle .nobold, #middle .stattxt")].map(node => node.getBoundingClientRect());
        const style = getComputedStyle(document.querySelector("#outer"));
        return {
          outer: { top: outer.top, right: outer.right, bottom: outer.bottom, left: outer.left, height: outer.height },
          buttons: buttons.map(rect => ({ top: rect.top, right: rect.right, bottom: rect.bottom, left: rect.left, width: rect.width, height: rect.height })),
          intervals: intervals.map(rect => ({ top: rect.top, bottom: rect.bottom })),
          paddingTop: parseFloat(style.paddingTop),
          paddingBottom: parseFloat(style.paddingBottom),
        };
      });
      bottomHeights.set(state, spacing.outer.height);
      check(spacing.paddingTop >= 8 && spacing.paddingBottom >= 16, `${filename}: outer padding mismatch ${spacing.paddingTop}/${spacing.paddingBottom}`);
      check(spacing.outer.bottom - Math.max(...spacing.buttons.map(button => button.bottom)) >= 16, `${filename}: bottom controls touch outer edge`);
      check(Math.min(...spacing.intervals.map(interval => interval.top)) - spacing.outer.top >= 8, `${filename}: interval labels touch top rule`);
      check(spacing.buttons.every(button => button.left >= spacing.outer.left && button.right <= spacing.outer.right), `${filename}: controls escape outer bounds`);
      const actionSurfaces = await page.locator("#outer button").evaluateAll(nodes => nodes.map(node => {
        const style = getComputedStyle(node);
        const rect = node.getBoundingClientRect();
        return { height: rect.height, radius: parseFloat(style.borderRadius), shadow: style.boxShadow };
      }));
      check(actionSurfaces.every(item => item.height >= 44 && item.radius >= 8 && item.shadow !== "none"), `${filename}: incomplete action surface ${JSON.stringify(actionSurfaces)}`);
      if (state === "answer") {
        const gaps = spacing.buttons.slice(1).map((button, index) => button.left - spacing.buttons[index].right);
        check(gaps.every(gap => gap >= 8), `${filename}: rating gap too small ${JSON.stringify(gaps)}`);
      }
    }
    if (context === "standard-bottom-bar") {
      const standard = await page.evaluate(() => {
        const outer = document.querySelector("#outer").getBoundingClientRect();
        const headerStyle = getComputedStyle(document.querySelector("#header"));
        const buttons = [...document.querySelectorAll("button")].map(node => node.getBoundingClientRect());
        return {
          outer: { left: outer.left, right: outer.right, top: outer.top, bottom: outer.bottom },
          paddingTop: parseFloat(headerStyle.paddingTop),
          paddingBottom: parseFloat(headerStyle.paddingBottom),
          buttons: buttons.map(rect => ({ left: rect.left, right: rect.right, top: rect.top, bottom: rect.bottom })),
        };
      });
      check(standard.paddingTop === 9 && standard.paddingBottom === 9, `standard bottom padding changed: ${standard.paddingTop}/${standard.paddingBottom}`);
      check(standard.buttons.every(button => button.left >= standard.outer.left && button.right <= standard.outer.right), "standard bottom controls escape outer bounds");
      const headerBoxSizing = await page.locator("#header").evaluate(node => getComputedStyle(node).boxSizing);
      check(headerBoxSizing === "border-box", `standard bottom header box sizing mismatch: ${headerBoxSizing}`);
      const surfaces = await page.locator("#outer button").evaluateAll(nodes => nodes.map(node => {
        const style = getComputedStyle(node);
        const rect = node.getBoundingClientRect();
        return { height: rect.height, radius: parseFloat(style.borderRadius), shadow: style.boxShadow };
      }));
      check(surfaces.every(item => item.height >= 44 && item.radius >= 8 && item.shadow !== "none"), `standard bottom action surface mismatch: ${JSON.stringify(surfaces)}`);
      await page.keyboard.press("Tab");
      const focused = await page.evaluate(() => ({ tag: document.activeElement?.tagName, outline: getComputedStyle(document.activeElement).outlineStyle }));
      check(focused.tag === "BUTTON" && focused.outline !== "none", `Anki outline reset defeated focus indicator: ${JSON.stringify(focused)}`);
      await page.evaluate(() => document.activeElement?.blur());
    }
    await page.screenshot({ path: path.join(captureDir, filename), fullPage: true });
  }

  check(Math.abs(bottomHeights.get("question") - bottomHeights.get("answer")) <= 0.5, `reviewer bottom height jumps ${bottomHeights.get("question")} -> ${bottomHeights.get("answer")}`);

  for (const width of [720, 660, 584, 583, 480, 360, 320]) {
    await page.setViewportSize({ width, height: 820 });
    const compactViews = [
      ["top-toolbar", "deck"],
      ["deck-browser", "deck"],
      ["overview", "deck"],
      ["reviewer", "answer"],
      ["standard-bottom-bar", "deck"],
      ["reviewer-bottom-bar", "question"],
      ["reviewer-bottom-bar", "answer"],
    ];
    const compactBottomHeights = new Map();
    for (const [context, state] of compactViews) {
      const extra = context === "top-toolbar" ? "&sync=1" : "";
      await page.goto(`${base}?context=${context}&state=${state}${extra}`);
      await page.waitForLoadState("networkidle");
      const compactOverflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
      check(compactOverflow <= 0, `${context}/${state}@${width}: horizontal overflow ${compactOverflow}px`);
      if (context === "deck-browser" || context === "overview") {
        const inlinePadding = await page.locator("body").evaluate(node => parseFloat(getComputedStyle(node).paddingLeft));
        check(inlinePadding >= 14, `${context}@${width}: body padding too small ${inlinePadding}px`);
        await auditHeatmap(context, `${context}@${width}`);
      }
      if (context === "deck-browser") {
        const deckBounds = await page.evaluate(() => {
          const table = document.querySelector("center > table").getBoundingClientRect();
          const viewport = document.documentElement.clientWidth;
          const decktd = getComputedStyle(document.querySelector(".decktd"));
          return { left: table.left, right: table.right, viewport, minWidth: decktd.minWidth };
        });
        check(deckBounds.left >= 0 && deckBounds.right <= deckBounds.viewport, `deck table escapes viewport @${width}: ${JSON.stringify(deckBounds)}`);
        if (width <= 480) check(deckBounds.minWidth === "0px", `deck name column min-width survives @${width}: ${deckBounds.minWidth}`);
      }
      if (context === "overview") {
        const overviewBounds = await page.evaluate(() => {
          const table = document.querySelector('center > table[width="400"]').getBoundingClientRect();
          const study = document.querySelector("#study").getBoundingClientRect();
          return { table: { left: table.left, right: table.right }, study: { left: study.left, right: study.right }, viewport: document.documentElement.clientWidth };
        });
        check(overviewBounds.table.left >= 0 && overviewBounds.table.right <= overviewBounds.viewport, `overview table escapes viewport @${width}: ${JSON.stringify(overviewBounds)}`);
        check(overviewBounds.study.left >= overviewBounds.table.left && overviewBounds.study.right <= overviewBounds.table.right, `study control escapes overview table @${width}: ${JSON.stringify(overviewBounds)}`);
      }
      if (context === "reviewer") {
        const reviewPadding = await page.evaluate(() => ({
          body: parseFloat(getComputedStyle(document.body).paddingLeft),
          qa: parseFloat(getComputedStyle(document.querySelector("#qa")).paddingLeft),
        }));
        check(reviewPadding.body >= 12 && reviewPadding.qa >= 12, `reviewer@${width}: compact padding mismatch ${JSON.stringify(reviewPadding)}`);
      }
      if (context === "top-toolbar") {
        const toolbarBounds = await page.evaluate(() => {
          const header = document.querySelector(".header").getBoundingClientRect();
          const controls = [...document.querySelectorAll(".toolbar > .hitem")].map(node => {
            const rect = node.getBoundingClientRect();
            const style = getComputedStyle(node);
            return {
              left: rect.left,
              right: rect.right,
              width: rect.width,
              height: rect.height,
              clientWidth: node.clientWidth,
              scrollWidth: node.scrollWidth,
              tabIndex: node.tabIndex,
              radius: parseFloat(style.borderRadius),
              shadow: style.boxShadow,
            };
          });
          const spinner = document.querySelector("#sync-spinner").getBoundingClientRect();
          return { header: { left: header.left, right: header.right }, controls, spinnerWidth: spinner.width };
        });
        check(toolbarBounds.controls.length === 5, `toolbar control count @${width}`);
        check(toolbarBounds.spinnerWidth > 0, `sync spinner fixture inactive @${width}`);
        check(toolbarBounds.controls.every(item => item.left >= toolbarBounds.header.left && item.right <= toolbarBounds.header.right && item.width >= 44 && item.height >= 44), `toolbar bounds @${width}: ${JSON.stringify(toolbarBounds)}`);
        check(toolbarBounds.controls.every(item => item.tabIndex === -1), `toolbar tab order @${width}: ${JSON.stringify(toolbarBounds)}`);
        check(toolbarBounds.controls.every(item => item.scrollWidth <= item.clientWidth), `toolbar label clipping @${width}: ${JSON.stringify(toolbarBounds)}`);
        check(toolbarBounds.controls.every(item => item.radius >= 8 && item.shadow !== "none"), `toolbar surfaces @${width}: ${JSON.stringify(toolbarBounds)}`);
        const compactGaps = toolbarBounds.controls.slice(1).map((item, index) => item.left - toolbarBounds.controls[index].right);
        const minimumGap = width <= 360 ? 1.5 : 3;
        check(compactGaps.every(gap => gap >= minimumGap), `toolbar gap @${width}: ${JSON.stringify(compactGaps)}`);
        if (width === 320) {
          await page.locator(".header").screenshot({ path: path.join(captureDir, "top-toolbar-compact.png") });
        }
      }
      if (context === "reviewer-bottom-bar") {
        const compactSpacing = await page.evaluate(() => {
          const outer = document.querySelector("#outer").getBoundingClientRect();
          const buttonNodes = [...document.querySelectorAll("#middle button")];
          const buttons = buttonNodes.map(node => node.getBoundingClientRect());
          const allButtons = [...document.querySelectorAll("#outer button")].map(node => node.getBoundingClientRect());
          const stat = document.querySelector(".stat");
          return {
            outer: { left: outer.left, right: outer.right, bottom: outer.bottom, height: outer.height },
            buttons: buttons.map(rect => ({ left: rect.left, right: rect.right, bottom: rect.bottom, width: rect.width })),
            allButtons: allButtons.map(rect => ({ left: rect.left, right: rect.right, bottom: rect.bottom })),
            statVisible: stat ? getComputedStyle(stat).display !== "none" : false,
            boxSizing: buttonNodes.map(node => getComputedStyle(node).boxSizing),
          };
        });
        compactBottomHeights.set(state, compactSpacing.outer.height);
        check(compactSpacing.outer.bottom - Math.max(...compactSpacing.buttons.map(button => button.bottom)) >= 16, `${state}@${width}: missing bottom clearance`);
        const minimumButtonWidth = width <= 360 ? 64 : 96;
        check(compactSpacing.buttons.every(button => button.width >= minimumButtonWidth && button.left >= compactSpacing.outer.left + 8 && button.right <= compactSpacing.outer.right - 8), `${state}@${width}: compact control bounds ${JSON.stringify(compactSpacing)}`);
        check(compactSpacing.allButtons.every(button => button.left >= compactSpacing.outer.left && button.right <= compactSpacing.outer.right), `${state}@${width}: side action escapes ${JSON.stringify(compactSpacing)}`);
        check(compactSpacing.statVisible === (width > 583), `${state}@${width}: side status visibility mismatch`);
        check(compactSpacing.boxSizing.every(value => value === "border-box"), `${state}@${width}: content-box action survives ${JSON.stringify(compactSpacing.boxSizing)}`);
      }
    }
    check(Math.abs(compactBottomHeights.get("question") - compactBottomHeights.get("answer")) <= 0.5, `bottom height jumps at ${width}px: ${compactBottomHeights.get("question")} -> ${compactBottomHeights.get("answer")}`);
    if (width === 480) {
      await page.goto(`${base}?context=reviewer-bottom-bar&state=answer`);
      await page.waitForLoadState("networkidle");
      await page.screenshot({ path: path.join(captureDir, "bottom-answer-compact.png"), fullPage: true });
    }
    if (width === 360) {
      for (const [context, filename] of [["deck-browser", "deck-browser-compact.png"], ["overview", "overview-compact.png"]]) {
        await page.goto(`${base}?context=${context}&state=deck`);
        await page.waitForLoadState("networkidle");
        await page.screenshot({ path: path.join(captureDir, filename), fullPage: true });
      }
    }
  }

  await page.setViewportSize({ width: 1440, height: 1000 });
  for (const context of ["deck-browser", "overview"]) {
    await page.goto(`${base}?context=${context}&state=deck&theme=dark`);
    await page.waitForLoadState("networkidle");
    check(await page.locator("html").evaluate(node => node.classList.contains("night-mode")), `${context}/dark: dark mode marker missing`);
    const darkBackground = await page.locator("body").evaluate(node => getComputedStyle(node).backgroundColor);
    check(darkBackground === "rgb(27, 25, 22)", `${context}/dark: paper background mismatch ${darkBackground}`);
    await auditHeatmap(context, `${context}/dark`);
    await auditTextContrast(
      context === "deck-browser"
        ? "tr.deck .new-count, tr.deck .learn-count, tr.deck .review-count"
        : ".new-count, .learn-count, .review-count",
      `${context}/dark semantic counts`,
    );
  }
  await page.goto(`${base}?context=reviewer-bottom-bar&state=answer&ratings=4&theme=dark`);
  await page.waitForLoadState("networkidle");
  await auditTextContrast("button[data-ease]", "reviewer ratings/dark");
  for (const ease of [1, 2, 3, 4]) {
    await page.locator(`button[data-ease="${ease}"]`).hover();
    await page.waitForTimeout(180);
    await auditTextContrast(`button[data-ease="${ease}"]`, `rating ${ease}/dark hover`);
  }

  await page.goto(`${base}?context=reviewer&state=question&motion=off`);
  await page.waitForLoadState("networkidle");
  const userMotion = await page.locator(".user-card-button").evaluate(node => {
    const style = getComputedStyle(node);
    return { animationDuration: style.animationDuration, transitionDuration: style.transitionDuration };
  });
  check(
    userMotion.animationDuration === "3s" && userMotion.transitionDuration === "2s",
    `reviewer user-owned motion was suppressed: ${JSON.stringify(userMotion)}`,
  );

  await page.setViewportSize({ width: 320, height: 820 });
  await page.goto(`${base}?context=top-toolbar&state=deck&sync=1&labels=long`);
  await page.waitForLoadState("networkidle");
  const localizedToolbar = await page.evaluate(() => {
    const viewport = document.documentElement.clientWidth;
    const controls = [...document.querySelectorAll(".toolbar > .hitem")].map(node => {
      const rect = node.getBoundingClientRect();
      const style = getComputedStyle(node);
      return {
        left: rect.left,
        right: rect.right,
        width: rect.width,
        overflow: style.overflow,
        textOverflow: style.textOverflow,
        title: node.title,
        ariaLabel: node.getAttribute("aria-label"),
      };
    });
    return { viewport, scrollWidth: document.documentElement.scrollWidth, controls };
  });
  check(localizedToolbar.scrollWidth <= localizedToolbar.viewport, `localized toolbar overflow: ${JSON.stringify(localizedToolbar)}`);
  check(localizedToolbar.controls.every(item => item.width >= 44 && item.left >= 0 && item.right <= localizedToolbar.viewport), `localized toolbar bounds: ${JSON.stringify(localizedToolbar)}`);
  check(localizedToolbar.controls.every(item => item.overflow === "hidden" && item.textOverflow === "ellipsis" && item.title === item.ariaLabel), `localized toolbar fallback/accessibility mismatch: ${JSON.stringify(localizedToolbar)}`);

  const auditWidths = [1440, 720, 660, 584, 583, 480, 360, 320];
  const standardVariants = { deck: 3, overview: 4, dynamic: 4 };
  for (const width of auditWidths) {
    await page.setViewportSize({ width, height: 820 });
    for (const [variant, expectedCount] of Object.entries(standardVariants)) {
      await page.goto(`${base}?context=standard-bottom-bar&variant=${variant}`);
      await page.waitForLoadState("networkidle");
      const standardAudit = await page.evaluate(() => {
        const viewport = document.documentElement.clientWidth;
        const outer = document.querySelector("#outer").getBoundingClientRect();
        const actions = [...document.querySelectorAll("#outer button")].map(node => {
          const rect = node.getBoundingClientRect();
          const style = getComputedStyle(node);
          return { left: rect.left, right: rect.right, height: rect.height, radius: parseFloat(style.borderRadius), shadow: style.boxShadow };
        });
        return { viewport, scrollWidth: document.documentElement.scrollWidth, outer: { left: outer.left, right: outer.right }, actions };
      });
      check(standardAudit.actions.length === expectedCount, `${variant}@${width}: standard action count mismatch`);
      check(standardAudit.scrollWidth <= standardAudit.viewport, `${variant}@${width}: standard toolbar overflow ${standardAudit.scrollWidth}/${standardAudit.viewport}`);
      check(standardAudit.actions.every(item => item.left >= standardAudit.outer.left && item.right <= standardAudit.outer.right && item.height >= 44 && item.radius >= 8 && item.shadow !== "none"), `${variant}@${width}: standard action mismatch ${JSON.stringify(standardAudit)}`);
    }
  }

  const ratingSemantics = {
    2: { 1: "--mist-due", 2: "--mist-good" },
    3: { 1: "--mist-due", 2: "--mist-good", 3: "--mist-easy" },
    4: { 1: "--mist-due", 2: "--mist-learn", 3: "--mist-good", 4: "--mist-easy" },
  };
  for (const width of auditWidths) {
    await page.setViewportSize({ width, height: 820 });
    for (const [ratingCount, expectedColors] of Object.entries(ratingSemantics)) {
      await page.goto(`${base}?context=reviewer-bottom-bar&state=answer&ratings=${ratingCount}`);
      await page.waitForLoadState("networkidle");
      const ratingAudit = await page.evaluate(expected => {
        const viewport = document.documentElement.clientWidth;
        const rootStyle = getComputedStyle(document.documentElement);
        const resolveColor = variable => {
          const probe = document.createElement("span");
          probe.style.color = `var(${variable})`;
          document.body.append(probe);
          const color = getComputedStyle(probe).color;
          probe.remove();
          return color;
        };
        const actions = [...document.querySelectorAll("button[data-ease]")].map(node => {
          const style = getComputedStyle(node);
          const rect = node.getBoundingClientRect();
          const ease = node.dataset.ease;
          return {
            ease,
            color: style.color,
            expected: resolveColor(expected[ease]),
            left: rect.left,
            right: rect.right,
            height: rect.height,
            radius: parseFloat(style.borderRadius),
            shadow: style.boxShadow,
          };
        });
        const stat = document.querySelector(".stat");
        const defaultAction = document.querySelector("#defease");
        return {
          viewport,
          scrollWidth: document.documentElement.scrollWidth,
          statVisible: getComputedStyle(stat).display !== "none",
          tokenProbe: rootStyle.getPropertyValue("--mist-good"),
          defaultOutline: defaultAction ? {
            style: getComputedStyle(defaultAction).outlineStyle,
            width: getComputedStyle(defaultAction).outlineWidth,
            offset: getComputedStyle(defaultAction).outlineOffset,
          } : null,
          actions,
        };
      }, expectedColors);
      check(ratingAudit.actions.length === Number(ratingCount), `${ratingCount} ratings@${width}: count mismatch`);
      check(ratingAudit.scrollWidth <= ratingAudit.viewport, `${ratingCount} ratings@${width}: overflow ${ratingAudit.scrollWidth}/${ratingAudit.viewport}`);
      check(ratingAudit.statVisible === (width > 583), `${ratingCount} ratings@${width}: Edit/More visibility mismatch`);
      check(ratingAudit.actions.every(item => item.color === item.expected), `${ratingCount} ratings@${width}: semantic color mismatch ${JSON.stringify(ratingAudit.actions)}`);
      await auditTextContrast("button[data-ease]", `${ratingCount} ratings@${width}`);
      check(ratingAudit.actions.every(item => item.left >= 8 && item.right <= ratingAudit.viewport - 8 && item.height >= 52 && item.radius >= 8 && item.shadow !== "none"), `${ratingCount} ratings@${width}: action surface mismatch ${JSON.stringify(ratingAudit.actions)}`);
      if (Number(ratingCount) >= 3) {
        check(ratingAudit.defaultOutline?.style !== "none" && parseFloat(ratingAudit.defaultOutline?.width) >= 2, `${ratingCount} ratings@${width}: default action ring defeated by Anki reset ${JSON.stringify(ratingAudit.defaultOutline)}`);
      }
    }
  }

  const interactionCases = [
    [`${base}?context=overview&state=deck`, "#study", "Study Now"],
    [`${base}?context=standard-bottom-bar&variant=overview`, "#outer button[data-action=opts]", "standard bottom action"],
    [`${base}?context=reviewer-bottom-bar&state=question`, "#ansbut", "Show Answer"],
    [`${base}?context=reviewer-bottom-bar&state=answer&ratings=4`, ".stat:first-child button", "Edit"],
    [`${base}?context=reviewer-bottom-bar&state=answer&ratings=4`, "button[data-ease='1']", "Again rating"],
    [`${base}?context=reviewer-bottom-bar&state=answer&ratings=4`, ".stat:last-child button", "More"],
  ];
  for (const [url, selector, label] of interactionCases) {
    await auditButtonInteraction(url, selector, label);
  }

  check(errors.length === 0, errors.join("\n"));
  console.log("PASS: production CSS fixture — 8 views, 8 responsive widths, all top/standard/reviewer actions, long labels, sync idle/active, 2/3/4 rating semantics, focus, interaction, spacing, overflow, ownership, and console");
  await browser.close();
})().catch(error => {
  console.error(error.stack || error);
  process.exit(1);
});
