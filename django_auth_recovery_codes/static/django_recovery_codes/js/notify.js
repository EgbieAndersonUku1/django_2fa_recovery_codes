import { showEnqueuedMessages } from "./messages/message.js";
import { checkIfHTMLElement }  from  "./utils.js";

const notificationContainer = document.getElementById("notification");


function oneTimeElementsCheck() {
    // === Notification ===
    checkIfHTMLElement(notificationContainer, "Notification container", true);
}

oneTimeElementsCheck();



/**
 * Subscribes to server-sent events (SSE) for recovery code notifications
 * and updates the notification container with new messages.
 *
 * @param {string[]} enqueueMessages - Array to store incoming messages.
 */
export function notify_user(enqueueMessages) {
   const es = new EventSource("/auth/recovery-codes/sse/notifications/");

es.onmessage = (evt) => {
    
    if (evt.data) {
        enqueueMessages.push(evt.data);
        showEnqueuedMessages(enqueueMessages, notificationContainer);
}
    
};

}
