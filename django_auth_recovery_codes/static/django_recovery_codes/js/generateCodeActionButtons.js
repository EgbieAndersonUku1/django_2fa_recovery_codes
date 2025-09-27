/**
 * `generateCodeActionButton.js` dynamically creates four buttons:
 * "Regenerate Code", "Email Code", "Delete Code", and "Download Code". 
 * These buttons are loaded into the DOM after the user generates their recovery codes.
 * 
 * Why this is needed:
 * The application behaves like a SPA (Single Page Application). This means 
 * parts of the page can update, change, or be removed without a full page refresh.
 * 
 * How it affects this page:
 * On initial load, the "generate code" form exists in the DOM. 
 * It allows the user to generate a recovery code with an expiry date. 
 * The four buttons above are hidden by Jinja template logic (if-statements), 
 * ensuring the user can only generate codes from the designated area.
 * 
 * After generating a code, the form is removed from the DOM. 
 * The buttons are also hidden via Jinja logic and displayed on page refresh. 
 * To show the button the page would need to be refreshed right after the codes have
 * been generate. However, this would normally break SPA behaviour, 
 * since refreshing the page defeats the SPA’s purpose.
 * 
 * To solve this, `generateCodeActionButton.js` dynamically generates the buttons 
 * after the code is generated. The dynamically created buttons behave identically 
 * to the Jinja template buttons. Users can't even tell and can  interact with them normally, 
 * and when the page is refreshed, the dynamic buttons are removed, 
 * allowing the Jinja template buttons to take over seamlessly.
 * 
 * Key points:
 * - Ensures SPA behaviour is maintained.
 * - Buttons mirror Jinja template buttons in functionality and style.
 * - Provides a smooth user experience without forcing a page refresh.
 */



import { warnError } from "./logger.js";

// Factory function to create button config
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


// Define all buttons// Define all buttons
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
 * Generates a container <div> with all code action buttons.
 * 
 * @returns {HTMLDivElement} The container div element with buttons appended.
 *
 * Notes:
 * - Uses a global `buttons` object mapping identifiers to button configuration objects.
 */
export function generateCodeActionAButtons() {
  const divElement = document.createElement("div");
  divElement.id = "code-actions";
  divElement.classList.add("buttons", "flex-grid", "fourth-column-grid", "margin-top-lg")

  for (let button in buttons) {
    const btnCode       = buttons[button];
    const buttonElement = createCodeActionButton(btnCode);
    
    divElement.appendChild(buttonElement);

  }

  return divElement;
}



/**
 * Creates a single code action button with loader and text/icon.
 *
 * @param {Object} buttonObject - Configuration object for the button.
 * @returns {HTMLButtonElement} The complete button element.
 *
 * Notes:
 * - Expected `buttonObject` structure:
 *   {
 *     button: { id: string, buttonClassList: string[] },
 *     loader: { id: string, class: string },
 *     iconSpan: { id: string, fontAwesomIElement: string[], textContent: string }
 *   }
 */
export function createCodeActionButton(buttonObject) {

  const buttonElement = createButton(buttonObject)
  const loaderElement = createLoader(buttonObject);
  const spanElement   = createSpanText(buttonObject);

  buttonElement.appendChild(loaderElement);
  buttonElement.appendChild(spanElement);
  return buttonElement
}



/**
 * Creates a basic button element with the specified ID and classes.
 *
 * @param {Object} buttonObject - Configuration object containing button id and class list.
 * @returns {HTMLButtonElement} The created button element.
 *
 * Notes:
 * - Expected structure: { button: { id: string, buttonClassList: string[] } }
 */
export function createButton(buttonObject) {
  const buttonElement = document.createElement("button");
  buttonElement.id    = buttonObject.button.id;

  addClassesToElement(buttonElement, buttonObject.button.buttonClassList);
  return buttonElement

}


/**
 * Creates a loader <span> element for a button.
 *
 * @param {Object} buttonObject - Configuration object containing loader id and class.
 * @returns {HTMLSpanElement} The loader span element.
 *
 * Notes:
 * - Expected structure: { loader: { id: string, class: string } }
 */
function createLoader(buttonObject) {
  const loaderElement     = document.createElement("span");
  loaderElement.id        = buttonObject.loader.id
  loaderElement.className = buttonObject.loader.class;
  return loaderElement
}



/**
 * Creates a <span> element containing an icon and text for a button.
 *
 * @param {Object} buttonObject - Configuration object containing icon and text details.
 * @returns {HTMLSpanElement} The span element with icon and text.
 *
 * Notes:
 * - Expected structure: 
 *   { iconSpan: { id: string, fontAwesomIElement: string[], textContent: string } }
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
 * Adds multiple CSS classes to a given DOM element.
 *
 * @param {HTMLElement} element - The element to which classes will be added.
 * @param {string[]} selectorList - Array of class names to add.
 *
 * Notes:
 * - Validates that `element` is not null/undefined and that `selectorList` is an array.
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


export function updateButtonFromConfig(btn, config, btnTitleMsg) {

  btn.className = ""; // reset old classes
  btn.classList.add(...config.button.buttonClassList);

  btn.id = config.button.id;

  btn.innerHTML = `<i class="${config.iconSpan.fontAwesomeClassSelector.join(' ')}"></i> ${config.iconSpan.textContent}`;
  btn.title     = btnTitleMsg

}