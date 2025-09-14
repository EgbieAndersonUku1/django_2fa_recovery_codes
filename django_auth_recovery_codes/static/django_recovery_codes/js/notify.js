import { showEnqueuedMessages } from "./messages/message.js";


const notificationContainer = document.getElementById("notification");

export function notify_user(enqueueMessages) {
   const es = new EventSource("/auth/recovery-codes/sse/notifications/");

es.onmessage = (evt) => {
    
    if (evt.data) {
        enqueueMessages.push(evt.data);
        showEnqueuedMessages(enqueueMessages, notificationContainer);
}
    
};

}
