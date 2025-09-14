export function markCardAsDeleted(cardElement) {

    if (cardElement === null) return;

    const statusElements = cardElement.querySelectorAll('.card-head .info-box .value p');
    if (!statusElements.length) return;


    for (const pElement of statusElements) {
        if (pElement.classList.contains('status')) {
            pElement.textContent = "Deleted";
            pElement.classList.remove("text-green");
            pElement.classList.add("text-red", "bold");
            break;
        }
    }
}
