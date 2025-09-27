/**
 * @summary Performs a one-time validation of static DOM elements via `oneTimeElementCheck`.
 *
 * @note This ensures required elements exist before the app starts and avoids repeated
 *       `if (element)` checks. Dynamic elements are excluded since they may not exist
 *       at initial load and must be checked at runtime.
 *
 * === One-Time DOM Element Check ===
 *
 * 1. Purpose
 *    - Ensure all required elements are valid before the app starts.
 *    - Reduce repeated `if (element)` checks in functions.
 *
 * --- Example without `oneTimeElementCheck` ---
 * const form = document.getElementById("form")
 * function someCallingFunction() {
 *     if (form) {
 *         // do something
 *     }
 * }
 *
 * --- Example with `oneTimeElementCheck` ---
 * function someCallingFunction() {
 *     form.appendChild(...)
 * }
 *
 * 2. Dynamic Elements
 *    - Elements not included in `oneTimeElementCheck` are excluded deliberately,
 *      because they are rendered only under certain conditions.
 *
 *    Example:
 *    const emailButtonElement = document.getElementById("email")
 *
 *    This button may be hidden by a Jinja `if` statement and only rendered
 *    when a condition is met (e.g. after generating a code). Until then,
 *    it does not exist in the DOM, so `emailButtonElement` will be `null`.
 *
 * 3. SPA Considerations
 *    - In an SPA, parts of the page update without a full refresh.
 *    - Dynamic elements must therefore be checked when they are used,
 *      not during the initial load.
 *
 * 4. Error Handling
 *    - Attempting to validate dynamic elements in `oneTimeElementCheck`
 *      would cause errors, as they do not exist until after the user action
 *      (and possible refresh) that renders them.
 */


import { warnError } from "../logger.js";



/**
 * Factory function to create a configuration object for a button with its loader and icon.
 *
 * @param {Object} options - Configuration options for the button.
 * @param {string} options.idPrefix - Prefix for the button and related element IDs.
 * @param {string} options.color - Color name to apply as a background class (e.g., 'blue').
 * @param {string} options.icon - Font Awesome icon class name (without the 'fa-' prefix).
 * @param {string} options.text - Text content for the icon span element.
 *
 * @returns {Object} A configuration object containing:
 *   - button: { buttonClassList: string[], id: string }
 *   - loader: { id: string, class: string }
 *   - iconSpan: { fontAwesomeClassSelector: string[], id: string, textContent: string }
 */
export function createButtonConfig({ idPrefix, color, icon, text }) {
  return {
    button: {
      buttonClassList: ["generate", "btn-medium", "padding-sm", "title", `bg-${color}`, "text-white"],
      id: `${idPrefix}-btn`,
    },
    loader: { id: `${idPrefix}-loader`, class: "loader" },
    iconSpan: {
      fontAwesomeClassSelector: ["fa-solid", icon],
      id: `${idPrefix}-span-text`,
      textContent: text,
    },
  };
}




/**
 * Defines all button configurations used in the test verification interface.
 *
 * Each button configuration is created using `createButtonConfig` and includes:
 *   - A button element with classes and a unique ID.
 *   - A loader element with a unique ID and CSS class.
 *   - An icon span element with Font Awesome classes, ID, and text content.
 */
export const buttons = {
  regenerateCode: createButtonConfig({
    idPrefix: "regenerate-code",
    color: "green",
    icon: "fa-code",
    text: "Regenerate code",
  }),
  emailCode: createButtonConfig({
    idPrefix: "email-code",
    color: "green",
    icon: "fa-envelope",
    text: "Email code",
  }),
  deleteAllCode: createButtonConfig({
    idPrefix: "delete-all-code",
    color: "red",
    icon: "fa-trash",
    text: "Delete code",
  }),
  downloadCode: createButtonConfig({
    idPrefix: "download-code",
    color: "blue",
    icon: "fa-download",
    text: "Download code",
  }),
};




/**
 * Generates a container div with all action buttons for code management. *
 * @returns {HTMLDivElement} The container `div` element containing all action buttons.
 */
export function generateCodeActionAButtons() {
  const divElement = document.createElement("div");
  divElement.id = "code-actions";
  divElement.classList.add("buttons", "flex-grid", "fourth-column-grid", "margin-top-lg")

  for (let button in buttons) {
    const btnCode = buttons[button];
    const buttonElement = createCodeActionButton(btnCode);
    divElement.appendChild(buttonElement);

  }

  return divElement;
}



/**
 * Creates a complete action button element with its loader and text span.
 *
 * This function:
 *   1. Creates a button element using `createButton`.
 *   2. Creates a loader element using `createLoader`.
 *   3. Creates a text span element using `createSpanText`.
 *   4. Appends the loader and text span to the button element.
 *
 * @param {Object} buttonObject - The configuration object for the button (from `createButtonConfig`).
 * @returns {HTMLButtonElement} The fully constructed button element ready to be added to the DOM.
 */
export function createCodeActionButton(buttonObject) {

  const buttonElement = createButton(buttonObject)
  const loaderElement = createLoader(buttonObject);
  const spanElement = createSpanText(buttonObject);

  buttonElement.appendChild(loaderElement);
  buttonElement.appendChild(spanElement);
  return buttonElement
}




/**
 * Creates a button element with specified properties.
 *
 * @param {Object} options - Options for the button.
 * @param {string} options.id - The ID of the button.
 * @param {string[]} [options.classes] - Array of CSS classes to add.
 * @param {string} [options.text] - Text content of the button.
 * @param {Function} [options.onClick] - Click event handler.
 * @returns {HTMLButtonElement} The created button element.
 */
export function createButton(buttonObject) {
  const buttonElement = document.createElement("button");
  buttonElement.id = buttonObject.button.id;
  addClassesToElement(buttonElement, buttonObject.button.buttonClassList);
  return buttonElement

}





/**
 * Creates a loader element (span) with specified properties.
 *
 * @param {Object} options - Options for the loader.
 * @param {string} options.id - The ID of the loader.
 * @param {string} [options.className] - CSS class(es) for the loader.
 * @param {string} [options.text] - Optional text content for the loader.
 * @returns {HTMLSpanElement} The created loader element.
 */
function createLoader(buttonObject) {
  const loaderElement = document.createElement("span");
  loaderElement.id = buttonObject.loader.id
  loaderElement.className = buttonObject.loader.class;
  return loaderElement
}




/**
 * Creates a span element with an icon and text.
 *
 * @param {Object} options - Options for the span element.
 * @param {string} options.id - The ID of the span.
 * @param {string[]} options.iconClasses - Array of classes for the <i> icon element.
 * @param {string} options.text - Text content for the span.
 * @returns {HTMLSpanElement} The created span element.
 */
export function createSpanText(buttonObject) {
  const spanElement = document.createElement("span");
  const fontAwesomIElement = document.createElement("i");

  addClassesToElement(fontAwesomIElement, buttonObject.iconSpan.fontAwesomIElement);
  spanElement.id = buttonObject.iconSpan.id;

  spanElement.appendChild(fontAwesomIElement);
  spanElement.appendChild(document.createTextNode(buttonObject.iconSpan.textContent))

  return spanElement;
}



/**
 * Adds an array of classes to a DOM element.
 *
 * @param {HTMLElement} element - The element to which classes will be added.
 * @param {string[]} selectorList - Array of class names to add.
 */
function addClassesToElement(element, selectorList) {
  if (!element) {
    warnError("addClassesToElement: The element provided is null or undefined.");
    return;
  }

  if (!Array.isArray(selectorList) || selectorList === undefined) {
    warnError(`addClassesToElement: The selectorList provided is not an array, got ${typeof selectorList}`);
    return;
  }

  console.log("Adding selector elements to element");
  selectorList.forEach((classSelector) => {
    element.classList.add(classSelector);
  });
}



/**
 * Predefined button states with configuration for id, color, icon, and text.
 */
export const buttonStates = {
  emailed: createButtonConfig({
    idPrefix: "email-code",
    color: "blue",
    icon: "fa-ban",
    text: "Emailed",
  }),

  downloaded: createButtonConfig({
    idPrefix: "download-code",
    color: "orange",
    icon: "fa-ban",
    text: "Downloaded",
  }),

  failed: createButtonConfig({
    idPrefix: "failed-code",
    color: "red",
    icon: "fa-times",
    text: "Failed",
  }),
};



/**
 * Updates a button element using a config object.
 *
 * @param {HTMLButtonElement} btn - The button element to update.
 * @param {Object} config - Configuration object for the button.
 * @param {string} btnTitleMsg - Tooltip/title text for the button.
 */
export function updateButtonFromConfig(btn, config, btnTitleMsg) {

  btn.className = ""; // reset old classes
  btn.classList.add(...config.button.buttonClassList);

  btn.id = config.button.id;

  btn.innerHTML = `<i class="${config.iconSpan.fontAwesomeClassSelector.join(' ')}"></i> ${config.iconSpan.textContent}`;
  btn.title     = btnTitleMsg

}


