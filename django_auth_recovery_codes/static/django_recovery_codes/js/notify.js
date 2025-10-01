import { showEnqueuedMessages } from "./messages/message.js";
import { checkIfHTMLElement }  from  "./utils.js";
import fetchData from "./fetch.js";
import { getCsrfToken } from "./security/csrf.js";


const notificationContainer = document.getElementById("notification");
const enqueueMessages = [];

function oneTimeElementsCheck() {
    // === Notification ===
    checkIfHTMLElement(notificationContainer, "Notification container", true);
}

oneTimeElementsCheck();




function pushNotificatonsInToQueue(notifications) {
     if (notifications) {
        notifications.forEach(msg => enqueueMessages.push(msg));
        showEnqueuedMessages(enqueueMessages, notificationContainer)
    }
}

function listenForLiveSSEMessages() {
    const es = new EventSource(`${window.location.origin}/auth/recovery-codes/sse/notifications/`);

    console.log(es)

    es.onmessage = (evt) => {
        
        if (evt.data) {
            enqueueMessages.push(evt.data);
            showEnqueuedMessages(enqueueMessages, notificationContainer);
    }
        
    };
}

/**
 * Subscribes to server-sent events (SSE) for recovery code notifications
 * and updates the notification container with new messages.
 *
 * @param {string[]} enqueueMessages - Array to store incoming messages.
 */
export async function notify_user() {

    const data = await fetchData({
        url: "/auth/recovery-codes/notifications/",
        csrfToken: getCsrfToken(),
        method: "GET",
        returnRawResponse: false,
        throwOnError: false
    })

    pushNotificatonsInToQueue(data.notifications);
   
   

}

notify_user()
listenForLiveSSEMessages();
console.log(enqueueMessages)
