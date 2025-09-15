
import { sleep } from "../utils.js";
import { checkIfHTMLElement } from "../utils.js";


/**
 * Shows a temporary message inside a container element and hides it after a specified duration.
 *
 * @param {HTMLElement} container - The container element that holds the message (e.g., a div).
 * @param {string} message - The text content to display inside the container.
 * @param {number} [duration=MILLI_SECONDS] - Optional. The time in milliseconds before the message is hidden. Defaults to MILLI_SECONDS.
 *
 * @example
 * showTemporaryMessage(messageContainerElement, "Operation successful!", 3000);
 */
export function showTemporaryMessage(container, message, duration = 6000) {

    container.classList.add("show");

    const pElement = container.querySelector("p")
    
    if (!pElement) {
        pElement = document.createElement("p")
    }
    
    pElement.textContent = message;


    setTimeout(() => {
        container.classList.remove("show");
       
    }, duration);

     return true;
}


/**
 * Displays a queue of messages inside a container, showing each message
 * one after the other with a staggered delay for smooth animations.
 *
 * This function is asynchronous and non-blocking, meaning the rest of the
 * page remains responsive while the messages are displayed.
 *
 * @async
 * @function showEnqueuedMessages
 * @param {string[]} enqueueMessages - An array of message strings to display sequentially.
 * @param {HTMLElement} container - The container element where messages will appear.
 * @param {number} [duration=6000] - Time in milliseconds before a message is hidden.
 * @param {number} [stagger=500] - Delay in milliseconds before showing the next message, 
 *                                 allowing animations to overlap smoothly.
 * 
 * @example
 * const messages = ["First message", "Second message", "Third message"];
 * showEnqueuedMessages(messages, document.querySelector("#message-box"));
 *
 * // Messages will appear one by one in #message-box,
 * // each visible for ~6s, staggered 500ms apart.
 */
export async function showEnqueuedMessages(enqueueMessages, container, duration = 6000, stagger = 3000) {
    if (enqueueMessages.length === 0) {
        warnError("showEnqueuedMessages", "The enqueueMessages is empty")
        return;
    }

    if (!checkIfHTMLElement(container)) {
        warnError("showEnqueuedMessages", "The container is not a HTML container")
        return false;
    }

  
    while (enqueueMessages.length > 0) {
       
        const message = enqueueMessages.shift();
     
        showTemporaryMessage(container, message,  duration);
        await sleep(stagger); // small stagger for animation
           
      
    }
}



