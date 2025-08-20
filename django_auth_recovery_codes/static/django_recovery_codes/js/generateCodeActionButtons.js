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
function createButtonConfig({ idPrefix, color, icon, text }) {
  return {
    button: {
      buttonClassList: ["generate", "btn-medium",  "padding-sm", "title", `bg-${color}`, "text-white"],
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
const buttons = {
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



export function generateCodeActionAButtons() {
    const divElement = document.createElement("div");
    divElement.id    = "code-actions";
    divElement.classList.add("buttons",  "flex-grid",  "fourth-column-grid",  "margin-top-lg")

    for (let button in buttons) {
      const btnCode       = buttons[button];
      const buttonElement = createCodeActionButton(btnCode);
      divElement.appendChild(buttonElement);
    
    }
    
    return divElement;
}


function createCodeActionButton(buttonObject) {
  
    const buttonElement   = createButton(buttonObject)
    const loaderElement   = createLoader(buttonObject);
    const spanElement     = createSpanText(buttonObject);
  
    buttonElement.appendChild(loaderElement);
    buttonElement.appendChild(spanElement);
    return buttonElement
}


function createButton(buttonObject) {
     const buttonElement   = document.createElement("button");
     buttonElement.id      = buttonObject.button.id;
     addClassesToElement(buttonElement, buttonObject.button.buttonClassList);
     return buttonElement

}

function createLoader(buttonObject) {
   const loaderElement     = document.createElement("span");
   loaderElement.id        = buttonObject.loader.id 
   loaderElement.className = buttonObject.loader.class;
   return loaderElement
}

function createSpanText(buttonObject) {
    const spanElement        = document.createElement("span");
    const fontAwesomIElement = document.createElement("i");

    addClassesToElement(fontAwesomIElement, buttonObject.iconSpan.fontAwesomIElement);
    spanElement.id = buttonObject.iconSpan.id;

    spanElement.appendChild(fontAwesomIElement);
    spanElement.appendChild(document.createTextNode(buttonObject.iconSpan.textContent))

    return spanElement;
}


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



