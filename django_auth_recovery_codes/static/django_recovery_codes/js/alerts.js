// Create a reusable Swal with smaller message text
// this allows the text to not be extreme larger for 
// success confirmation message. The smaller text is
// set in the CSS
const SmallTextSwal = Swal.mixin({
    customClass: {
        htmlContainer: "smaller-text"
    }
});



export const AlertUtils = {


    /**
     * Show a SweetAlert2 alert.
     *
     * @param {Object} options - The options for the alert.
     * @param {string} options.title - The title of the alert.
     * @param {string} options.text - The text content of the alert.
     * @param {string} options.icon - The icon to display in the alert. 
     *                                Available options: 'success', 'error', 'warning', 'info', 'question'.
     * @param {string} options.confirmButtonText - The text for the confirm button.
     */
    showAlert({ title, text, icon, confirmButtonText }) {
        Swal.fire({
            title: title,
            text: text,
            icon: icon,
            confirmButtonText: confirmButtonText
        });
    },



    async showConfirmationAlert({
        showDenyButton = true,
        showCancelButton = true,
        confirmButtonText = "Remove",
        denyButtonText = "Don't remove",
        title = "Do you want to proceed with this action ?",
        text = "This action is irreversable and cannot be undone",
        icon = "info",
        cancelMessage = "No action was taken",
        messageToDisplayOnSuccess = "The action was successfully",
    } = {}) {
        return SmallTextSwal.fire({
            title,
            text,
            showDenyButton,
            showCancelButton,
            confirmButtonText,
            denyButtonText,
            icon
        }).then((result) => {
            if (result.isConfirmed) {
                SmallTextSwal.fire({
                    text: messageToDisplayOnSuccess,
                    icon: "success"
                });
                return true;
            } else if (result.isDenied) {
                SmallTextSwal.fire({
                    text: cancelMessage,
                    icon: "info"
                });
                return false;
            }
            return null;
        });
    }

};


