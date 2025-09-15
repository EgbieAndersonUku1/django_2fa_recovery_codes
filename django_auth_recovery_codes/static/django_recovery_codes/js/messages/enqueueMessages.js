import { showTemporaryMessage } from "./message.js";
import { sleep } from "../utils.js";
import { warnError } from "../logger.js";
import { checkIfHTMLElement } from "../utils.js";


export default class EnqueuedMessages {

    constructor( ){
        this._enqueuedMessages = [];
    }   

    addMessage(message) {
        this._enqueuedMessages.push(message)
    }

    getEnqueuedMessages() {
        return this._enqueuedMessages;
    }

    
    /**
     * Displays a queue of messages inside a container, showing each message
     * one after the other with a staggered delay for smooth animations.
     *
     * This method is asynchronous and non-blocking, meaning the rest of the
     * page remains responsive while the messages are displayed.
     *
     * @async
     * @method showEnqueuedMessages
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
    async showEnqueuedMessages(container, duration = 6000, stagger = 3000) {
        if (this._enqueuedMessages.length === 0) {
            warnError("showEnqueuedMessages", "The enqueueMessages is empty")
            return;
        }
    
        if (!checkIfHTMLElement(container)) {
            warnError("showEnqueuedMessages", "The container is not a HTML container")
            return false;
        }
    
        while (this._enqueuedMessages.length > 0) {
           
            const message = this._enqueuedMessages.shift();
         
            showTemporaryMessage(container, message,  duration);
            await sleep(stagger); // small stagger for animation
               
        }
    }
    
    
    
    
}